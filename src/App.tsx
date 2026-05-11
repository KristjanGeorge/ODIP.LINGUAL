/**
 * Router principal de LingualParam-CSM™.
 * 5 rutas: /importar / /procesar / /revisar / /exportar / /historico
 */
import React from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ImportarPage } from "./pages/ImportarPage";
import { ProcesarPage } from "./pages/ProcesarPage";
import { RevisarPage } from "./pages/RevisarPage";
import { ExportarPage } from "./pages/ExportarPage";
import { HistoricoPage } from "./pages/HistoricoPage";

const App: React.FC = () => {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/importar" replace />} />
          <Route path="importar" element={<ImportarPage />} />
          <Route path="procesar" element={<ProcesarPage />} />
          <Route path="revisar" element={<RevisarPage />} />
          <Route path="exportar" element={<ExportarPage />} />
          <Route path="historico" element={<HistoricoPage />} />
          <Route path="*" element={<Navigate to="/importar" replace />} />
        </Route>
      </Routes>
    </HashRouter>
  );
};

export default App;
