"""
Tests para M1: Importación y validación de archivos 3D.
TDD London School — pruebas de comportamiento.
"""
from __future__ import annotations

import os
import struct
import tempfile

import numpy as np
import pytest

from lingualParam.m1_importer import (
    ErrorImportacion,
    _calcular_hash_archivo,
    _detectar_formato,
    _validar_geometria,
    importar_archivo,
)
from lingualParam.types import FormatoArchivo


# ------------------------------------------------------------------
# Helpers para generar archivos de prueba mínimos
# ------------------------------------------------------------------

def _crear_stl_binario(n_triangulos: int = 200) -> bytes:
    """Genera un archivo STL binario sintético con n_triangulos."""
    cabecera = b"\x00" * 80
    header = cabecera + struct.pack("<I", n_triangulos)
    triangulos = b""
    for i in range(n_triangulos):
        # Normal + 3 vértices + atributo
        normal = struct.pack("<fff", 0.0, 0.0, 1.0)
        v1 = struct.pack("<fff", float(i), 0.0, 0.0)
        v2 = struct.pack("<fff", float(i) + 1.0, 0.0, 0.0)
        v3 = struct.pack("<fff", float(i), 1.0, 0.0)
        triangulos += normal + v1 + v2 + v3 + b"\x00\x00"
    return header + triangulos


def _archivo_stl_temporal(n_triangulos: int = 200) -> str:
    """Crea un archivo STL temporal y retorna su ruta."""
    contenido = _crear_stl_binario(n_triangulos)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".stl")
    tmp.write(contenido)
    tmp.close()
    return tmp.name


# ------------------------------------------------------------------
# Tests _detectar_formato
# ------------------------------------------------------------------

class TestDetectarFormato:
    def test_stl_retorna_enum_stl(self) -> None:
        assert _detectar_formato("/ruta/modelo.stl") == FormatoArchivo.STL

    def test_ply_retorna_enum_ply(self) -> None:
        assert _detectar_formato("/ruta/modelo.PLY") == FormatoArchivo.PLY

    def test_obj_retorna_enum_obj(self) -> None:
        assert _detectar_formato("/ruta/modelo.obj") == FormatoArchivo.OBJ

    def test_dcm_retorna_enum_dcm(self) -> None:
        assert _detectar_formato("/ruta/scan.dcm") == FormatoArchivo.DCM

    def test_formato_no_soportado_lanza_excepcion(self) -> None:
        with pytest.raises(ErrorImportacion, match="no soportado"):
            _detectar_formato("/ruta/modelo.fbx")


# ------------------------------------------------------------------
# Tests _calcular_hash_archivo
# ------------------------------------------------------------------

class TestCalcularHash:
    def test_hash_es_64_chars_hex(self, tmp_path) -> None:
        ruta = tmp_path / "test.bin"
        ruta.write_bytes(b"contenido de prueba")
        h = _calcular_hash_archivo(str(ruta))
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_hash_deterministico(self, tmp_path) -> None:
        ruta = tmp_path / "test.bin"
        ruta.write_bytes(b"mismo contenido")
        assert _calcular_hash_archivo(str(ruta)) == _calcular_hash_archivo(str(ruta))

    def test_hashes_diferentes_para_diferentes_contenidos(self, tmp_path) -> None:
        r1 = tmp_path / "a.bin"
        r2 = tmp_path / "b.bin"
        r1.write_bytes(b"contenido A")
        r2.write_bytes(b"contenido B")
        assert _calcular_hash_archivo(str(r1)) != _calcular_hash_archivo(str(r2))


# ------------------------------------------------------------------
# Tests _validar_geometria
# ------------------------------------------------------------------

class TestValidarGeometria:
    def test_malla_valida_no_lanza(self) -> None:
        v = np.random.uniform(0, 50, (2000, 3))
        c = np.zeros((600, 3), dtype=np.int32)
        _validar_geometria(v, c, "test.stl")  # no debe lanzar

    def test_pocos_vertices_lanza(self) -> None:
        v = np.zeros((100, 3))
        c = np.zeros((600, 3), dtype=np.int32)
        with pytest.raises(ErrorImportacion, match="vértices"):
            _validar_geometria(v, c, "test.stl")

    def test_pocas_caras_lanza(self) -> None:
        v = np.random.uniform(0, 30, (2000, 3))
        c = np.zeros((10, 3), dtype=np.int32)
        with pytest.raises(ErrorImportacion, match="caras"):
            _validar_geometria(v, c, "test.stl")

    def test_coordenadas_fuera_de_rango_mm_lanza(self) -> None:
        v = np.full((2000, 3), 1000.0)  # 1000 mm — fuera de rango
        c = np.zeros((600, 3), dtype=np.int32)
        with pytest.raises(ErrorImportacion, match="mm"):
            _validar_geometria(v, c, "test.stl")

    def test_nan_en_vertices_lanza(self) -> None:
        v = np.random.uniform(0, 30, (2000, 3))
        v[0, 0] = float("nan")
        c = np.zeros((600, 3), dtype=np.int32)
        with pytest.raises(ErrorImportacion, match="NaN"):
            _validar_geometria(v, c, "test.stl")


# ------------------------------------------------------------------
# Tests importar_archivo (integración con archivo real)
# ------------------------------------------------------------------

class TestImportarArchivo:
    def test_archivo_inexistente_lanza(self) -> None:
        with pytest.raises(ErrorImportacion, match="no encontrado"):
            importar_archivo("/ruta/inexistente.stl")

    def test_importar_stl_valido_retorna_malla(self) -> None:
        # Crear STL con suficientes triángulos para pasar validación
        ruta = _archivo_stl_temporal(n_triangulos=600)
        try:
            malla = importar_archivo(ruta)
            assert malla.formato == "stl"
            assert malla.unidad_mm is True
            assert len(malla.hash_origen) == 64
            assert malla.vertices.shape[1] == 3
        finally:
            os.unlink(ruta)

    def test_malla_importada_tiene_metadata(self) -> None:
        ruta = _archivo_stl_temporal(n_triangulos=600)
        try:
            malla = importar_archivo(ruta)
            assert "n_vertices" in malla.metadata
            assert "bbox_mm" in malla.metadata
        finally:
            os.unlink(ruta)
