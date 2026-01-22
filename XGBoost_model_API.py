from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    # Dummy prediction for testing
    return jsonify({"prediction": "NORMAL", "score": 0.9, "raw_prediction": data})

if __name__ == "__main__":
    # Listen on all network interfaces so other machines can reach it
    app.run(host="0.0.0.0", port=5000, debug=True)
