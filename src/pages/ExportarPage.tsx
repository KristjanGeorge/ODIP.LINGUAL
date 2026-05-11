/**
 * Página Exportar — M8.
 * Confirmación explícita y exportación firmada en múltiples formatos.
 * RF-17..RF-21.
 */
import React, { useState, useCallback } from "react";
import { useIPC } from "../hooks/useIPC";
import { CargandoIndicador } from "../components/BarraProgreso";
import type { ResultadoExportacion } from "../types";

interface DatosPaciente {
  nombre: string;
  fechaNacimiento: string;
  rutUId: string;
}

const FORMATOS_EXPORTACION = [
  { id: "xlsx", etiqueta: ".xlsx", descripcion: "Excel — 21 columnas por patente" },
  { id: "json", etiqueta: ".json", descripcion: "JSON — para CAD/CAM" },
  { id: "csv", etiqueta: ".csv", descripcion: "CSV — compatible con sistemas externos" },
  { id: "sql", etiqueta: ".sql", descripcion: "SQL INSERT — para bases de datos" },
];

export const ExportarPage: React.FC = () => {
  const { seleccionarCarpeta, exportar, abrirCarpeta, estadoExportar } = useIPC();
  const [paciente, setPaciente] = useState<DatosPaciente>({
    nombre: "",
    fechaNacimiento: "",
    rutUId: "",
  });
  const [carpetaDestino, setCarpetaDestino] = useState<string | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const [resultado, setResultado] = useState<ResultadoExportacion | null>(null);

  const idCaso = sessionStorage.getItem("odip_id_caso") ?? "";

  const manejarSeleccionarCarpeta = useCallback(async () => {
    const ruta = await seleccionarCarpeta();
    if (ruta) setCarpetaDestino(ruta);
  }, [seleccionarCarpeta]);

  const puedeExportar =
    idCaso &&
    carpetaDestino &&
    paciente.nombre.trim() &&
    paciente.fechaNacimiento &&
    paciente.rutUId.trim() &&
    confirmado;

  const manejarExportar = useCallback(async () => {
    if (!puedeExportar) return;
    try {
      const res = await exportar({
        id_caso: idCaso,
        nombre_paciente: paciente.nombre,
        fecha_nacimiento: paciente.fechaNacimiento,
        rut_u_id: paciente.rutUId,
        directorio_destino: carpetaDestino!,
      });
      setResultado(res);
    } catch {
      // error capturado en estadoExportar.error
    }
  }, [puedeExportar, idCaso, paciente, carpetaDestino, exportar]);

  if (!idCaso) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <p className="text-slate-400">No hay caso procesado. Complete los pasos anteriores.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">Exportar resultados</h1>
        <p className="text-slate-400 text-sm">
          Los datos del paciente serán anonimizados (SHA-256) antes de exportar.
          El dataset será firmado con SHA-256.
        </p>
      </div>

      {/* Datos del paciente (solo para anonimización) */}
      <div className="bg-slate-800 border border-slate-600 rounded-lg p-4 space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Datos del paciente (para anonimización)
        </h2>
        <p className="text-slate-500 text-xs">
          Estos datos NO se almacenan. Solo se usan para generar el ID anónimo SHA-256.
        </p>
        <div className="space-y-2">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Nombre completo</label>
            <input
              type="text"
              value={paciente.nombre}
              onChange={(e) => setPaciente((p) => ({ ...p, nombre: e.target.value }))}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
              placeholder="Nombre Apellido"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Fecha de nacimiento</label>
            <input
              type="date"
              value={paciente.fechaNacimiento}
              onChange={(e) => setPaciente((p) => ({ ...p, fechaNacimiento: e.target.value }))}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">RUT u otro identificador</label>
            <input
              type="text"
              value={paciente.rutUId}
              onChange={(e) => setPaciente((p) => ({ ...p, rutUId: e.target.value }))}
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm"
              placeholder="12.345.678-9"
            />
          </div>
        </div>
      </div>

      {/* Formatos */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Formatos de exportación
        </h2>
        <div className="space-y-2">
          {FORMATOS_EXPORTACION.map((fmt) => (
            <div key={fmt.id} className="flex items-center gap-3">
              <span className="text-green-400 text-sm">✓</span>
              <span className="font-mono text-blue-300 text-sm w-12">{fmt.etiqueta}</span>
              <span className="text-slate-400 text-xs">{fmt.descripcion}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Carpeta destino */}
      <div className="space-y-2">
        <label className="block text-sm text-slate-400 font-medium">
          Carpeta de exportación
        </label>
        <div className="flex gap-2">
          <div className="flex-1 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm text-slate-400 truncate">
            {carpetaDestino ?? "Sin seleccionar"}
          </div>
          <button
            onClick={manejarSeleccionarCarpeta}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-slate-200 rounded text-sm"
          >
            Seleccionar
          </button>
        </div>
      </div>

      {/* Confirmación explícita RF-17 */}
      <label className="flex items-start gap-3 p-4 bg-amber-950 border border-amber-700 rounded-lg cursor-pointer">
        <input
          type="checkbox"
          checked={confirmado}
          onChange={(e) => setConfirmado(e.target.checked)}
          className="mt-0.5"
        />
        <div>
          <p className="text-amber-200 font-medium text-sm">Confirmación explícita de exportación</p>
          <p className="text-amber-400 text-xs mt-1">
            Confirmo que he revisado todos los parámetros, que el caso {idCaso} está aprobado
            clínicamente, y que autorizo la exportación del dataset firmado.
          </p>
        </div>
      </label>

      {/* Botón exportar */}
      {!estadoExportar.cargando && !resultado && (
        <button
          onClick={manejarExportar}
          disabled={!puedeExportar}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 disabled:text-slate-400 text-white rounded-lg font-semibold transition-colors"
        >
          Exportar y firmar dataset
        </button>
      )}

      {estadoExportar.cargando && (
        <div className="bg-slate-800 rounded-lg p-4">
          <CargandoIndicador mensaje="Generando archivos y calculando firmas SHA-256..." />
        </div>
      )}

      {estadoExportar.error && (
        <div className="bg-red-950 border border-red-700 rounded-lg p-4">
          <p className="text-red-300">{estadoExportar.error}</p>
        </div>
      )}

      {resultado?.ok && (
        <div className="bg-green-950 border border-green-700 rounded-lg p-4 space-y-3">
          <p className="text-green-300 font-semibold">Exportación completada y firmada</p>
          <div className="space-y-1">
            <p className="text-xs text-slate-400">
              ID paciente anonimizado:
              <span className="font-mono text-slate-300 ml-2 text-xs break-all">
                {resultado.id_paciente_anonimizado}
              </span>
            </p>
            <div className="space-y-1 mt-2">
              {Object.entries(resultado.hashes).map(([fmt, sha]) => (
                <div key={fmt} className="flex gap-2 text-xs">
                  <span className="text-blue-300 font-mono w-16 shrink-0">{fmt}:</span>
                  <span className="text-slate-400 font-mono break-all">{sha}</span>
                </div>
              ))}
            </div>
          </div>
          {carpetaDestino && (
            <button
              onClick={() => abrirCarpeta(carpetaDestino)}
              className="text-blue-400 hover:text-blue-300 text-sm underline"
            >
              Abrir carpeta de exportación →
            </button>
          )}
        </div>
      )}
    </div>
  );
};
