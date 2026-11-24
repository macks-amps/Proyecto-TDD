# HydroFlow IoT — Sistema de Captación Pasiva de Energía Hidroeléctrica Domiciliaria

**Curso:** TEI201 — Taller de Diseño en Ingeniería (Universidad Adolfo Ibáñez)  
**Evaluación:** Avance #3 — Prototipo IoT Completo  
**Equipo:** Francisca Heredia · Benjamín Ibarra · Maximiliano Jander · Nicolás Pérez  

---

## 1. Descripción del Proyecto

**HydroFlow** es un sistema de captación pasiva de energía (*energy harvesting*) diseñado para mitigar la vulnerabilidad energética domiciliaria frente a cortes de suministro eléctrico en Chile[cite: 22, 23]. El prototipo aprovecha la energía cinética del flujo de agua de la red sanitaria urbana mediante una **microturbina Savonius helicoidal de 90°** impresa en 3D acoplada a un micromotor DC (operando como dinamo), integrando telemetría en tiempo real para monitorear caudal, voltaje generado y proyección de almacenamiento energético[cite: 21, 22].

### Ciclo IoT Implementado
1. **Captura en tiempo real:** Lectura simultánea de caudal ($\text{L/min}$) y voltaje generado ($\text{V}$) a $1\text{ Hz}$ mediante Arduino Nano.
2. **Persistencia estructurada:** Registro histórico continuo con marca de tiempo en archivo local `.csv` sin dependencia de conexión a internet.
3. **Visualización y toma de decisiones:** Dashboard web local (`http://localhost:8000`) con gráficas en vivo, cálculo de energía acumulada ($\text{mWh}$), proyección de carga diaria y alertas automáticas de fricción u obstrucción.

---

## 2. Estructura del Repositorio

```text
Proyecto-TDD/
├── README.md                  # Documentación principal y guía de ejecución
├── FUENTES.md                 # Declaración obligatoria de librerías, código adaptado y uso de IA
├── firmware/                  # Código del microcontrolador y servidor dashboard
│   ├── hydroflow_avance3.ino  # Firmware Arduino Nano (sensores + OLED + telemetría serial)
│   └── dashboard_hydroflow.py # Backend Python, persistencia CSV y dashboard web local
├── hardware/                  # Electrónica y fabricación
│   ├── esquematico.pdf        # Diagrama completo de conexiones y pines
│   ├── BOM.xlsx               # Lista de materiales y costos en CLP
│   └── fotos/                 # Fotografías del prototipo físico desde distintos ángulos
├── diseño-3d/                 # Modelado CAD y planimetría
│   ├── hydroflow_ensamble.f3d # Gemelo 3D en Fusion 360 (carcasa + componentes internos)
│   ├── planos_acotados.pdf    # Planos ortogonales con cotas, tolerancias y escala
│   └── renders/               # Vistas renderizadas exterior e interior/explosionada
├── testing/                   # Validación experimental
│   ├── protocolo_pruebas.pdf  # Protocolo, métricas, análisis de fallas y validación
│   └── datos_hydroflow_2.csv  # Registro experimental crudo capturado a 1 Hz
└── docs/                      # Informes previos y presentación final
    ├── Informe TDD 1.pdf      # Entrega 1: Problemática y diseño conceptual
    ├── Informe TDD 2.pdf      # Entrega 2: Prototipo Alpha y pruebas desacopladas
    └── presentacion_E3.pptx    # Diapositivas de exposición Avance #3
