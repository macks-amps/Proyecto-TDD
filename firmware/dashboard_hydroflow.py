"""
Proyecto: HydroFlow IoT — Servidor Local de Telemetría, Persistencia CSV y Dashboard Web
Curso: TEI201 — Taller de Diseño en Ingeniería (Universidad Adolfo Ibáñez) - Avance #3
Descripción: Recibe datos seriales desde Arduino Nano a 1 Hz, almacena registros históricos
             en CSV y despliega un dashboard local para diagnóstico y proyección energética.
"""

import csv
import json
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import serial
import serial.tools.list_ports

# --- PARÁMETROS DE CONFIGURACIÓN DEL SERVIDOR Y ALMACENAMIENTO ---
ARCHIVO_CSV = "datos_hydroflow.csv"
PUERTO_WEB = 8000
BAUDRATE = 9600
CAPACIDAD_BATERIA_REF_MWH = 7400.0  # Referencia teórica: celda Li-Ion 3.7V / 2000mAh

# --- ESTADO COMPARTIDO EN MEMORIA PARA EL DASHBOARD EN TIEMPO REAL ---
estado = {
    "conectado": False,
    "puerto": "Buscando Arduino...",
    "timestamp": "--:--:--",
    "caudal": 0.0,
    "pot_esperada": 0.0,
    "voltaje_inst": 0.0,
    "voltaje_1min": 0.0,
    "pot_estimada": 0.0,
    "energia_sesion_mwh": 0.0,
    "almacenamiento_dia_mwh": 0.0,
    "tiempo_carga_horas": 0.0,
    "diagnostico_tipo": "info",
    "diagnostico_texto": "Sistema en espera. Abre el flujo de agua para analizar generación.",
    "historial": []
}
lock = threading.Lock()


def inicializar_csv():
    """Crea el archivo CSV con sus encabezados si aún no existe en el directorio."""
    if not os.path.exists(ARCHIVO_CSV):
        with open(ARCHIVO_CSV, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                "fecha_hora", "caudal_lmin", "pot_esperada_mw",
                "voltaje_inst_v", "voltaje_1min_v", "pot_estimada_mw", "energia_acumulada_mwh"
            ])


def analizar_rendimiento(caudal, v_inst, pot_est):
    """
    Calcula proyecciones de almacenamiento energético y genera alertas diagnósticas
    para la toma de decisiones en función del caudal (L/min), voltaje (V) y potencia (mW).
    """
    # Proyección de almacenamiento con 30 min (0.5 h) de uso diario de agua en el hogar
    almacenamiento_dia = pot_est * 0.5
    # Horas de flujo continuo necesarias para llenar una celda de referencia de 7.400 mWh
    horas_carga = (CAPACIDAD_BATERIA_REF_MWH / pot_est) if pot_est > 0.01 else 0.0

    if caudal < 0.5 and v_inst < 0.05:
        tipo = "info"
        msg = "EN REPOSO: Sin flujo de agua. Abre la llave para medir capacidad de generación."
    elif caudal >= 2.5 and v_inst < 0.10:
        tipo = "danger"
        msg = "ALERTA MECÁNICA: Se detecta flujo de agua, pero voltaje casi nulo. Posible roce del rotor o chorro mal centrado."
    elif v_inst < 0.50:
        tipo = "warning"
        msg = f"GENERACIÓN BAJA ({v_inst:.2f} V): Captación comprobada, pero insuficiente para carga rápida. Justifica uso de rodamientos y elevador Boost."
    else:
        tipo = "success"
        msg = f"BUEN RENDIMIENTO ({v_inst:.2f} V): Supera umbral de 0.50 V. Viable para almacenamiento gradual mediante etapa elevadora."

    return almacenamiento_dia, horas_carga, tipo, msg


def buscar_puerto_arduino():
    """Escanea los puertos seriales USB disponibles y retorna el puerto asociado al Arduino Nano."""
    puertos = list(serial.tools.list_ports.comports())
    for p in puertos:
        desc = (p.description or "").lower()
        if "ch340" in desc or "arduino" in desc or "usb" in desc or "serial" in desc:
            return p.device
    return puertos[0].device if puertos else None


def leer_serial_continuo():
    """
    Hilo en segundo plano que lee tramas CSV desde el puerto serial a 1 Hz,
    integra la energía acumulada, actualiza el estado en memoria y guarda en disco.
    """
    inicializar_csv()
    while True:
        puerto = buscar_puerto_arduino()
        if not puerto:
            with lock:
                estado["conectado"] = False
                estado["puerto"] = "Arduino no detectado (revisa cable USB)"
            time.sleep(2)
            continue

        try:
            with serial.Serial(puerto, BAUDRATE, timeout=2) as ser:
                with lock:
                    estado["conectado"] = True
                    estado["puerto"] = puerto
                time.sleep(2)

                while True:
                    linea = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not linea or linea.startswith("caudal"):
                        continue
                    partes = linea.split(",")
                    if len(partes) == 5:
                        try:
                            caudal = float(partes[0])
                            pot_esp = float(partes[1])
                            v_inst = float(partes[2])
                            v_1min = float(partes[3])
                            pot_est = float(partes[4])
                            ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            hora = datetime.now().strftime("%H:%M:%S")

                            with lock:
                                # Energía acumulada en 1 segundo: mW * (1/3600 h)
                                estado["energia_sesion_mwh"] += pot_est / 3600.0
                                e_acum = estado["energia_sesion_mwh"]
                                alm_dia, h_carga, d_tipo, d_msg = analizar_rendimiento(caudal, v_inst, pot_est)

                                estado.update({
                                    "timestamp": hora,
                                    "caudal": caudal,
                                    "pot_esperada": pot_esp,
                                    "voltaje_inst": v_inst,
                                    "voltaje_1min": v_1min,
                                    "pot_estimada": pot_est,
                                    "almacenamiento_dia_mwh": alm_dia,
                                    "tiempo_carga_horas": h_carga,
                                    "diagnostico_tipo": d_tipo,
                                    "diagnostico_texto": d_msg
                                })
                                estado["historial"].append({"t": hora, "q": caudal, "v": v_inst})
                                if len(estado["historial"]) > 60:
                                    estado["historial"].pop(0)

                            with open(ARCHIVO_CSV, mode="a", newline="", encoding="utf-8") as f:
                                csv.writer(f).writerow([
                                    ahora, caudal, pot_esp, v_inst, v_1min, pot_est, round(e_acum, 5)
                                ])
                        except ValueError:
                            pass
        except Exception:
            with lock:
                estado["conectado"] = False
                estado["puerto"] = "Reconectando..."
            time.sleep(2)


# --- INTERFAZ WEB LOCAL DEL DASHBOARD (HTML + CSS + JS) ---
HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>HydroFlow IoT - Análisis de Generación</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 18px; }
  .badge { padding: 6px 14px; border-radius: 999px; font-size: 13px; font-weight: 600; background: #1e293b; }
  .ok { color: #34d399; border: 1px solid #34d399; }
  .err { color: #f87171; border: 1px solid #f87171; }
  .alerta { padding: 14px 18px; border-radius: 10px; font-weight: 600; margin-bottom: 20px; font-size: 15px; }
  .info { background: #1e293b; border-left: 5px solid #38bdf8; }
  .success { background: #064e3b; border-left: 5px solid #34d399; }
  .warning { background: #451a03; border-left: 5px solid #fbbf24; }
  .danger { background: #450a0a; border-left: 5px solid #f87171; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 20px; }
  .card { background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #334155; }
  .card .label { font-size: 12px; color: #94a3b8; text-transform: uppercase; }
  .card .val { font-size: 26px; font-weight: 700; margin-top: 6px; color: #38bdf8; }
  .card .sub { font-size: 12px; color: #cbd5e1; margin-top: 4px; }
  .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .chart-box { background: #1e293b; padding: 16px; border-radius: 12px; border: 1px solid #334155; }
  canvas { width: 100%; height: 210px; }
  @media (max-width: 800px) { .charts { grid-template-columns: 1fr; } }
</style>
</head>
<body>
  <div class="header">
    <div>
      <h2 style="margin:0;">HydroFlow IoT — Análisis de Generación y Almacenamiento</h2>
      <small style="color:#94a3b8;">TEI201 UAI · Registro histórico guardado en <code>datos_hydroflow.csv</code></small>
    </div>
    <div id="status" class="badge err">Desconectado</div>
  </div>

  <div id="alerta" class="alerta info">Iniciando lectura...</div>

  <div class="grid">
    <div class="card"><div class="label">Caudal Red</div><div class="val" id="caudal">0.0 L/m</div><div class="sub">Sensor YF-S201</div></div>
    <div class="card"><div class="label">Voltaje Generado</div><div class="val" id="v_inst" style="color:#34d399;">0.00 V</div><div class="sub">Promedio 1 min: <span id="v_1min">0.00</span> V</div></div>
    <div class="card"><div class="label">Potencia Esperada / Est.</div><div class="val" id="pot" style="color:#fbbf24;">0.0 / 0.0</div><div class="sub">mW Teórica / mW Estimada</div></div>
    <div class="card"><div class="label">Energía en esta Prueba</div><div class="val" id="e_sesion" style="color:#a78bfa;">0.000 mWh</div><div class="sub">Acumulado real de la sesión</div></div>
    <div class="card"><div class="label">Proyección Uso Diario</div><div class="val" id="e_dia" style="color:#f472b6;">0.00 mWh</div><div class="sub">Estimado con 30 min flujo/día</div></div>
    <div class="card"><div class="label">Tiempo Carga Celda Ref.</div><div class="val" id="t_carga" style="color:#38bdf8;">-- h</div><div class="sub">Para llenar celda 7.400 mWh</div></div>
  </div>

  <div class="charts">
    <div class="chart-box"><h4 style="margin:0 0 10px 0;">Caudal en Tiempo Real (L/min)</h4><canvas id="chartQ" width="500" height="210"></canvas></div>
    <div class="chart-box"><h4 style="margin:0 0 10px 0;">Voltaje en Tiempo Real (V)</h4><canvas id="chartV" width="500" height="210"></canvas></div>
  </div>

<script>
function dibujar(id, datos, color, maxRef, uni) {
  const c = document.getElementById(id), ctx = c.getContext("2d");
  const w = c.width, h = c.height;
  ctx.clearRect(0, 0, w, h);
  ctx.strokeStyle = "#334155";
  for (let i = 1; i <= 4; i++) {
    let y = (h - 25) * (i / 4);
    ctx.beginPath(); ctx.moveTo(35, y); ctx.lineTo(w - 10, y); ctx.stroke();
  }
  if (datos.length < 2) return;
  const maxVal = Math.max(maxRef, ...datos);
  ctx.fillStyle = "#94a3b8"; ctx.font = "11px sans-serif";
  ctx.fillText(maxVal.toFixed(1) + uni, 2, 12);
  ctx.fillText("0.0" + uni, 2, h - 25);
  ctx.strokeStyle = color; ctx.lineWidth = 2.5; ctx.beginPath();
  datos.forEach((v, i) => {
    const x = 40 + (i / (datos.length - 1)) * (w - 55);
    const y = (h - 25) - (v / maxVal) * (h - 35);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}

async function refrescar() {
  try {
    const d = await (await fetch("/api/datos")).json();
    const st = document.getElementById("status");
    st.textContent = d.conectado ? `Conectado (${d.puerto}) · ${d.timestamp}` : `Desconectado (${d.puerto})`;
    st.className = "badge " + (d.conectado ? "ok" : "err");

    const al = document.getElementById("alerta");
    al.textContent = d.diagnostico_texto;
    al.className = "alerta " + d.diagnostico_tipo;

    document.getElementById("caudal").textContent = d.caudal.toFixed(1) + " L/m";
    document.getElementById("v_inst").textContent = d.voltaje_inst.toFixed(2) + " V";
    document.getElementById("v_1min").textContent = d.voltaje_1min.toFixed(2);
    document.getElementById("pot").textContent = `${d.pot_esperada.toFixed(1)} / ${d.pot_estimada.toFixed(2)}`;
    document.getElementById("e_sesion").textContent = d.energia_sesion_mwh.toFixed(3) + " mWh";
    document.getElementById("e_dia").textContent = d.almacenamiento_dia_mwh.toFixed(2) + " mWh";
    document.getElementById("t_carga").textContent = d.tiempo_carga_horas > 0 ? d.tiempo_carga_horas.toFixed(0) + " h" : "-- h";

    dibujar("chartQ", d.historial.map(p => p.q), "#38bdf8", 15.0, " L/m");
    dibujar("chartV", d.historial.map(p => p.v), "#34d399", 1.0, " V");
  } catch (e) {}
}
setInterval(refrescar, 1000);
refrescar();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    """Servidor HTTP local que sirve el dashboard web y el endpoint JSON de telemetría."""

    def do_GET(self):
        """Responde con los datos en vivo en /api/datos o con la interfaz HTML en la raíz."""
        if self.path == "/api/datos":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with lock:
                self.wfile.write(json.dumps(estado).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))

    def log_message(self, format, *args):
        """Suprime los registros de peticiones HTTP en consola para mantener la salida limpia."""
        pass


# --- PUNTO DE ENTRADA PRINCIPAL ---
if __name__ == "__main__":
    threading.Thread(target=leer_serial_continuo, daemon=True).start()
    print(f"Dashboard abierto en: http://localhost:{PUERTO_WEB}")
    print(f"Archivo de datos en:  {os.path.abspath(ARCHIVO_CSV)}")
    HTTPServer(("0.0.0.0", PUERTO_WEB), Handler).serve_forever()
