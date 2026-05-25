/* ============================================
   SIGAT — JavaScript Principal
   Módulos: Nav, Charts, API, Render
   ============================================ */

// ===== STATE =====
let currentView = 'dashboard';
let charts = {};
let alertFilter = 'ALL';
let refreshInterval = null;

// ===== NAVIGATION =====
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    const view = item.dataset.view;
    switchView(view);
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');
  });
});

function switchView(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(`view-${view}`).classList.add('active');
  document.getElementById('view-title').textContent = {
    dashboard: 'Panel de Control',
    sensors: 'Sensores IoT',
    alerts: 'Centro de Alertas',
    prediction: 'Predicción IA',
    zones: 'Zonas Forestales',
    history: 'Historial 24h',
  }[view] || '';
  currentView = view;
  loadViewData(view);
}

function loadViewData(view) {
  switch(view) {
    case 'dashboard': loadDashboard(); break;
    case 'sensors': loadSensors(); break;
    case 'alerts': loadFullAlerts(); break;
    case 'prediction': loadPrediction(); break;
    case 'zones': loadZones(); break;
    case 'history': loadHistory(); break;
  }
}

// ===== TIME CLOCK =====
function updateClock() {
  const el = document.getElementById('sidebar-time');
  if (el) el.textContent = new Date().toLocaleTimeString('es-BO', { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ===== API CALLS =====
async function api(endpoint) {
  try {
    const res = await fetch(endpoint);
    return await res.json();
  } catch(e) {
    console.error('API error:', endpoint, e);
    return null;
  }
}

// ===== DASHBOARD =====
async function loadDashboard() {
  const [stats, alerts, sensors] = await Promise.all([
    api('/api/stats'), api('/api/alerts'), api('/api/sensors')
  ]);
  if (stats) renderStats(stats);
  if (alerts) {
    renderAlertsList(alerts);
    document.getElementById('alert-count').textContent = `${alerts.filter(a=>a.level==='CRÍTICO'||a.level==='ALTO').length} alertas`;
  }
  if (sensors) {
    renderMapSensors(sensors);
    renderBarCharts(sensors);
  }
}

function renderStats(s) {
  document.getElementById('stat-critical').textContent = s.critical_zones;
  document.getElementById('stat-temp').textContent = s.avg_temp + '°';
  document.getElementById('stat-hum').textContent = s.avg_humidity + '%';
  document.getElementById('stat-smoke').textContent = s.avg_smoke;
  document.getElementById('stat-sensors').textContent = s.active_sensors;
  document.getElementById('stat-alerts-today').textContent = s.total_alerts_today;
}

function renderAlertsList(alerts) {
  const el = document.getElementById('alerts-list');
  if (!el) return;
  el.innerHTML = alerts.map(a => `
    <div class="alert-item ${a.level}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
        <div class="alert-zone">${a.zone}</div>
        <span class="alert-level-pill" style="background:${a.color}20;color:${a.color};border:1px solid ${a.color}40">${a.level}</span>
      </div>
      <div class="alert-msg">${a.message}</div>
      <div class="alert-meta">
        <span>🌡️ ${a.temperature}°C</span>
        <span>💧 ${a.humidity}%</span>
        <span>💨 ${a.smoke_ppm} PPM</span>
        <span>${new Date(a.timestamp).toLocaleTimeString('es-BO', {hour12:false})}</span>
      </div>
    </div>
  `).join('');
}

// ===== MAP SENSORS =====
function renderMapSensors(sensors) {
  const container = document.getElementById('map-sensors');
  if (!container) return;

  // Map lat/lng to SVG coords (approximate for Cochabamba area)
  const latMin = -17.41, latMax = -17.32;
  const lngMin = -66.28, lngMax = -66.00;

  const toX = lng => ((lng - lngMin) / (lngMax - lngMin)) * 560 + 20;
  const toY = lat => ((lat - latMax) / (latMin - latMax)) * 340 + 20;

  const colors = { 'CRÍTICO': '#FF2D2D', 'ALTO': '#FF7A00', 'MEDIO': '#FFD600', 'BAJO': '#00C853' };

  container.innerHTML = sensors.map((s, i) => {
    const x = toX(s.lng), y = toY(s.lat);
    const c = colors[s.risk_level] || '#888';
    return `
      <g>
        <circle cx="${x}" cy="${y}" r="14" fill="${c}15" stroke="${c}" stroke-width="1" opacity="0.5">
          <animate attributeName="r" values="10;18;10" dur="${1.5+i*0.3}s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.5;0.1;0.5" dur="${1.5+i*0.3}s" repeatCount="indefinite"/>
        </circle>
        <circle cx="${x}" cy="${y}" r="5" fill="${c}" filter="url(#glow)"/>
        <text x="${x+8}" y="${y-8}" fill="${c}" font-size="9" font-family="Space Mono">${s.sensor_id}</text>
        <text x="${x+8}" y="${y+2}" fill="#aaa" font-size="8" font-family="Space Mono">${s.temperature}°C</text>
      </g>
    `;
  }).join('');
}

// ===== BAR CHARTS =====
function renderBarCharts(sensors) {
  const labels = sensors.map(s => s.sensor_id);
  const riskColors = { 'CRÍTICO': '#FF2D2D', 'ALTO': '#FF7A00', 'MEDIO': '#FFD600', 'BAJO': '#00C853' };
  const getColors = key => sensors.map(s => riskColors[s.risk_level] + 'CC');

  const chartDefaults = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 } }, grid: { color: '#1e3320' } },
      y: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 } }, grid: { color: '#1e3320' } }
    }
  };

  makeChart('temp-chart', 'bar', labels,
    [{ data: sensors.map(s=>s.temperature), backgroundColor: getColors('temperature'), borderRadius: 4 }],
    { ...chartDefaults, scales: { ...chartDefaults.scales, y: { ...chartDefaults.scales.y, suggestedMin: 0 } } }
  );
  makeChart('hum-chart', 'bar', labels,
    [{ data: sensors.map(s=>s.humidity), backgroundColor: '#00B4FFCC', borderRadius: 4 }],
    chartDefaults
  );
  makeChart('smoke-chart', 'bar', labels,
    [{ data: sensors.map(s=>s.smoke_ppm), backgroundColor: '#aa00ffCC', borderRadius: 4 }],
    chartDefaults
  );
}

function makeChart(id, type, labels, datasets, options) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(ctx, {
    type, data: { labels, datasets },
    options: { ...options, animation: { duration: 800 } }
  });
}

// ===== SENSORS VIEW =====
async function loadSensors() {
  const sensors = await api('/api/sensors');
  if (!sensors) return;
  const el = document.getElementById('sensor-cards');
  if (!el) return;

  const riskColors = { 'CRÍTICO': '#FF2D2D', 'ALTO': '#FF7A00', 'MEDIO': '#FFD600', 'BAJO': '#00C853' };

  el.innerHTML = sensors.map(s => {
    const tempPct = Math.min(100, (s.temperature / 60) * 100);
    const humPct = s.humidity;
    const smokePct = Math.min(100, (s.smoke_ppm / 900) * 100);
    const c = riskColors[s.risk_level];
    return `
    <div class="sensor-card">
      <div class="sensor-header">
        <div>
          <div class="sensor-id">${s.sensor_id}</div>
          <div class="sensor-name">${s.name}</div>
        </div>
        <span class="risk-pill risk-${s.risk_level}">${s.risk_level}</span>
      </div>
      <div class="sensor-body">
        <div class="sensor-readings">
          <div class="reading-item">
            <div class="reading-label">Temperatura</div>
            <div class="reading-val" style="color:${c}">${s.temperature}<span class="reading-unit">°C</span></div>
          </div>
          <div class="reading-item">
            <div class="reading-label">Humedad</div>
            <div class="reading-val" style="color:#00B4FF">${s.humidity}<span class="reading-unit">%</span></div>
          </div>
          <div class="reading-item">
            <div class="reading-label">Humo PPM</div>
            <div class="reading-val" style="color:#aa00ff">${s.smoke_ppm}<span class="reading-unit">ppm</span></div>
          </div>
          <div class="reading-item">
            <div class="reading-label">Viento</div>
            <div class="reading-val" style="color:#00C853">${s.wind_speed}<span class="reading-unit">km/h</span></div>
          </div>
        </div>
        <div class="sensor-bar-wrap">
          <div class="sensor-bar-label"><span>Temperatura</span><span>${s.temperature}°C</span></div>
          <div class="sensor-bar-bg"><div class="sensor-bar-fill" style="width:${tempPct}%;background:${c}"></div></div>
        </div>
        <div class="sensor-bar-wrap">
          <div class="sensor-bar-label"><span>Humedad</span><span>${humPct}%</span></div>
          <div class="sensor-bar-bg"><div class="sensor-bar-fill" style="width:${humPct}%;background:#00B4FF"></div></div>
        </div>
        <div class="sensor-bar-wrap">
          <div class="sensor-bar-label"><span>Humo</span><span>${s.smoke_ppm} PPM</span></div>
          <div class="sensor-bar-bg"><div class="sensor-bar-fill" style="width:${smokePct}%;background:#aa00ff"></div></div>
        </div>
        <div class="sensor-bar-wrap">
          <div class="sensor-bar-label"><span>CO₂</span><span>${s.co2_ppm} PPM</span></div>
          <div class="sensor-bar-bg"><div class="sensor-bar-fill" style="width:${Math.min(100,(s.co2_ppm/2000)*100)}%;background:#FFD600"></div></div>
        </div>
      </div>
      <div class="sensor-footer">
        <span>📡 LoRa Mesh</span>
        <span>${new Date(s.timestamp).toLocaleTimeString('es-BO',{hour12:false})}</span>
      </div>
    </div>`;
  }).join('');
}

// ===== ALERTS VIEW =====
async function loadFullAlerts() {
  const alerts = await api('/api/alerts');
  if (!alerts) return;
  renderFullAlerts(alerts);

  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      alertFilter = btn.dataset.filter;
      const filtered = alertFilter === 'ALL' ? alerts : alerts.filter(a => a.level === alertFilter);
      renderFullAlerts(filtered);
    });
  });
}

function renderFullAlerts(alerts) {
  const el = document.getElementById('full-alerts-list');
  if (!el) return;
  el.innerHTML = alerts.map(a => `
    <div class="full-alert-card">
      <div class="full-alert-header">
        <div>
          <div style="font-family:var(--font-display);font-size:15px;font-weight:600">${a.zone}</div>
          <div style="font-family:var(--font-mono);font-size:10px;color:var(--text-muted)">${a.sensor_id}</div>
        </div>
        <span class="risk-pill risk-${a.level}">${a.level}</span>
      </div>
      <div class="full-alert-body">
        <div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px">${a.message}</div>
        <div class="alert-action">→ ${a.recommended_action}</div>
        <div class="alert-readings">
          <div class="mini-reading">🌡️ <span>${a.temperature}°C</span></div>
          <div class="mini-reading">💧 <span>${a.humidity}%</span></div>
          <div class="mini-reading">💨 <span>${a.smoke_ppm} PPM</span></div>
          <div class="mini-reading">🌬️ <span>${a.wind_speed} km/h</span></div>
        </div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--text-muted);margin-top:10px">${new Date(a.timestamp).toLocaleString('es-BO')}</div>
      </div>
    </div>
  `).join('');
}

// ===== PREDICTION VIEW =====
async function loadPrediction() {
  const data = await api('/api/prediction');
  if (!data) return;

  // Hourly forecast chart
  const labels = data.hourly_forecast.map(h => h.hour);
  const probs = data.hourly_forecast.map(h => h.probability);
  const colors = probs.map(p => p > 60 ? '#FF2D2DCC' : p > 35 ? '#FF7A00CC' : '#00C853CC');

  makeChart('forecast-chart', 'line', labels, [{
    data: probs,
    borderColor: '#FF7A00',
    backgroundColor: 'rgba(255,122,0,0.1)',
    pointBackgroundColor: colors,
    pointRadius: 4,
    fill: true,
    tension: 0.4,
  }], {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 }, maxRotation: 0, maxTicksLimit: 12 }, grid: { color: '#1e3320' } },
      y: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 }, callback: v => v + '%' }, grid: { color: '#1e3320' }, suggestedMax: 100 }
    }
  });

  // Model info
  const mi = data.model_info;
  document.getElementById('model-info').innerHTML = `
    <div><strong>MODELO</strong>${mi.name}</div>
    <div><strong>VARIABLES</strong>${mi.variables.join(', ')}</div>
    <div><strong>ACTUALIZADO</strong>${new Date(mi.last_updated).toLocaleString('es-BO')}</div>
    <div><strong>SENSORES</strong>6 nodos IoT activos</div>
    <div><strong>PROTOCOLO</strong>LoRa WAN + Mesh</div>
  `;

  // Zone forecasts
  const trendColors = { 'ASCENDENTE': '#FF2D2D', 'ESTABLE_ALTO': '#FF7A00', 'DESCENDENTE': '#00C853', 'ESTABLE': '#FFD600' };
  const el = document.getElementById('zone-forecasts');
  el.innerHTML = data.zone_forecasts.map(zf => {
    const prob = zf.current_probability;
    const c = prob > 60 ? '#FF2D2D' : prob > 35 ? '#FF7A00' : prob > 20 ? '#FFD600' : '#00C853';
    return `
    <div class="zone-forecast-card">
      <div class="zfc-header">
        <div>
          <div class="zfc-name">${zf.zone}</div>
          <div style="font-family:var(--font-mono);font-size:10px;color:${trendColors[zf.trend]}">${zf.trend.replace('_',' ')}</div>
        </div>
        <div class="prob-circle" style="border-color:${c}">
          <div class="prob-val" style="color:${c}">${prob}%</div>
          <div class="prob-label">RIESGO</div>
        </div>
      </div>
      <div class="forecast-hours">
        <div class="fh-item"><div class="fh-label">+3h</div><div class="fh-val" style="color:${c}">${zf.forecast_3h}%</div></div>
        <div class="fh-item"><div class="fh-label">+6h</div><div class="fh-val" style="color:${c}">${zf.forecast_6h}%</div></div>
        <div class="fh-item"><div class="fh-label">+12h</div><div class="fh-val" style="color:${c}">${zf.forecast_12h}%</div></div>
        <div class="fh-item"><div class="fh-label">Confianza</div><div class="fh-val" style="color:#00B4FF;font-size:14px">${zf.confidence}%</div></div>
      </div>
      <div class="risk-factors">
        ${zf.risk_factors.map(f=>`<div class="rf-item">${f}</div>`).join('')}
      </div>
    </div>`;
  }).join('');
}

// ===== ZONES VIEW =====
async function loadZones() {
  const zones = await api('/api/zones');
  if (!zones) return;
  const el = document.getElementById('zone-cards');
  const riskColors = { 'CRÍTICO': '#FF2D2D', 'ALTO': '#FF7A00', 'MEDIO': '#FFD600', 'BAJO': '#00C853' };
  el.innerHTML = zones.map(z => {
    const c = riskColors[z.current_risk];
    const firePct = Math.min(100, (z.fire_index / 10) * 100);
    return `
    <div class="zone-card">
      <div class="zone-card-header">
        <div>
          <div class="zone-card-name">${z.name}</div>
          <div class="zone-card-id">${z.id} · ${z.sensors.join(', ')}</div>
        </div>
        <span class="risk-pill risk-${z.current_risk}">${z.current_risk}</span>
      </div>
      <div class="zone-card-body">
        <div class="zone-meta">
          <div class="zone-meta-item"><label>Área</label><span>${z.area_ha.toLocaleString()} ha</span></div>
          <div class="zone-meta-item"><label>Altitud</label><span>${z.altitude_m} msnm</span></div>
          <div class="zone-meta-item"><label>Temperatura</label><span style="color:${c}">${z.temperature}°C</span></div>
          <div class="zone-meta-item"><label>Humedad</label><span style="color:#00B4FF">${z.humidity}%</span></div>
          <div class="zone-meta-item"><label>Vegetación</label><span style="font-size:12px">${z.vegetation}</span></div>
          <div class="zone-meta-item"><label>Población cercana</label><span>${z.population_nearby.toLocaleString()}</span></div>
        </div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--text-muted);margin-bottom:4px">
          Índice de riesgo de fuego: <span style="color:${c}">${z.fire_index}/10</span>
        </div>
        <div class="zone-fire-index">
          <div class="zone-fire-fill" style="width:${firePct}%;background:linear-gradient(90deg,#00C853,${c})"></div>
        </div>
      </div>
      <div class="zone-card-footer">
        <span>Prioridad: ${z.priority}</span>
        <span>Último evento: ${z.last_incident}</span>
      </div>
    </div>`;
  }).join('');
}

// ===== HISTORY VIEW =====
async function loadHistory() {
  const history = await api('/api/history');
  if (!history) return;

  const labels = history.map(h => h.hour);
  makeChart('history-chart', 'line', labels, [
    { label: 'Temperatura °C', data: history.map(h=>h.avg_temp), borderColor: '#FF7A00', backgroundColor: '#FF7A0015', tension: 0.4, fill: true, pointRadius: 2 },
    { label: 'Humedad %', data: history.map(h=>h.avg_humidity), borderColor: '#00B4FF', backgroundColor: '#00B4FF10', tension: 0.4, fill: true, pointRadius: 2 },
    { label: 'Humo PPM', data: history.map(h=>h.avg_smoke), borderColor: '#aa00ff', backgroundColor: '#aa00ff10', tension: 0.4, fill: true, pointRadius: 2 },
  ], {
    responsive: true,
    plugins: {
      legend: { labels: { color: '#8aaa8a', font: { family: 'Space Mono', size: 10 }, boxWidth: 12 } }
    },
    scales: {
      x: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 }, maxTicksLimit: 12, maxRotation: 0 }, grid: { color: '#1e3320' } },
      y: { ticks: { color: '#4a6a4a', font: { family: 'Space Mono', size: 9 } }, grid: { color: '#1e3320' } }
    }
  });

  document.getElementById('history-table').innerHTML = `
    <div class="history-table-wrap">
    <table class="history-tbl">
      <thead><tr><th>Hora</th><th>Temp. Prom (°C)</th><th>Humedad Prom (%)</th><th>Humo Prom (PPM)</th><th>Incidentes</th></tr></thead>
      <tbody>
        ${history.map(h=>`
          <tr>
            <td>${h.hour}</td>
            <td>${h.avg_temp}</td>
            <td>${h.avg_humidity}</td>
            <td>${h.avg_smoke}</td>
            <td class="${h.incidents>0?'incidents-val':''}">${h.incidents > 0 ? '⚠️ '+h.incidents : '—'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
    </div>`;
}

// ===== REFRESH BUTTON =====
document.getElementById('refresh-btn').addEventListener('click', () => {
  loadViewData(currentView);
  showToast('🔄 Datos actualizados correctamente');
});

// ===== AUTO REFRESH =====
function startAutoRefresh() {
  refreshInterval = setInterval(() => {
    if (currentView === 'dashboard') loadDashboard();
  }, 15000);
}

// ===== TOAST =====
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}

// ===== INIT =====
loadDashboard();
startAutoRefresh();
showToast('🔥 SIGAT conectado — Monitoreo activo');
