from flask import Flask, render_template, jsonify
from modules.database import init_db
from modules.sensor_simulator import SensorSimulator
from modules.alert_engine import AlertEngine
from modules.predictor import FirePredictor
from modules.zones import ZoneManager

app = Flask(__name__)

try:
    init_db()
except Exception as e:
    print(f"[SIGAT] DB init error: {e}")

sensor_sim = SensorSimulator()
alert_engine = AlertEngine()
predictor = FirePredictor()
zone_manager = ZoneManager()


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/sensors")
def api_sensors():
    data = sensor_sim.get_readings()
    return jsonify(data)


@app.route("/api/alerts")
def api_alerts():
    readings = sensor_sim.get_readings()
    alerts = alert_engine.evaluate(readings)
    return jsonify(alerts)


@app.route("/api/alerts/history")
def api_alerts_history():
    history = alert_engine.get_alert_history(limit=50)
    return jsonify(history)


@app.route("/api/prediction")
def api_prediction():
    readings = sensor_sim.get_readings()
    prediction = predictor.predict(readings)
    return jsonify(prediction)


@app.route("/api/zones")
def api_zones():
    zones = zone_manager.get_zones()
    return jsonify(zones)


@app.route("/api/history")
def api_history():
    history = sensor_sim.get_history()
    return jsonify(history)


@app.route("/api/stats")
def api_stats():
    stats = sensor_sim.get_stats()
    return jsonify(stats)


@app.route("/api/sensors/db")
def api_sensors_db():
    data = sensor_sim.get_readings_from_db(limit=200)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
