/**
 * Visor 3D de malla dental usando @react-three/fiber.
 * Soporta rotación, paneo, zoom y resaltado de pieza seleccionada.
 */
import React, { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame, ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Grid, GizmoHelper, GizmoViewport } from "@react-three/drei";
import * as THREE from "three";
import type { PiezaDatos } from "../types";

// ------------------------------------------------------------------
// Tipos
// ------------------------------------------------------------------

interface PropsMallaTotal {
  /** Vértices planos: [x1, y1, z1, x2, y2, z2, ...] */
  vertices: Float32Array;
  /** Índices de triángulos */
  indices: Uint32Array;
}

interface PropsPieza {
  pieza: PiezaDatos;
  seleccionada: boolean;
  onClick: (fdi: number) => void;
}

interface PropsViewer3D {
  piezas?: PiezaDatos[];
  piezaSeleccionada?: number | null;
  onSeleccionarPieza?: (fdi: number) => void;
  mostrarEjes?: boolean;
}

// ------------------------------------------------------------------
// Componente de malla individual
// ------------------------------------------------------------------

const MallaPieza: React.FC<PropsPieza> = ({ pieza, seleccionada, onClick }) => {
  const meshRef = useRef<THREE.Mesh>(null);

  // Construir geometría desde centroide + radio aproximado
  const geometria = useMemo(() => {
    const geo = new THREE.SphereGeometry(3, 16, 12);
    geo.translate(
      pieza.centroide_lingual[0],
      pieza.centroide_lingual[1],
      pieza.centroide_lingual[2]
    );
    return geo;
  }, [pieza.centroide_lingual]);

  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: seleccionada ? "#3b82f6" : "#94a3b8",
        roughness: 0.6,
        metalness: 0.1,
        transparent: true,
        opacity: seleccionada ? 1.0 : 0.75,
      }),
    [seleccionada]
  );

  const manejarClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onClick(pieza.fdi);
  };

  return (
    <mesh
      ref={meshRef}
      geometry={geometria}
      material={material}
      onClick={manejarClick}
      castShadow
    />
  );
};

// ------------------------------------------------------------------
// Etiqueta FDI flotante
// ------------------------------------------------------------------

const EtiquetaFDI: React.FC<{ pieza: PiezaDatos }> = ({ pieza }) => {
  const posicion: [number, number, number] = [
    pieza.centroide_lingual[0],
    pieza.centroide_lingual[1] + 4,
    pieza.centroide_lingual[2],
  ];

  return (
    <mesh position={posicion}>
      <planeGeometry args={[3, 1.2]} />
      <meshBasicMaterial color="#1e293b" transparent opacity={0.8} />
    </mesh>
  );
};

// ------------------------------------------------------------------
// Escena 3D
// ------------------------------------------------------------------

const Escena: React.FC<{
  piezas: PiezaDatos[];
  piezaSeleccionada: number | null;
  onSeleccionarPieza: (fdi: number) => void;
  mostrarEjes: boolean;
}> = ({ piezas, piezaSeleccionada, onSeleccionarPieza, mostrarEjes }) => {
  return (
    <>
      {/* Iluminación */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 20, 10]} intensity={1.2} castShadow />
      <directionalLight position={[-10, -10, -5]} intensity={0.3} />
      <pointLight position={[0, 10, 0]} intensity={0.8} />

      {/* Piezas */}
      {piezas.map((pieza) => (
        <MallaPieza
          key={pieza.fdi}
          pieza={pieza}
          seleccionada={piezaSeleccionada === pieza.fdi}
          onClick={onSeleccionarPieza}
        />
      ))}

      {/* Etiquetas FDI */}
      {piezas.map((pieza) => (
        <EtiquetaFDI key={`label-${pieza.fdi}`} pieza={pieza} />
      ))}

      {/* Grid del plano oclusal */}
      {mostrarEjes && (
        <Grid
          args={[80, 80]}
          cellSize={5}
          cellThickness={0.5}
          cellColor="#334155"
          sectionSize={20}
          sectionThickness={1}
          sectionColor="#475569"
          fadeDistance={100}
          fadeStrength={1}
          followCamera={false}
        />
      )}

      {/* Controles de órbita */}
      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={10}
        maxDistance={200}
        panSpeed={0.8}
        zoomSpeed={1.2}
        rotateSpeed={0.6}
      />

      {/* Ayudante de orientación */}
      <GizmoHelper alignment="bottom-right" margin={[80, 80]}>
        <GizmoViewport
          axisColors={["#ef4444", "#22c55e", "#3b82f6"]}
          labelColor="white"
        />
      </GizmoHelper>
    </>
  );
};

// ------------------------------------------------------------------
// Componente principal
// ------------------------------------------------------------------

export const Viewer3D: React.FC<PropsViewer3D> = ({
  piezas = [],
  piezaSeleccionada = null,
  onSeleccionarPieza = () => {},
  mostrarEjes = true,
}) => {
  return (
    <div className="w-full h-full bg-slate-900 rounded-lg overflow-hidden border border-slate-700">
      {piezas.length === 0 ? (
        <div className="flex items-center justify-center h-full text-slate-500">
          <div className="text-center">
            <div className="text-4xl mb-2">🦷</div>
            <p className="text-sm">Sin datos 3D. Importe un archivo para visualizar.</p>
          </div>
        </div>
      ) : (
        <Canvas
          camera={{ position: [0, -60, 40], fov: 45, near: 0.1, far: 1000 }}
          shadows
          dpr={[1, 2]}
          gl={{ antialias: true }}
        >
          <Suspense fallback={null}>
            <Escena
              piezas={piezas}
              piezaSeleccionada={piezaSeleccionada}
              onSeleccionarPieza={onSeleccionarPieza}
              mostrarEjes={mostrarEjes}
            />
          </Suspense>
        </Canvas>
      )}
    </div>
  );
};
