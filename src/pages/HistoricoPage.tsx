/**
 * Página Histórico — M10.
 * Consulta de la bitácora cifrada con filtros por caso, tipo, fecha.
 * RF-25.
 */
import React, { useState, useCallback, useEffect } from "react";
import { useIPC } from "../hooks/useIPC";
import { CargandoIndicador } from "../components/BarraProgreso";
import type { EventoBitacora, ResultadoHistorico } from "../types";

const TIPOS_EVENTO = [
  { valor: "", etiqueta: "Todos" },
  { valor: "importacion", etiqueta: "Importación" },
  { valor: "procesamiento", etiqueta: "Procesamiento" },
  { valor: "ajuste_manual", etiqueta: "Ajuste manual" },
  { valor: "exportacion", etiqueta: "Exportación" },
  { valor: "error", etiqueta: "Error" },
];

const BadgeTipo: React.FC<{ tipo: string }> = ({ tipo }) => {
  const colores: Record<string, string> = {
    importacion: "bg-blue-900 text-blue-300",
    procesamiento: "bg-purple-900 text-purple-300",
    ajuste_manual: "bg-yellow-900 text-yellow-300",
    exportacion: "bg-green-900 text-green-300",
    error: "bg-red-900 text-red-300",
    consulta: "bg-slate-700 text-slate-300",
  };
  const color = colores[tipo] ?? "bg-slate-700 text-slate-400";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {tipo}
    </span>
  );
};

const FilaEvento: React.FC<{ evento: EventoBitacora }> = ({ evento }) => (
  <tr className="border-b border-slate-700 hover:bg-slate-800 transition-colors">
    <td className="px-3 py-2 font-mono text-xs text-slate-500">{evento.id_evento}</td>
    <td className="px-3 py-2">
      <BadgeTipo tipo={evento.tipo} />
    </td>
    <td className="px-3 py-2 text-sm text-slate-300 font-mono">
      {evento.id_caso ?? "—"}
    </td>
    <td className="px-3 py-2 text-sm text-slate-400">{evento.autor}</td>
    <td className="px-3 py-2 text-xs text-slate-500 whitespace-nowrap">
      {new Date(evento.marca_temporal).toLocaleString("es-CL")}
    </td>
    <td className="px-3 py-2 text-xs text-slate-400 max-w-xs truncate">
      {evento.descripcion ?? ""}
    </td>
    <td className="px-3 py-2 text-xs font-mono text-slate-600 max-w-24 truncate">
      {evento.hash.slice(0, 12)}…
    </td>
  </tr>
);

export const HistoricoPage: React.FC = () => {
  const { historico } = useIPC();
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState<ResultadoHistorico | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [filtros, setFiltros] = useState({
    id_caso: "",
    tipo: "",
    fecha_desde: "",
    fecha_hasta: "",
    limite: 100,
  });

  const buscar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const res = await historico({
        id_caso: filtros.id_caso || undefined,
        tipo: filtros.tipo || undefined,
        fecha_desde: filtros.fecha_desde || undefined,
        fecha_hasta: filtros.fecha_hasta || undefined,
        limite: filtros.limite,
      });
      setResultado(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al consultar bitácora.");
    } finally {
      setCargando(false);
    }
  }, [historico, filtros]);

  // Cargar automáticamente al montar
  useEffect(() => {
    buscar();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">Histórico de bitácora</h1>
        <p className="text-slate-400 text-sm">
          Registro cifrado de todas las acciones del sistema. Búsqueda por ID de caso, tipo o fecha.
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">ID Caso</label>
          <input
            type="text"
            value={filtros.id_caso}
            onChange={(e) => setFiltros((f) => ({ ...f, id_caso: e.target.value }))}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm font-mono"
            placeholder="caso-xxx"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Tipo de evento</label>
          <select
            value={filtros.tipo}
            onChange={(e) => setFiltros((f) => ({ ...f, tipo: e.target.value }))}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm"
          >
            {TIPOS_EVENTO.map((t) => (
              <option key={t.valor} value={t.valor}>{t.etiqueta}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Desde</label>
          <input
            type="date"
            value={filtros.fecha_desde}
            onChange={(e) => setFiltros((f) => ({ ...f, fecha_desde: e.target.value }))}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Hasta</label>
          <input
            type="date"
            value={filtros.fecha_hasta}
            onChange={(e) => setFiltros((f) => ({ ...f, fecha_hasta: e.target.value }))}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm"
          />
        </div>
        <div className="md:col-span-4 flex justify-end">
          <button
            onClick={buscar}
            disabled={cargando}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-600 text-white rounded text-sm font-medium transition-colors"
          >
            Buscar
          </button>
        </div>
      </div>

      {cargando && (
        <div className="py-4">
          <CargandoIndicador mensaje="Consultando bitácora cifrada..." />
        </div>
      )}

      {error && (
        <div className="bg-red-950 border border-red-700 rounded-lg p-3">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Tabla de resultados */}
      {resultado && (
        <div className="flex-1 overflow-auto">
          <div className="mb-2 text-xs text-slate-500">
            {resultado.total} evento{resultado.total !== 1 ? "s" : ""} encontrado{resultado.total !== 1 ? "s" : ""}
          </div>
          {resultado.eventos.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <div className="text-3xl mb-2">📋</div>
              <p>No se encontraron eventos con los filtros seleccionados.</p>
            </div>
          ) : (
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-slate-800 border-b border-slate-600">
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">ID</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Tipo</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Caso</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Autor</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Fecha</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Descripción</th>
                  <th className="px-3 py-2 text-left text-xs text-slate-400 font-semibold uppercase">Hash</th>
                </tr>
              </thead>
              <tbody>
                {resultado.eventos.map((ev) => (
                  <FilaEvento key={ev.id_evento} evento={ev} />
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};
