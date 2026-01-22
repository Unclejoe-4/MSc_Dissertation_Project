import paho.mqtt.client as mqtt
import requests
import json
import time
from dotenv import load_dotenv
import os

# --- CONFIGURATION ---
API_URL = "http://192.168.0.61:5000/predict"
MQTT_BROKER = "192.168.254.129"
MQTT_PORT = 1883
MQTT_USER = "mqtt_user"
MQTT_PASS = "Dissertation@1"
MQTT_TOPIC_DETECTION = "home/traffic/ddos_alert"
MQTT_TOPICS = [
    "home/sensor/temperature",
    "home/sensor/humidity",
    "home/sensor/gas"
]

load_dotenv()  # loads the .env file
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# --- STATE ---
latest = {"temperature": None, "humidity": None, "gas": None}
packet_counter = 0
last_time = None

# --- HELPER FUNCTIONS ---
def fetch_ha_sensors():
    """Optional: Fetch current HA sensor states."""
    try:
        response = requests.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=3)
        response.raise_for_status()
        sensors = response.json()
        for sensor in sensors:
            entity_id = sensor["entity_id"]
            state = sensor["state"]
            # Map Home Assistant entities to latest dictionary if names match
            if "temperature" in entity_id:
                latest["temperature"] = float(state)
            elif "humidity" in entity_id:
                latest["humidity"] = float(state)
            elif "gas" in entity_id:
                latest["gas"] = float(state)
    except Exception as e:
        print(f"Failed to fetch HA sensors: {e}")

# --- MQTT CALLBACK ---
def on_message(client, userdata, msg):
    global packet_counter, last_time
    topic = msg.topic
    value = float(msg.payload.decode())

    if "temperature" in topic:
        latest["temperature"] = value
    elif "humidity" in topic:
        latest["humidity"] = value
    elif "gas" in topic:
        latest["gas"] = value

    # Only run detection if all sensors have a value
    if all(v is not None for v in latest.values()):
        now = time.time()
        inter_arrival = round(now - last_time, 6) if last_time else 0.0
        last_time = now
        packet_counter += 1

        # Prepare features for your model
        features = {
            "no": packet_counter,
            "time": now,
            "temperature": latest["temperature"],
            "humidity": latest["humidity"],
            "length": latest["gas"],
            "protocol": "MQTT"
        }

        # Call API
        try:
            resp = requests.post(API_URL, json=features, timeout=3)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            print(f"API error: {e}")
            result = {"prediction": "Unknown", "score": None}

        # Print result
        print(f"Packet {packet_counter}: Temp={latest['temperature']} "
              f"Humidity={latest['humidity']} Gas={latest['gas']} => "
              f"Detection: {result.get('prediction')} Score: {result.get('score')}")

        # Publish to MQTT
        label_raw = result.get("prediction")
        label = "DDOS" if isinstance(label_raw, str) and "ddos" in label_raw.lower() else "NORMAL"
        out = {
            "label": label,
            "score": result.get("score"),
            "model_raw": result.get("raw_prediction"),
            "meta": {
                "packet_no": packet_counter,
                "temperature": latest["temperature"],
                "humidity": latest["humidity"],
                "packet_length": latest["gas"],
                "inter_arrival": inter_arrival
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        retain = True if label == "DDOS" else False
        client.publish(MQTT_TOPIC_DETECTION, json.dumps(out), retain=retain)

# --- MQTT SETUP ---
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
for t in MQTT_TOPICS:
    mqtt_client.subscribe(t)

print("Listening for sensor data and sending live detection results...")
try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("Stopped.")
    mqtt_client.disconnect()
