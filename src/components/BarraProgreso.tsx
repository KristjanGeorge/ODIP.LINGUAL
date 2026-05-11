/**
 * Componente de barra de progreso con etiqueta de estado.
 */
import React from "react";

interface PropsBarraProgreso {
  progreso: number;       // 0 – 100
  etiqueta?: string;
  variante?: "azul" | "verde" | "rojo" | "amarillo";
  mostrar?: boolean;
}

const COLORES: Record<NonNullable<PropsBarraProgreso["variante"]>, string> = {
  azul: "bg-blue-500",
  verde: "bg-green-500",
  rojo: "bg-red-500",
  amarillo: "bg-yellow-400",
};

export const BarraProgreso: React.FC<PropsBarraProgreso> = ({
  progreso,
  etiqueta,
  variante = "azul",
  mostrar = true,
}) => {
  if (!mostrar) return null;

  const porcentaje = Math.min(100, Math.max(0, Math.round(progreso)));
  const colorBarra = COLORES[variante];

  return (
    <div className="w-full">
      {etiqueta && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-slate-400">{etiqueta}</span>
          <span className="text-sm font-mono text-slate-300">{porcentaje}%</span>
        </div>
      )}
      <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${colorBarra}`}
          style={{ width: `${porcentaje}%` }}
          role="progressbar"
          aria-valuenow={porcentaje}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
};

/** Indicador de carga tipo spinner + texto */
export const CargandoIndicador: React.FC<{ mensaje?: string }> = ({
  mensaje = "Procesando...",
}) => (
  <div className="flex items-center gap-3 text-slate-400">
    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    <span className="text-sm">{mensaje}</span>
  </div>
);
