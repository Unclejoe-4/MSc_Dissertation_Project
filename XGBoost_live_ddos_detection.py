import paho.mqtt.client as mqtt
import requests
import json
import time
from dotenv import load_dotenv
import os

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:5000/predict"
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

load_dotenv()
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# --- STATE ---
latest = {
    "temperature": None,
    "humidity": None,
    "gas": None
}

packet_counter = 0
last_time = None

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

    # Run prediction only when all values exist
    if not all(v is not None for v in latest.values()):
        return

    now = time.time()
    inter_arrival = round(now - last_time, 6) if last_time else 0.0
    last_time = now
    packet_counter += 1

    # --- XGBOOST FEATURE VECTOR ---
    features = {
        "packet_no": packet_counter,
        "temperature": latest["temperature"],
        "humidity": latest["humidity"],
        "packet_length": latest["gas"],
        "inter_arrival": inter_arrival
    }

    # --- API CALL ---
    try:
        response = requests.post(API_URL, json=features, timeout=3)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        print(f"API error: {e}")
        return

    # --- MODEL OUTPUT ---
    prediction = result.get("prediction")        # 0 or 1
    probability = result.get("probability")      # float

    label = "DDOS" if prediction == 1 else "NORMAL"

    print(
        f"Packet {packet_counter} | "
        f"Temp={latest['temperature']} "
        f"Humidity={latest['humidity']} "
        f"Length={latest['gas']} | "
        f"Prediction={label} "
        f"Prob={probability}"
    )

    # --- MQTT PUBLISH ---
    payload = {
        "label": label,
        "probability": probability,
        "features": features,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    retain = True if label == "DDOS" else False
    client.publish(MQTT_TOPIC_DETECTION, json.dumps(payload), retain=retain)

# --- MQTT SETUP ---
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.on_message = on_message

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

for topic in MQTT_TOPICS:
    mqtt_client.subscribe(topic)

print("Listening for sensor data and sending XGBoost DDoS predictions...")

try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    mqtt_client.disconnect()
    print("Stopped.")
