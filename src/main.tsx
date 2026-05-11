/**
 * Punto de entrada del renderer React.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

const contenedor = document.getElementById("root");
if (!contenedor) {
  throw new Error("No se encontró el elemento #root en el DOM.");
}

ReactDOM.createRoot(contenedor).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
