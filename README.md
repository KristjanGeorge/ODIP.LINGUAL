# LingualParam-CSM™ — ODIP.LINGUAL

**Sistema de Parametrización Tridimensional de Modelos Dentales para Ortodoncia Lingual**

> Cliente: **Clínica Lingual — Dr. Christian San Martín**  
> Ingeniero Jefe: **Kristjan Araoz & Asociados**  
> Versión: `0.1.0` · Frutillar, Chile · Mayo 2026  
> Patente de Invención: **ODIP-L™** — INAPI, presentada el 01-04-2026

---

## Descripción

LingualParam-CSM™ es el software de la realización informática de los **Módulos B, C y E** del Sistema **ODIP-L™** patentado. A partir de un escaneo intraoral (`.STL`/`.PLY`/`.OBJ`) o CBCT (`.DCM`), el sistema:

1. **Segmenta** cada pieza dental por nomenclatura FDI mediante red neuronal convolucional 3D.
2. **Calcula** los parámetros de **Torque (T)**, **Angulación (A)** e **Inclinación (I)** con precisión ±0,1°.
3. **Compara** los valores con la prescripción lingual seleccionada (STb, 2D Wiechmann, WIN o personalizada).
4. **Calcula** la geometría individualizada de la base del bracket lingual.
5. **Exporta** el dataset firmado criptográficamente (SHA-256) para el laboratorio dental o sistema de doblado robótico de arcos.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| GUI | Electron 30 + React 18 + TypeScript 5.4 |
| Visor 3D | Three.js + @react-three/fiber |
| Núcleo cálculo | Python 3.11 (mypy strict) |
| Geometría bracket (M7) | C++17 via pybind11 |
| IPC | FastAPI + uvicorn (JSON sobre HTTP local) |
| Persistencia | SQLite 3 cifrada AES-256-GCM |
| Estilo | Tailwind CSS 3 |

---

## Arquitectura de módulos (M1–M10)

```
M1  Importación y validación (.STL/.PLY/.OBJ/.DCM)
M2  Pre-procesamiento de malla (SOR, Laplaciano, normalización oclusal)
M3  Segmentación CNN FDI (PyTorch, ≥98 % accuracy)
M4  Geometría 3D (eje PCA, centroide lingual, vector normal)
M5  Parámetros T/A/I ±0.1°, distancia cingular
M6  Gestión de prescripciones (STb / 2D / WIN / personalizada)
M7  Geometría individualizada del bracket (C++17/pybind11)
M8  Exportación firmada (.xlsx · .json · .csv · .sql) + SHA-256
M9  GUI de revisión clínica (React/Three.js)
M10 Bitácora cifrada, anonimización PII, histórico
```

---

## Requisitos del sistema

| Componente | Mínimo |
|-----------|--------|
| SO | Windows 10/11 (64 bits) · Ubuntu 22.04 LTS |
| RAM | 16 GB |
| GPU | NVIDIA con CUDA 12 (requerida para inferencia CNN) |
| Almacenamiento | 10 GB libres |
| Python | 3.11+ |
| Node.js | 20+ |

---

## Instalación (desarrollo)

### 1. Clonar el repositorio

```bash
git clone https://github.com/KristjanGeorge/ODIP.LINGUAL.git ODIP_L
cd ODIP_L
```

### 2. Backend Python

```bash
cd core
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. Frontend Electron/React

```bash
cd ..   # raíz del proyecto
npm install
```

### 4. Ejecutar en modo desarrollo

```bash
# Terminal 1 — servidor Python
cd core && python ipc_server.py

# Terminal 2 — Electron + Vite
npm run dev
```

---

## Scripts disponibles

```bash
npm run dev        # Desarrollo: Vite + Electron concurrentes
npm run build      # Build producción: Vite + tsc Electron
npm run package    # Empaqueta instalador (NSIS/AppImage)
npm run lint       # ESLint TypeScript
npm run typecheck  # tsc --noEmit
```

```bash
# Python (desde core/)
pytest                    # Suite de pruebas (≥80 % cobertura)
mypy lingualParam         # Verificación de tipos estricta
ruff check lingualParam   # Lint
```

---

## Prescripciones incluidas

| Archivo | Prescripción |
|---------|-------------|
| `prescriptions/STb.json` | Scuzzo-Takemoto (Quintessenz, 2003) |
| `prescriptions/2D_Wiechmann.json` | Dirk Wiechmann 2D (Eur J Orthod, 2002) |
| `prescriptions/WIN_WildSmile.json` | Wild Smile WIN |

---

## Conformidad regulatoria

- **IEEE Std 830-1998** — SRS completo en `docs/`
- **IEC 62304:2015** — Clase de seguridad B
- **ISO 13485:2016** — Ciclo de vida de dispositivos médicos
- **Ley 19.628** (Chile) — Protección de datos personales
- **Ley 20.584** (Chile) — Derechos del paciente

---

## Propiedad intelectual

© 2026 **Kristjan Araoz & Asociados** — Todos los derechos reservados.  
El software es la realización de la solicitud de patente de invención **ODIP-L™** presentada ante INAPI el 01-04-2026.  
El registro de derechos de autor (DDI) corresponde al **Dr. Christian San Martín — Clínica Lingual**.  
Cualquier distribución a terceros distintos de Clínica Lingual requiere acuerdo escrito con el titular.
