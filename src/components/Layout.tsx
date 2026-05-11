/**
 * Layout principal con navegación por pestañas.
 * 5 pestañas: Importar / Procesar / Revisar / Exportar / Histórico
 */
import React from "react";
import { NavLink, Outlet } from "react-router-dom";

interface Tab {
  ruta: string;
  etiqueta: string;
  icono: string;
}

const TABS: Tab[] = [
  { ruta: "/importar", etiqueta: "Importar", icono: "📂" },
  { ruta: "/procesar", etiqueta: "Procesar", icono: "⚙️" },
  { ruta: "/revisar", etiqueta: "Revisar", icono: "🔍" },
  { ruta: "/exportar", etiqueta: "Exportar", icono: "📤" },
  { ruta: "/historico", etiqueta: "Histórico", icono: "📋" },
];

export const Layout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100">
      {/* Barra superior */}
      <header className="flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-700 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-blue-400 font-mono text-sm font-bold tracking-widest uppercase">
            LingualParam-CSM™
          </span>
          <span className="text-slate-500 text-xs">ODIP_L v0.1.0</span>
        </div>
        <span className="text-slate-500 text-xs">
          Sistema de Individualización de Parámetros Linguales
        </span>
      </header>

      {/* Navegación pestañas */}
      <nav className="flex border-b border-slate-700 bg-slate-900 shrink-0">
        {TABS.map((tab) => (
          <NavLink
            key={tab.ruta}
            to={tab.ruta}
            className={({ isActive }) =>
              [
                "flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors",
                "border-b-2 hover:text-blue-300",
                isActive
                  ? "border-blue-500 text-blue-400 bg-slate-800"
                  : "border-transparent text-slate-400 hover:border-slate-500",
              ].join(" ")
            }
          >
            <span role="img" aria-hidden>{tab.icono}</span>
            {tab.etiqueta}
          </NavLink>
        ))}
      </nav>

      {/* Contenido principal */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>

      {/* Pie de página */}
      <footer className="px-6 py-2 bg-slate-900 border-t border-slate-700 text-slate-600 text-xs shrink-0">
        LingualParam-CSM™ — Software de uso clínico exclusivo para profesionales habilitados.
        No constituye diagnóstico médico.
      </footer>
    </div>
  );
};
