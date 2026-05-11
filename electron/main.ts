/**
 * Proceso principal de Electron — LingualParam-CSM™
 * Lanza el servidor FastAPI Python y gestiona la ventana principal.
 */
import { app, BrowserWindow, ipcMain, dialog, shell } from "electron";
import { spawn, ChildProcess } from "child_process";
import path from "path";
import fs from "fs";

const PUERTO_IPC = 8765;
const URL_IPC = `http://127.0.0.1:${PUERTO_IPC}`;
const ANCHO_VENTANA = 1920;
const ALTO_VENTANA = 1080;

let ventanaPrincipal: BrowserWindow | null = null;
let procesoPython: ChildProcess | null = null;

// ------------------------------------------------------------------
// Lanzar servidor Python
// ------------------------------------------------------------------

function lanzarServidorPython(): void {
  const rutaCore = path.join(app.getAppPath(), "core");
  const rutaScript = path.join(rutaCore, "ipc_server.py");

  const entorno: NodeJS.ProcessEnv = {
    ...process.env,
    PYTHONPATH: rutaCore,
    PYTHONUNBUFFERED: "1",
  };

  const interprete = process.platform === "win32" ? "python" : "python3";

  procesoPython = spawn(interprete, [rutaScript], {
    cwd: rutaCore,
    env: entorno,
    stdio: ["ignore", "pipe", "pipe"],
  });

  procesoPython.stdout?.on("data", (data: Buffer) => {
    console.log(`[Python IPC] ${data.toString().trim()}`);
  });

  procesoPython.stderr?.on("data", (data: Buffer) => {
    console.error(`[Python IPC ERROR] ${data.toString().trim()}`);
  });

  procesoPython.on("exit", (codigo) => {
    console.log(`[Python IPC] Proceso terminado con código ${codigo}`);
    procesoPython = null;
  });

  console.log(`[Electron] Servidor Python iniciado en ${URL_IPC}`);
}

// ------------------------------------------------------------------
// Esperar a que FastAPI esté disponible
// ------------------------------------------------------------------

async function esperarServidorPython(maxIntentos = 30): Promise<void> {
  const http = await import("http");
  for (let intento = 0; intento < maxIntentos; intento++) {
    const disponible = await new Promise<boolean>((resolve) => {
      const req = http.get(`${URL_IPC}/health`, (res) => {
        resolve(res.statusCode === 200);
      });
      req.on("error", () => resolve(false));
      req.setTimeout(500, () => {
        req.destroy();
        resolve(false);
      });
    });
    if (disponible) return;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error("El servidor Python no respondió en el tiempo esperado.");
}

// ------------------------------------------------------------------
// Crear ventana principal
// ------------------------------------------------------------------

async function crearVentana(): Promise<void> {
  ventanaPrincipal = new BrowserWindow({
    width: ANCHO_VENTANA,
    height: ALTO_VENTANA,
    minWidth: 1280,
    minHeight: 720,
    title: "LingualParam-CSM™",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    show: false,
    backgroundColor: "#0f172a",
  });

  ventanaPrincipal.once("ready-to-show", () => {
    ventanaPrincipal?.show();
  });

  if (process.env.NODE_ENV === "development") {
    await ventanaPrincipal.loadURL("http://localhost:5173");
    ventanaPrincipal.webContents.openDevTools();
  } else {
    await ventanaPrincipal.loadFile(
      path.join(__dirname, "../dist/index.html")
    );
  }

  ventanaPrincipal.on("closed", () => {
    ventanaPrincipal = null;
  });
}

// ------------------------------------------------------------------
// Handlers IPC (renderer → main)
// ------------------------------------------------------------------

ipcMain.handle("odip:health", async () => {
  const res = await fetch(`${URL_IPC}/health`);
  return res.json();
});

ipcMain.handle("odip:importar", async (_event, rutaArchivo: string) => {
  const datos = new FormData();
  const blob = new Blob([fs.readFileSync(rutaArchivo)]);
  const nombreArchivo = path.basename(rutaArchivo);
  datos.append("archivo", blob, nombreArchivo);

  const res = await fetch(`${URL_IPC}/importar`, {
    method: "POST",
    body: datos,
  });
  return res.json();
});

ipcMain.handle(
  "odip:procesar",
  async (
    _event,
    rutaArchivo: string,
    idCaso: string,
    tipoPrescripcion: string,
    rutaModeloCNN?: string
  ) => {
    const url = new URL(`${URL_IPC}/procesar-con-ruta`);
    url.searchParams.set("ruta_archivo", rutaArchivo);
    url.searchParams.set("id_caso", idCaso);
    url.searchParams.set("tipo_prescripcion", tipoPrescripcion);
    if (rutaModeloCNN) url.searchParams.set("ruta_modelo_cnn", rutaModeloCNN);

    const res = await fetch(url.toString(), { method: "POST" });
    return res.json();
  }
);

ipcMain.handle("odip:obtenerCaso", async (_event, idCaso: string) => {
  const res = await fetch(`${URL_IPC}/caso/${idCaso}`);
  return res.json();
});

ipcMain.handle("odip:ajusteManual", async (_event, datos: object) => {
  const res = await fetch(`${URL_IPC}/ajuste-manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  return res.json();
});

ipcMain.handle("odip:exportar", async (_event, datos: object) => {
  const res = await fetch(`${URL_IPC}/exportar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  return res.json();
});

ipcMain.handle("odip:historico", async (_event, parametros: object) => {
  const url = new URL(`${URL_IPC}/historico`);
  for (const [k, v] of Object.entries(parametros)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url.toString());
  return res.json();
});

// Diálogo de apertura de archivo
ipcMain.handle("odip:abrirArchivo", async () => {
  const resultado = await dialog.showOpenDialog({
    title: "Seleccionar archivo 3D dental",
    filters: [
      { name: "Archivos 3D dentales", extensions: ["stl", "ply", "obj", "dcm"] },
    ],
    properties: ["openFile"],
  });
  return resultado.canceled ? null : resultado.filePaths[0];
});

// Diálogo de selección de carpeta de exportación
ipcMain.handle("odip:seleccionarCarpeta", async () => {
  const resultado = await dialog.showOpenDialog({
    title: "Seleccionar carpeta de exportación",
    properties: ["openDirectory", "createDirectory"],
  });
  return resultado.canceled ? null : resultado.filePaths[0];
});

// Abrir carpeta en explorador
ipcMain.handle("odip:abrirCarpeta", async (_event, ruta: string) => {
  await shell.openPath(ruta);
});

// ------------------------------------------------------------------
// Ciclo de vida de la app
// ------------------------------------------------------------------

app.whenReady().then(async () => {
  lanzarServidorPython();
  try {
    await esperarServidorPython();
    console.log("[Electron] Servidor Python disponible.");
  } catch (err) {
    console.error("[Electron] Error al conectar con servidor Python:", err);
    dialog.showErrorBox(
      "Error de inicio",
      "No se pudo iniciar el servidor de cálculo Python. Verifique la instalación."
    );
  }
  await crearVentana();

  app.on("activate", async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await crearVentana();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (procesoPython) {
      procesoPython.kill();
    }
    app.quit();
  }
});

app.on("before-quit", () => {
  if (procesoPython) {
    procesoPython.kill("SIGTERM");
  }
});
