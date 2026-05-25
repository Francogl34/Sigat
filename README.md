SIGAT - Sistema Inteligente de Monitoreo, Predicción y Alerta Temprana de Incendios Forestales
Universidad Privada Franz Tamayo | Cochabamba, Bolivia
Autor: Franco Guerra Roca

CONFIGURACIÓN DE BASE DE DATOS
================================

1. Crear la base de datos en PostgreSQL:

   psql -U postgres
   CREATE DATABASE sigat_db;
   CREATE USER sigat_user WITH PASSWORD 'sigat_pass';
   GRANT ALL PRIVILEGES ON DATABASE sigat_db TO sigat_user;
   \q

2. Copiar el archivo de entorno:

   cp .env.example .env

3. Editar .env con tus credenciales reales si son distintas a las por defecto.

4. Instalar dependencias:

   pip install -r requirements.txt

5. Ejecutar la aplicación:

   python app.py

   La base de datos se inicializa automáticamente al arrancar (tablas y datos semilla).

TABLAS CREADAS AUTOMÁTICAMENTE
================================
- sensors           → sensores registrados
- sensor_readings   → lecturas históricas de cada sensor
- zones             → zonas de monitoreo
- alerts            → historial de alertas generadas
- predictions       → historial de predicciones
- hourly_history    → resumen histórico por hora

ENDPOINTS API
================================
GET /api/sensors        → lecturas actuales de sensores (guarda en DB)
GET /api/alerts         → alertas evaluadas (guarda en DB)
GET /api/alerts/history → historial de alertas desde DB
GET /api/prediction     → predicciones (guarda en DB)
GET /api/zones          → zonas de riesgo
GET /api/history        → historial horario
GET /api/stats          → estadísticas generales
GET /api/sensors/db     → lecturas históricas desde DB

Version 0.7
