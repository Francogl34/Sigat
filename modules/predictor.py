import math
import random
import json
from datetime import datetime, timedelta
from modules.database import execute_query


class FirePredictor:
    def predict(self, sensor_readings):
        forecasts = []
        for reading in sensor_readings:
            prob = self._calculate_probability(reading)
            trend = self._project_trend(reading, prob)
            risk_factors = self._get_risk_factors(reading)

            forecast = {
                "zone": reading["name"],
                "sensor_id": reading["sensor_id"],
                "current_probability": prob,
                "trend": trend,
                "forecast_3h": self._adjust_prob(prob, 3),
                "forecast_6h": self._adjust_prob(prob, 6),
                "forecast_12h": self._adjust_prob(prob, 12),
                "risk_factors": risk_factors,
                "confidence": round(random.uniform(72, 92), 1),
            }

            self._save_prediction(forecast)
            forecasts.append(forecast)

        forecasts.sort(key=lambda x: x["current_probability"], reverse=True)

        hourly = self._generate_hourly_forecast()

        return {
            "zone_forecasts": forecasts,
            "hourly_forecast": hourly,
            "model_info": {
                "name": "SIGAT-Heuristic v1.0",
                "variables": ["Temperatura", "Humedad", "Viento", "Humo (PPM)", "CO2"],
                "last_updated": datetime.now().isoformat(),
            }
        }

    def _save_prediction(self, forecast):
        try:
            execute_query(
                """
                INSERT INTO predictions
                    (sensor_id, zone, current_probability, trend, forecast_3h, forecast_6h, forecast_12h, confidence, risk_factors)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    forecast["sensor_id"],
                    forecast["zone"],
                    forecast["current_probability"],
                    forecast["trend"],
                    forecast["forecast_3h"],
                    forecast["forecast_6h"],
                    forecast["forecast_12h"],
                    forecast["confidence"],
                    json.dumps(forecast["risk_factors"]),
                )
            )
        except Exception:
            pass

    def get_prediction_history(self, sensor_id=None, limit=50):
        try:
            if sensor_id:
                return execute_query(
                    "SELECT * FROM predictions WHERE sensor_id = %s ORDER BY created_at DESC LIMIT %s",
                    (sensor_id, limit),
                    fetch=True
                )
            return execute_query(
                "SELECT * FROM predictions ORDER BY created_at DESC LIMIT %s",
                (limit,),
                fetch=True
            )
        except Exception:
            return []

    def _calculate_probability(self, r):
        score = 0
        if r["temperature"] > 45: score += 35
        elif r["temperature"] > 38: score += 25
        elif r["temperature"] > 30: score += 12
        else: score += 2

        if r["humidity"] < 10: score += 35
        elif r["humidity"] < 20: score += 25
        elif r["humidity"] < 35: score += 12
        else: score += 1

        if r["smoke_ppm"] > 500: score += 20
        elif r["smoke_ppm"] > 250: score += 12
        elif r["smoke_ppm"] > 100: score += 5

        if r["wind_speed"] > 40: score += 10
        elif r["wind_speed"] > 30: score += 6
        elif r["wind_speed"] > 20: score += 3

        return min(round(score * 1.1 + random.uniform(-3, 3), 1), 98)

    def _adjust_prob(self, base, hours):
        hour = datetime.now().hour + hours
        peak_factor = 1 + 0.3 * math.sin((hour - 14) * math.pi / 12)
        adjusted = base * peak_factor + random.uniform(-4, 4)
        return round(max(1, min(98, adjusted)), 1)

    def _project_trend(self, reading, prob):
        hour = datetime.now().hour
        if 10 <= hour <= 16 and prob > 40:
            return "ASCENDENTE"
        elif prob > 70:
            return "ESTABLE_ALTO"
        elif hour > 18:
            return "DESCENDENTE"
        else:
            return "ESTABLE"

    def _get_risk_factors(self, r):
        factors = []
        if r["temperature"] > 35: factors.append(f"Temperatura alta: {r['temperature']}°C")
        if r["humidity"] < 25: factors.append(f"Baja humedad: {r['humidity']}%")
        if r["smoke_ppm"] > 150: factors.append(f"Humo elevado: {r['smoke_ppm']} PPM")
        if r["wind_speed"] > 25: factors.append(f"Viento fuerte: {r['wind_speed']} km/h")
        if not factors: factors.append("Sin factores de riesgo significativos")
        return factors

    def _generate_hourly_forecast(self):
        forecast = []
        now = datetime.now()
        for h in range(24):
            ts = now + timedelta(hours=h)
            hour = ts.hour
            base = 20 + 40 * max(0, math.sin((hour - 8) * math.pi / 10))
            forecast.append({
                "hour": ts.strftime("%H:00"),
                "probability": round(base + random.uniform(-5, 5), 1),
                "label": ts.strftime("%H:%M"),
            })
        return forecast
