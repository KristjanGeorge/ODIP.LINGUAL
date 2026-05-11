# Arquitectura LingualParam-CSM™ (ODIP_L)

## Visión general

```
┌─────────────────────────────────────────────────────────┐
│                   ELECTRON (proceso principal)           │
│  main.ts                                                 │
│  ├── Spawn proceso Python (ipc_server.py)               │
│  ├── BrowserWindow 1920×1080                            │
│  └── ipcMain handlers → HTTP → FastAPI                  │
└───────────────┬─────────────────────────────────────────┘
                │ contextBridge (preload.ts)
                │ window.odip.*
┌───────────────▼─────────────────────────────────────────┐
│                   RENDERER (React + Three.js)            │
│  src/App.tsx (HashRouter)                               │
│  ├── /importar   → ImportarPage.tsx                     │
│  ├── /procesar   → ProcesarPage.tsx                     │
│  ├── /revisar    → RevisarPage.tsx                      │
│  │     ├── Viewer3D.tsx      (@react-three/fiber)       │
│  │     └── TablaParametros.tsx (editable, RF-16)        │
│  ├── /exportar   → ExportarPage.tsx                     │
│  └── /historico  → HistoricoPage.tsx                    │
│                                                         │
│  hooks/useIPC.ts   → window.odip (IPC tipado)           │
│  types/index.ts    → contratos TS compartidos           │
└───────────────┬─────────────────────────────────────────┘
                │ HTTP JSON (127.0.0.1:8765)
                │ FastAPI
┌───────────────▼─────────────────────────────────────────┐
│              NÚCLEO PYTHON (FastAPI + pipeline)          │
│  ipc_server.py                                          │
│  ├── POST /importar        → M1                         │
│  ├── POST /procesar-con-ruta → pipeline M1-M8           │
│  ├── GET  /caso/{id}       → M9 (revisión)              │
│  ├── POST /ajuste-manual   → M10 bitácora               │
│  ├── POST /exportar        → M8 + M10                   │
│  └── GET  /historico       → M10                        │
│                                                         │
│  lingualParam/pipeline.py  (orquestador M1→M8)          │
│  ├── M1: m1_importer.py    STL/PLY/OBJ/DCM + SHA-256    │
│  ├── M2: m2_preprocessor.py  SOR + Laplaciano + oclusal │
│  ├── M3: m3_segmenter.py   CNN FDI (stub) + DBSCAN      │
│  ├── M4: m4_geometry.py    PCA + centroide lingual       │
│  ├── M5: m5_parameters.py  T/A/I ±0.1° + cingular       │
│  ├── M6: m6_prescription.py  STb/2D/WIN/personalizada   │
│  ├── M7: m7_bracket.py     C++17 stub → fallback Python  │
│  ├── M8: m8_exporter.py    xlsx/json/csv/sql + SHA-256  │
│  └── M10: m10_audit.py     SQLite + AES-256-GCM         │
└───────────────┬─────────────────────────────────────────┘
                │ SQLite AES-256
                │ pybind11 (M7 C++17)
┌───────────────▼─────────────────────────────────────────┐
│                   PERSISTENCIA                           │
│  ~/.odip_l/bitacora.db    (SQLite cifrada AES-256-GCM)  │
│  ├── Tabla: Paciente      (ID = SHA-256 PII)            │
│  ├── Tabla: Caso          (metadatos escaneo)           │
│  ├── Tabla: Pieza         (21 parámetros por pieza)     │
│  ├── Tabla: Ajuste_manual (historial de correcciones)   │
│  └── Tabla: Bitacora      (payload cifrado por evento)  │
│                                                         │
│  prescriptions/           (JSON valores reales)         │
│  ├── STb.json             Scuzzo-Takemoto 2003          │
│  ├── 2D_Wiechmann.json    Wiechmann 2003                │
│  └── WIN_WildSmile.json   WIN 4th Gen                   │
└─────────────────────────────────────────────────────────┘
```

## Flujo de datos por módulo

```
Archivo 3D
    │
    ▼
[M1] importar_archivo()
    Validación: formato, integridad, unidades mm, SHA-256
    │
    ▼
[M2] preprocesar()
    SOR → Laplaciano → normalización plano oclusal
    │
    ▼
[M3] segmentar()
    CNN FDI (PyTorch) o DBSCAN fallback
    → lista SegmentoFDI por pieza
    │
    ▼
[M4] calcular_geometria_pieza()
    PCA → eje longitudinal
    filtro lingual + zona cingular → centroide lingual
    normales → vector normal lingual
    │
    ▼
[M5] calcular_parametros()
    proyecciones en planos → Torque/Angulación/Inclinación ±0.1°
    distancia cingular
    │
    ▼
[M6] aplicar_prescripcion()
    carga STb/2D/WIN/personalizada
    ΔT = objetivo − actual, ΔA, ΔI
    │
    ▼
[M7] calcular_geometria_bracket()
    C++17 (pybind11) o Python fallback
    grosor base, ángulo slot, radio curvatura
    │
    ▼
[M8] exportar_todo()
    xlsx (21 col) + json + csv + sql + SHA-256
    │
    ▼
[M10] registrar_evento()
    AES-256-GCM → SQLite bitácora cifrada
```

## Decisiones de diseño clave

| Decisión | Razón |
|----------|-------|
| FastAPI sobre stdin/stdout | IPC robusto con tipado JSON; extensible a red |
| AES-256-GCM para bitácora | Autenticado (AEAD); detecta tampering sin clave |
| SHA-256 PII | Anonimización irreversible; requerimiento RGPD/salud |
| DBSCAN como fallback | Independencia de GPU; permite ejecutar sin modelo CNN |
| Open3D | Estándar de facto para geometría 3D en Python; soporte STL/PLY/OBJ |
| pybind11 para M7 | Velocidad C++17 para geometría de millones de brackets; fallback Python garantiza funcionalidad |
| SQLite (no PostgreSQL) | Aplicación de escritorio; sin servidor requerido; fácil cifrado |
