import random
import time
import math
from datetime import datetime, timedelta
from modules.database import execute_query, execute_one


class SensorSimulator:
    def __init__(self):
        self.sensors = [
            {"id": "SEN-001", "name": "Sector Tunari Norte", "lat": -17.340, "lng": -66.215},
            {"id": "SEN-002", "name": "Sector Tunari Centro", "lat": -17.355, "lng": -66.240},
            {"id": "SEN-003", "name": "Sector Tunari Sur", "lat": -17.370, "lng": -66.225},
            {"id": "SEN-004", "name": "Quebrada Saytu Kocha", "lat": -17.345, "lng": -66.260},
            {"id": "SEN-005", "name": "Bosque Sacaba", "lat": -17.385, "lng": -66.050},
            {"id": "SEN-006", "name": "Parque Alalay", "lat": -17.395, "lng": -66.140},
        ]
        self._generate_history()

    def _simulate_reading(self, sensor, danger_mode=False):
        t = time.time()
        base_temp = 28 + 8 * math.sin(t / 3600)
        base_hum = 45 - 15 * math.sin(t / 3600)

        if danger_mode:
            temp = round(base_temp + random.uniform(15, 30), 1)
            humidity = round(max(5, base_hum - random.uniform(20, 35)), 1)
            smoke = round(random.uniform(400, 900), 1)
            wind = round(random.uniform(20, 45), 1)
            co2 = round(random.uniform(800, 2000), 1)
        else:
            temp = round(base_temp + random.uniform(-2, 4), 1)
            humidity = round(max(10, base_hum + random.uniform(-5, 5)), 1)
            smoke = round(random.uniform(10, 80), 1)
            wind = round(random.uniform(5, 20), 1)
            co2 = round(random.uniform(350, 450), 1)

        risk = self._calc_risk(temp, humidity, smoke, wind)

        reading = {
            "sensor_id": sensor["id"],
            "name": sensor["name"],
            "lat": sensor["lat"],
            "lng": sensor["lng"],
            "temperature": temp,
            "humidity": humidity,
            "smoke_ppm": smoke,
            "wind_speed": wind,
            "co2_ppm": co2,
            "risk_level": risk,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
        }

        self._save_reading(reading)
        return reading

    def _save_reading(self, reading):
        try:
            execute_query(
                """
                INSERT INTO sensor_readings
                    (sensor_id, temperature, humidity, smoke_ppm, wind_speed, co2_ppm, risk_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    reading["sensor_id"],
                    reading["temperature"],
                    reading["humidity"],
                    reading["smoke_ppm"],
                    reading["wind_speed"],
                    reading["co2_ppm"],
                    reading["risk_level"],
                )
            )
        except Exception:
            pass

    def _calc_risk(self, temp, humidity, smoke, wind):
        score = 0
        if temp > 35: score += 30
        elif temp > 28: score += 15
        if humidity < 20: score += 30
        elif humidity < 35: score += 15
        if smoke > 200: score += 25
        elif smoke > 100: score += 10
        if wind > 30: score += 15
        elif wind > 20: score += 8

        if score >= 70: return "CRÍTICO"
        elif score >= 45: return "ALTO"
        elif score >= 25: return "MEDIO"
        else: return "BAJO"

    def get_readings(self):
        readings = []
        for i, sensor in enumerate(self.sensors):
            danger = (i == 1 or i == 3)
            readings.append(self._simulate_reading(sensor, danger_mode=danger))
        return readings

    def get_readings_from_db(self, sensor_id=None, limit=100):
        if sensor_id:
            return execute_query(
                """
                SELECT sr.*, s.name, s.lat, s.lng
                FROM sensor_readings sr
                JOIN sensors s ON sr.sensor_id = s.id
                WHERE sr.sensor_id = %s
                ORDER BY sr.recorded_at DESC LIMIT %s
                """,
                (sensor_id, limit),
                fetch=True
            )
        return execute_query(
            """
            SELECT sr.*, s.name, s.lat, s.lng
            FROM sensor_readings sr
            JOIN sensors s ON sr.sensor_id = s.id
            ORDER BY sr.recorded_at DESC LIMIT %s
            """,
            (limit,),
            fetch=True
        )

    def _generate_history(self):
        try:
            existing = execute_query(
                "SELECT COUNT(*) as total FROM hourly_history",
                fetch=True
            )
            if existing and existing[0]["total"] > 0:
                return
        except Exception:
            return

        now = datetime.now()
        for h in range(24):
            ts = now - timedelta(hours=23 - h)
            try:
                execute_query(
                    """
                    INSERT INTO hourly_history (hour, avg_temp, avg_humidity, avg_smoke, incidents)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        ts.strftime("%H:00"),
                        round(22 + 12 * math.sin((h - 6) * math.pi / 12) + random.uniform(-1, 1), 1),
                        round(60 - 20 * math.sin((h - 6) * math.pi / 12) + random.uniform(-2, 2), 1),
                        round(30 + 20 * max(0, math.sin((h - 10) * math.pi / 8)) + random.uniform(0, 10), 1),
                        random.randint(0, 2) if 10 <= h <= 16 else 0,
                    )
                )
            except Exception:
                pass

    def get_history(self):
        try:
            rows = execute_query(
                "SELECT hour, avg_temp, avg_humidity, avg_smoke, incidents FROM hourly_history ORDER BY recorded_at ASC LIMIT 24",
                fetch=True
            )
            if rows:
                return rows
        except Exception:
            pass

        now = datetime.now()
        history = []
        for h in range(24):
            ts = now - timedelta(hours=23 - h)
            history.append({
                "hour": ts.strftime("%H:00"),
                "avg_temp": round(22 + 12 * math.sin((h - 6) * math.pi / 12) + random.uniform(-1, 1), 1),
                "avg_humidity": round(60 - 20 * math.sin((h - 6) * math.pi / 12) + random.uniform(-2, 2), 1),
                "avg_smoke": round(30 + 20 * max(0, math.sin((h - 10) * math.pi / 8)) + random.uniform(0, 10), 1),
                "incidents": random.randint(0, 2) if 10 <= h <= 16 else 0,
            })
        return history

    def get_stats(self):
        readings = self.get_readings()
        temps = [r["temperature"] for r in readings]
        hums = [r["humidity"] for r in readings]
        smokes = [r["smoke_ppm"] for r in readings]
        critical = sum(1 for r in readings if r["risk_level"] == "CRÍTICO")
        high = sum(1 for r in readings if r["risk_level"] == "ALTO")

        try:
            db_alerts = execute_query(
                "SELECT COUNT(*) as total FROM alerts WHERE created_at::date = CURRENT_DATE",
                fetch=True
            )
            alerts_today = db_alerts[0]["total"] if db_alerts else random.randint(3, 12)
        except Exception:
            alerts_today = random.randint(3, 12)

        return {
            "avg_temp": round(sum(temps) / len(temps), 1),
            "avg_humidity": round(sum(hums) / len(hums), 1),
            "avg_smoke": round(sum(smokes) / len(smokes), 1),
            "critical_zones": critical,
            "high_risk_zones": high,
            "active_sensors": len(readings),
            "total_alerts_today": alerts_today,
        }
