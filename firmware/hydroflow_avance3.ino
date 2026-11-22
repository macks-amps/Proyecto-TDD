/*
 * Proyecto: HydroFlow - Sistema IoT de Captación Pasiva Hidroeléctrica Domiciliaria
 * Curso: TEI201 - Taller de Diseño en Ingeniería (UAI) - Avance #3
 * Descripción: Adquiere caudal (YF-S201) y voltaje generado (0-25V), calcula potencia
 *              esperada vs. estimada, muestra en OLED y envía telemetría CSV por USB.
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

// --- CONFIGURACIÓN DE PANTALLA OLED 1.3" (SH1106) ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SH1106G display = Adafruit_SH1106G(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// --- PINES DE SENSORES ---
const int PIN_CAUDAL = 2;     // Cable amarillo sensor YF-S201 (Interrupción 0)
const int PIN_VOLTAJE = A0;   // Pin 'S' sensor de voltaje DC 0-25V

// --- PARÁMETROS DEL MODELO ---
const float PULSOS_POR_LMIN = 7.5;        // Calibración de fábrica YF-S201
const float FACTOR_PREDICCION = 15.0;     // Modelo base: 15 mW esperados por L/min
const float RESISTENCIA_REF = 100.0;      // Carga de referencia (Ohms) para estimar mW sin carga física
const unsigned long INTERVALO_MS = 1000;  // Muestreo cada 1 segundo (1 Hz)

// --- VARIABLES GLOBALES ---
volatile unsigned int contadorPulsos = 0;
unsigned long tiempoAnterior = 0;
float voltajePromedio1Min = 0.0;
int muestrasMinuto = 0;

void contarPulso() {
  contadorPulsos++;
}

// Módulo 1: Calcular caudal en L/min
float obtenerCaudal(unsigned long deltaMs) {
  float frecuenciaHz = (1000.0 / deltaMs) * contadorPulsos;
  return frecuenciaHz / PULSOS_POR_LMIN;
}

// Módulo 2: Leer voltaje real con filtro de promedio y corte de ruido base
float obtenerVoltaje() {
  long sumaADC = 0;
  for (int i = 0; i < 20; i++) {
    sumaADC += analogRead(PIN_VOLTAJE);
    delay(2);
  }
  float voltajePin = (sumaADC / 20.0) * (5.0 / 1023.0);
  float voltajeReal = voltajePin * 5.0; // Divisor resistivo 5:1 del módulo

  if (voltajeReal < 0.15) {
    voltajeReal = 0.0; // Elimina estática residual cuando el motor está detenido
  }
  return voltajeReal;
}

// Módulo 3: Dibujar valores en pantalla OLED
void actualizarPantalla(float caudal, float potEsp, float vInst, float v1Min) {
  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(0, 0);
  display.print(F("Flujo: "));
  display.print(caudal, 1);
  display.println(F(" L/min"));

  display.setCursor(0, 13);
  display.print(F("P.Esp: "));
  display.print(potEsp, 1);
  display.println(F(" mW"));

  display.drawLine(0, 25, 128, 25, SH110X_WHITE);

  display.setCursor(0, 32);
  display.print(F("V.Inst: "));
  display.print(vInst, 2);
  display.println(F(" V"));

  display.setCursor(0, 48);
  display.print(F("V.1min: "));
  display.print(v1Min, 2);
  display.println(F(" V"));

  display.display();
}

// Módulo 4: Enviar datos al PC en formato CSV
void enviarDatosUSB(float caudal, float potEsp, float vInst, float v1Min, float potEst) {
  Serial.print(caudal, 2);
  Serial.print(F(","));
  Serial.print(potEsp, 2);
  Serial.print(F(","));
  Serial.print(vInst, 3);
  Serial.print(F(","));
  Serial.print(v1Min, 3);
  Serial.print(F(","));
  Serial.println(potEst, 2);
}

void setup() {
  Serial.begin(9600);
  Wire.begin();
  Wire.setWireTimeout(3000, true); // Evita bloqueos de pantalla por ruido del motor

  if (!display.begin(0x3C, true)) {
    while (1);
  }

  pinMode(PIN_CAUDAL, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_CAUDAL), contarPulso, FALLING);

  display.clearDisplay();
  display.setTextColor(SH110X_WHITE);

  // Encabezado inicial para el puerto serial
  Serial.println(F("caudal_lmin,pot_esperada_mw,voltaje_inst_v,voltaje_1min_v,pot_estimada_mw"));
}

void loop() {
  unsigned long tiempoActual = millis();
  if ((tiempoActual - tiempoAnterior) >= INTERVALO_MS) {
    detachInterrupt(digitalPinToInterrupt(PIN_CAUDAL));

    float caudal = obtenerCaudal(tiempoActual - tiempoAnterior);
    contadorPulsos = 0;
    tiempoAnterior = tiempoActual;

    float vInst = obtenerVoltaje();
    float potEsp = caudal * FACTOR_PREDICCION;
    float potEst = ((vInst * vInst) / RESISTENCIA_REF) * 1000.0;

    if (muestrasMinuto < 60) {
      muestrasMinuto++;
    }
    voltajePromedio1Min += (vInst - voltajePromedio1Min) / muestrasMinuto;

    actualizarPantalla(caudal, potEsp, vInst, voltajePromedio1Min);
    enviarDatosUSB(caudal, potEsp, vInst, voltajePromedio1Min, potEst);

    attachInterrupt(digitalPinToInterrupt(PIN_CAUDAL), contarPulso, FALLING);
  }
}