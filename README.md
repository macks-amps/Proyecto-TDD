# HydroFlow — Prototipo IoT de Captación Pasiva de Energía Hidroeléctrica Domiciliaria

**Curso:** TEI201 — Taller de Diseño en Ingeniería (Universidad Adolfo Ibáñez)  
**Evaluación:** Avance #3 — Prototipo IoT Completo (23 de noviembre de 2026)  
**Equipo:** Francisca Heredia · Benjamín Ibarra · Maximiliano Jander · Nicolás Pérez  

---

## Descripción del Proyecto
**HydroFlow** es un sistema de captación pasiva (*energy harvesting*) diseñado para aprovechar el flujo hídrico domiciliario mediante una microturbina Savonius helicoidal impresa en 3D acoplada a un micromotor DC operando como dinamo, integrado con telemetría en tiempo real (caudalímetro YF-S201, sensor de voltaje 0–25V, Arduino Nano V3, pantalla OLED 1.3" SH1106 y *dashboard* web local en Python).

---

## Estructura del Repositorio

```text
├── Diseño3D/
│   ├── Planos/
│   │   ├── Plano Caja Pieza 1.png ... Plano Caja Pieza 6.png
│   │   ├── Plano Turbina Savonius 1.png
│   │   └── Plano Turbina Savonius 2.png
│   ├── Renders/
│   │   ├── Render1.Interior.png
│   │   ├── Render2.Turbina.png
│   │   ├── Render3.vistaexterior.png
│   │   ├── Render4.TapaAbierta.png
│   │   ├── Vista Turbina.png
│   │   ├── Vista interior.png
│   │   └── ensamble_exterior.jpg
│   ├── Modelo3DFinalProyecto.f3d
│   └── Planos Turbina HydroFlow Modelo 3D.pdf
├── Docs/
│   ├── Informe TDD 1.pdf
│   ├── Informe TDD 2.pdf
│   └── presentacion_E3.pptx
├── firmware/
│   ├── dashboard_hydroflow.py
│   └── hydroflow_avance3.ino
├── hardware/
│   ├── fotos/
│   ├── BOM.xlsx
│   └── esquematico.pdf
├── testing/
│   ├── prueba_llave_1/
│   ├── prueba_llave_2/
│   └── protocolo_pruebas.pdf
├── FUENTES.md
└── README.md
