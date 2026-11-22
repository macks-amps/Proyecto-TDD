# Declaración de Fuentes, Librerías y Uso de Inteligencia Artificial — Proyecto HydroFlow

**Curso:** TEI201 — Taller de Diseño en Ingeniería (Universidad Adolfo Ibáñez)  
**Entrega:** Avance #3 — Prototipo IoT Completo  
**Equipo:** Francisca Heredia, Benjamín Ibarra, Maximiliano Jander, Nicolás Pérez  

---

## 1. Librerías Externas Utilizadas

### Firmware Arduino (`firmware/hydroflow_avance3.ino`)
* **`Wire.h` (Arduino Core):** Comunicación serial síncrona I2C (pines SDA/A4 y SCL/A5) con timeout configurado (`Wire.setWireTimeout`) para evitar bloqueos por ruido eléctrico del motor DC.
* **`Adafruit_GFX.h` (Adafruit Industries, Licencia BSD):** Librería gráfica base para renderizado de texto, líneas y coordenadas en pantallas matriciales.
* **`Adafruit_SH110X.h` (Adafruit Industries, Licencia BSD):** Controlador específico para la pantalla OLED monocromática de 1.3" (128×64 píxeles, chip SH1106 en dirección I2C `0x3C`).

### Backend y Dashboard Local (`firmware/dashboard_hydroflow.py`)
* **`pyserial` (`serial` y `serial.tools.list_ports`, Licencia BSD):** Detección automática del puerto COM USB del Arduino Nano y lectura continua de tramas seriales a 9600 baudios.
* **Librerías estándar de Python 3 (`csv`, `json`, `os`, `threading`, `time`, `datetime`, `http.server`):** Persistencia histórica de datos en formato CSV, concurrencia entre lectura serial y servidor HTTP local (`http://localhost:8000`) sin dependencia de conexión a internet.

---

## 2. Código Externo y Referencias Técnicas Adaptadas

* **Lectura de frecuencia por interrupción externa (Sensor YF-S201):** Se adaptó el patrón estándar de conteo de pulsos mediante interrupción hardware (`attachInterrupt` en flanco `FALLING` sobre el pin digital `D2`) y conversión a caudal volumétrico utilizando el factor nominal del fabricante ($7,5\text{ pulsos/s}$ por cada $\text{L/min}$).
* **Acondicionamiento de lectura analógica (Sensor de Voltaje DC 0–25V):** Se implementó la compensación matemática del divisor resistivo interno $5:1$ sobre la entrada analógica `A0` ($V_{\text{real}} = V_{\text{ADC}} \times 5,0$), incorporando promediado móvil de 20 muestras para estabilizar fluctuaciones de escobillas y ruido USB.
* **Modelo de referencia hidrodinámico:** Basado en el principio de captación pasiva mediante rotor Savonius helicoidal de $90^\circ$ descrito por Lepipas & Holmes (2024), *Smart Materials and Structures, 33*(2), 025019.

---

## 3. Declaración de Uso de Inteligencia Artificial (IA)

Durante el desarrollo del software del Avance #3 se utilizó **Gemini (Google)** como asistente técnico de programación y depuración bajo supervisión del equipo:

* **Propósito y prompts empleados:** Se solicitó asistencia para: (a) modularizar el firmware del Arduino Nano integrando lectura simultánea de caudal y voltaje con envío por puerto serial; (b) desarrollar un servidor web local en Python con persistencia automática en `.csv` y visualización gráfica en tiempo real; y (c) diagnosticar fallas de memoria RAM en la pantalla OLED y filtrado de ruido eléctrico en `A0`.
* **Adaptaciones realizadas por el equipo:**
  1. **Calibración de hardware y ruido:** El equipo ajustó el umbral de zona muerta a $0,05\text{ V}$ y el promediado de 20 muestras tras medir el comportamiento real del micromotor DC acoplado directamente sin rodamientos.
  2. **Modelo de proyección sin batería física:** Se adaptó la lógica de decisión del dashboard para estimar potencia sobre una carga de referencia de $100\,\Omega$, proyectar energía diaria acumulada en $30\text{ min}$ de uso doméstico y calcular el tiempo teórico de carga de una celda estándar de $3,7\text{ V} / 2.000\text{ mAh}$ ($7.400\text{ mWh}$).
  3. **Alertas operativas:** Se definieron los umbrales de alerta de reposo, generación activa y detección de fricción/obstrucción ($Q \ge 2,5\text{ L/min}$ con $V < 0,10\text{ V}$) según los ensayos reales en lavamanos.
* **Funcionamiento general del código:** El firmware en Arduino captura pulsos de flujo y muestras de voltaje cada $1\text{ s}$, actualiza la pantalla OLED local y transmite una línea CSV por USB; el script en Python recibe esa trama, la almacena en `datos_hydroflow_2.csv` y sirve un dashboard HTML/Canvas local que grafica las series temporales y evalúa el desempeño energético en vivo.
