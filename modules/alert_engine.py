from datetime import datetime
import random
from modules.database import execute_query


THRESHOLDS = {
    "temperature": {"medium": 30, "high": 38, "critical": 45},
    "humidity": {"medium": 35, "high": 20, "critical": 10},
    "smoke_ppm": {"medium": 100, "high": 250, "critical": 500},
    "wind_speed": {"medium": 20, "high": 30, "critical": 40},
}

ALERT_MESSAGES = {
    "CRÍTICO": [
        "⚠️ ALERTA ROJA: Condiciones extremas detectadas. Riesgo inminente de incendio.",
        "🔥 PELIGRO MÁXIMO: Activar protocolo de emergencia inmediatamente.",
        "🚨 NIVEL CRÍTICO: Notificar a bomberos y autoridades locales.",
    ],
    "ALTO": [
        "🟠 ALERTA NARANJA: Condiciones de alto riesgo. Aumentar vigilancia.",
        "⚡ RIESGO ELEVADO: Preparar brigadas forestales.",
        "📡 MONITOREO INTENSIVO: Variables ambientales en umbral peligroso.",
    ],
    "MEDIO": [
        "🟡 ALERTA AMARILLA: Condiciones moderadas de riesgo.",
        "📊 PRECAUCIÓN: Temperatura y sequedad en niveles de atención.",
    ],
    "BAJO": [
        "🟢 CONDICIONES NORMALES: Sin riesgo significativo detectado.",
    ],
}


class AlertEngine:
    def evaluate(self, sensor_readings):
        alerts = []
        for reading in sensor_readings:
            level = reading["risk_level"]
            messages = ALERT_MESSAGES.get(level, ["Estado desconocido"])
            message = random.choice(messages)
            action = self._get_action(level)
            color = self._get_color(level)

            alert = {
                "sensor_id": reading["sensor_id"],
                "zone": reading["name"],
                "level": level,
                "message": message,
                "temperature": reading["temperature"],
                "humidity": reading["humidity"],
                "smoke_ppm": reading["smoke_ppm"],
                "wind_speed": reading["wind_speed"],
                "timestamp": reading["timestamp"],
                "recommended_action": action,
                "color": color,
            }

            self._save_alert(alert)
            alerts.append(alert)

        alerts.sort(key=lambda x: ["BAJO", "MEDIO", "ALTO", "CRÍTICO"].index(x["level"]), reverse=True)
        return alerts

    def _save_alert(self, alert):
        try:
            execute_query(
                """
                INSERT INTO alerts
                    (sensor_id, zone, level, message, temperature, humidity, smoke_ppm, wind_speed, recommended_action, color)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    alert["sensor_id"],
                    alert["zone"],
                    alert["level"],
                    alert["message"],
                    alert["temperature"],
                    alert["humidity"],
                    alert["smoke_ppm"],
                    alert["wind_speed"],
                    alert["recommended_action"],
                    alert["color"],
                )
            )
        except Exception:
            pass

    def get_alert_history(self, limit=50):
        try:
            return execute_query(
                "SELECT * FROM alerts ORDER BY created_at DESC LIMIT %s",
                (limit,),
                fetch=True
            )
        except Exception:
            return []

    def get_alerts_by_level(self, level):
        try:
            return execute_query(
                "SELECT * FROM alerts WHERE level = %s ORDER BY created_at DESC LIMIT 20",
                (level,),
                fetch=True
            )
        except Exception:
            return []

    def _get_action(self, level):
        actions = {
            "CRÍTICO": "Activar protocolo de emergencia. Contactar bomberos: 119",
            "ALTO": "Desplegar brigada forestal preventiva al sector.",
            "MEDIO": "Incrementar frecuencia de monitoreo y patrullaje.",
            "BAJO": "Continuar monitoreo rutinario.",
        }
        return actions.get(level, "Verificar estado del sensor.")

    def _get_color(self, level):
        colors = {
            "CRÍTICO": "#FF2D2D",
            "ALTO": "#FF7A00",
            "MEDIO": "#FFD600",
            "BAJO": "#00C853",
        }
        return colors.get(level, "#888888")
