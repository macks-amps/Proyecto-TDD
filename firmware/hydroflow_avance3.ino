#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

// Pantalla OLED 1.3" (128x64 píxeles, chip SH1106)
Adafruit_SH1106G display = Adafruit_SH1106G(128, 64, &Wire, -1);

// Pines de los sensores
const int pinCaudal = 2;     // Cable amarillo del YF-S201
const int pinVoltaje = A0;   // Pin 'S' del sensor de voltaje

// Variables de caudal
volatile int pulsos = 0;
float caudal_Lmin = 0.0;
unsigned long tiempoAnterior = 0;
const float FACTOR_EFICIENCIA = 15.0;

// Variables ligeras para promedio de 1 minuto (sin gastar RAM)
float voltaje1Min = 0.0;
int nMuestras = 0;

void contarPulsos() {
  pulsos++;
}

void setup() {
  if (!display.begin(0x3C, true)) {
    while (1); // Si falla la pantalla, se detiene aquí
  }

  pinMode(pinCaudal, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(pinCaudal), contarPulsos, FALLING);

  display.clearDisplay();
  display.setTextColor(SH110X_WHITE);
}

void loop() {
  if ((millis() - tiempoAnterior) > 1000) {
    detachInterrupt(digitalPinToInterrupt(pinCaudal));

    // 1. Caudal real y potencia esperada
    caudal_Lmin = ((1000.0 / (millis() - tiempoAnterior)) * pulsos) / 7.5;
    tiempoAnterior = millis();
    pulsos = 0;
    float potenciaEsperada_mW = caudal_Lmin * FACTOR_EFICIENCIA;

    // 2. Voltaje instantáneo (promedio rápido de 20 muestras)
    long sumaADC = 0;
    for (int i = 0; i < 20; i++) {
      sumaADC += analogRead(pinVoltaje);
      delay(2);
    }
    float voltajeInst = ((sumaADC / 20.0) * 5.0 / 1023.0) * 5.0;

    if (voltajeInst < 0.09) {
      voltajeInst = 0.0;
    }

    // 3. Promedio continuo de 1 minuto (sin arreglo en memoria)
    if (nMuestras < 60) {
      nMuestras++;
    }
    voltaje1Min = voltaje1Min + (voltajeInst - voltaje1Min) / nMuestras;

    // 4. Mostrar en pantalla OLED
    display.clearDisplay();
    display.setTextSize(1);

    display.setCursor(0, 0);
    display.print(F("Flujo: "));
    display.print(caudal_Lmin, 1);
    display.println(F(" L/min"));

    display.setCursor(0, 13);
    display.print(F("P.Esp: "));
    display.print(potenciaEsperada_mW, 1);
    display.println(F(" mW"));

    display.drawLine(0, 25, 128, 25, SH110X_WHITE);

    display.setCursor(0, 32);
    display.print(F("V.Inst: "));
    display.print(voltajeInst, 2);
    display.println(F(" V"));

    display.setCursor(0, 48);
    display.print(F("V.1min: "));
    display.print(voltaje1Min, 2);
    display.println(F(" V"));

    display.display();

    attachInterrupt(digitalPinToInterrupt(pinCaudal), contarPulsos, FALLING);
  }
}
