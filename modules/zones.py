import random
from modules.database import execute_query


class ZoneManager:
    def get_zones(self):
        try:
            rows = execute_query("SELECT * FROM zones", fetch=True)
            if rows:
                risk_levels = ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]
                weights = [0.15, 0.25, 0.35, 0.25]
                zones = []
                for zone in rows:
                    z = dict(zone)
                    z["sensors"] = [f"SEN-{str(int(zone['id'].replace('Z',''))).zfill(3)}"]
                    z["current_risk"] = random.choices(risk_levels, weights=weights)[0]
                    z["humidity"] = round(random.uniform(15, 65), 1)
                    z["temperature"] = round(random.uniform(22, 52), 1)
                    z["fire_index"] = round(random.uniform(1, 10), 2)
                    if z.get("last_incident"):
                        z["last_incident"] = str(z["last_incident"])
                    zones.append(z)
                return zones
        except Exception:
            pass

        return self._fallback_zones()

    def get_zone_by_id(self, zone_id):
        try:
            return execute_query(
                "SELECT * FROM zones WHERE id = %s",
                (zone_id,),
                fetch=True
            )
        except Exception:
            return None

    def _fallback_zones(self):
        zones_data = [
            {"id": "Z001", "name": "Parque Nacional Tunari Norte", "area_ha": 4850, "vegetation": "Bosque montano", "altitude_m": 2800, "sensors": ["SEN-001"], "lat": -17.340, "lng": -66.215, "priority": "Alta", "last_incident": "2024-08-15", "population_nearby": 12500},
            {"id": "Z002", "name": "Parque Nacional Tunari Centro", "area_ha": 6200, "vegetation": "Queñuales y matorrales", "altitude_m": 3200, "sensors": ["SEN-002"], "lat": -17.355, "lng": -66.240, "priority": "Crítica", "last_incident": "2025-09-03", "population_nearby": 8200},
            {"id": "Z003", "name": "Parque Nacional Tunari Sur", "area_ha": 3900, "vegetation": "Pino y eucalipto", "altitude_m": 2600, "sensors": ["SEN-003"], "lat": -17.370, "lng": -66.225, "priority": "Media", "last_incident": "2024-07-22", "population_nearby": 22000},
            {"id": "Z004", "name": "Quebrada Saytu Kocha", "area_ha": 1200, "vegetation": "Vegetación riparia", "altitude_m": 2500, "sensors": ["SEN-004"], "lat": -17.345, "lng": -66.260, "priority": "Alta", "last_incident": "2025-10-11", "population_nearby": 4500},
            {"id": "Z005", "name": "Bosque Sacaba", "area_ha": 890, "vegetation": "Arbustos y pastizales", "altitude_m": 2600, "sensors": ["SEN-005"], "lat": -17.385, "lng": -66.050, "priority": "Media", "last_incident": "2023-09-05", "population_nearby": 35000},
            {"id": "Z006", "name": "Área Verde Alalay", "area_ha": 320, "vegetation": "Vegetación urbana", "altitude_m": 2500, "sensors": ["SEN-006"], "lat": -17.395, "lng": -66.140, "priority": "Baja", "last_incident": "2022-08-19", "population_nearby": 85000},
        ]
        risk_levels = ["CRÍTICO", "ALTO", "MEDIO", "BAJO"]
        weights = [0.15, 0.25, 0.35, 0.25]
        zones = []
        for zone in zones_data:
            z = dict(zone)
            z["current_risk"] = random.choices(risk_levels, weights=weights)[0]
            z["humidity"] = round(random.uniform(15, 65), 1)
            z["temperature"] = round(random.uniform(22, 52), 1)
            z["fire_index"] = round(random.uniform(1, 10), 2)
            zones.append(z)
        return zones
