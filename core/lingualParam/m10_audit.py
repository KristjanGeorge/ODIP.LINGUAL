"""
M10: Bitácora cifrada, anonimización PII, histórico.
Usa SQLite + AES-256 (biblioteca cryptography). RF-22, RF-23, RF-25.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Ruta por defecto de la base de datos cifrada
_RUTA_DB_DEFAULT = Path.home() / ".odip_l" / "bitacora.db"


class GestorBitacora:
    """
    Gestiona la bitácora cifrada de acciones del sistema.
    El payload se cifra con AES-256-GCM antes de almacenarse.
    """

    def __init__(
        self,
        ruta_db: Union[str, Path] = _RUTA_DB_DEFAULT,
        clave_aes: Optional[bytes] = None,
    ) -> None:
        self._ruta_db = Path(ruta_db)
        self._ruta_db.parent.mkdir(parents=True, exist_ok=True)
        # Clave AES-256 (32 bytes). En producción: cargar desde Vault/env.
        self._clave = clave_aes or self._obtener_o_crear_clave()
        self._aesgcm = AESGCM(self._clave)
        self._inicializar_db()

    # ------------------------------------------------------------------
    # Gestión de clave
    # ------------------------------------------------------------------

    def _obtener_o_crear_clave(self) -> bytes:
        """Obtiene la clave AES desde variable de entorno o crea una nueva."""
        clave_env = os.environ.get("ODIP_L_AES_KEY")
        if clave_env:
            clave = bytes.fromhex(clave_env)
            if len(clave) != 32:
                raise ValueError("ODIP_L_AES_KEY debe ser 64 hex chars (32 bytes).")
            return clave
        # Desarrollo: generar clave aleatoria y advertir
        clave = AESGCM.generate_key(bit_length=256)
        print(
            "[ADVERTENCIA] Clave AES generada aleatoriamente. "
            "Defina ODIP_L_AES_KEY para producción."
        )
        return clave

    # ------------------------------------------------------------------
    # Inicialización DB
    # ------------------------------------------------------------------

    def _inicializar_db(self) -> None:
        """Crea las tablas si no existen."""
        with sqlite3.connect(self._ruta_db) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS bitacora (
                    id_evento    INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo         TEXT    NOT NULL,
                    autor        TEXT    NOT NULL,
                    id_caso      TEXT,
                    marca_temporal TEXT  NOT NULL,
                    hash         TEXT    NOT NULL,
                    payload_cifrado BLOB NOT NULL
                )
            """)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_bitacora_caso
                ON bitacora (id_caso)
            """)
            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_bitacora_tipo
                ON bitacora (tipo)
            """)

    # ------------------------------------------------------------------
    # Cifrado / Descifrado
    # ------------------------------------------------------------------

    def _cifrar(self, payload: dict) -> bytes:
        """Cifra el payload con AES-256-GCM. Retorna nonce || ciphertext."""
        datos = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        nonce = os.urandom(12)  # 96 bits recomendado para GCM
        cifrado = self._aesgcm.encrypt(nonce, datos, None)
        return nonce + cifrado

    def _descifrar(self, blob: bytes) -> dict:
        """Descifra un blob nonce || ciphertext."""
        nonce, cifrado = blob[:12], blob[12:]
        datos = self._aesgcm.decrypt(nonce, cifrado, None)
        return json.loads(datos.decode("utf-8"))

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def registrar_evento(
        self,
        tipo: str,
        autor: str,
        descripcion: str,
        id_caso: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> int:
        """
        RF-22: Registra un evento en la bitácora cifrada.

        Returns:
            id_evento asignado por SQLite.
        """
        payload_completo = {
            "descripcion": descripcion,
            **(payload or {}),
        }
        blob_cifrado = self._cifrar(payload_completo)
        hash_evento = hashlib.sha256(blob_cifrado).hexdigest()
        marca = datetime.utcnow().isoformat()

        with sqlite3.connect(self._ruta_db) as con:
            cursor = con.execute(
                """
                INSERT INTO bitacora (tipo, autor, id_caso, marca_temporal, hash, payload_cifrado)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tipo, autor, id_caso, marca, hash_evento, blob_cifrado),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def leer_evento(self, id_evento: int) -> dict:
        """Lee y descifra un evento de la bitácora."""
        with sqlite3.connect(self._ruta_db) as con:
            row = con.execute(
                "SELECT tipo, autor, id_caso, marca_temporal, hash, payload_cifrado "
                "FROM bitacora WHERE id_evento = ?",
                (id_evento,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Evento {id_evento} no encontrado.")
        tipo, autor, id_caso, marca, hash_db, blob = row
        payload = self._descifrar(blob)
        return {
            "id_evento": id_evento,
            "tipo": tipo,
            "autor": autor,
            "id_caso": id_caso,
            "marca_temporal": marca,
            "hash": hash_db,
            **payload,
        }

    def consultar_historico(
        self,
        id_caso: Optional[str] = None,
        tipo: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        limite: int = 100,
    ) -> list[dict]:
        """
        RF-25: Consulta el histórico de eventos con filtros opcionales.
        Los payloads se descifran en tiempo de consulta.
        """
        condiciones = []
        parametros: list = []

        if id_caso:
            condiciones.append("id_caso = ?")
            parametros.append(id_caso)
        if tipo:
            condiciones.append("tipo = ?")
            parametros.append(tipo)
        if fecha_desde:
            condiciones.append("marca_temporal >= ?")
            parametros.append(fecha_desde)
        if fecha_hasta:
            condiciones.append("marca_temporal <= ?")
            parametros.append(fecha_hasta)

        where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
        parametros.append(limite)

        with sqlite3.connect(self._ruta_db) as con:
            filas = con.execute(
                f"SELECT id_evento, tipo, autor, id_caso, marca_temporal, hash, payload_cifrado "
                f"FROM bitacora {where} ORDER BY marca_temporal DESC LIMIT ?",
                parametros,
            ).fetchall()

        resultados = []
        for fila in filas:
            id_ev, tipo_f, autor_f, id_caso_f, marca_f, hash_f, blob = fila
            try:
                payload = self._descifrar(blob)
            except Exception:
                payload = {"error": "No se pudo descifrar el payload."}
            resultados.append({
                "id_evento": id_ev,
                "tipo": tipo_f,
                "autor": autor_f,
                "id_caso": id_caso_f,
                "marca_temporal": marca_f,
                "hash": hash_f,
                **payload,
            })
        return resultados


# ------------------------------------------------------------------
# Anonimización PII (RF-23)
# ------------------------------------------------------------------

def anonimizar_paciente(
    nombre: str,
    fecha_nacimiento: str,
    rut_u_id: str,
) -> str:
    """
    RF-23: Genera el ID anónimo del paciente.
    ID = SHA-256(nombre + fecha_nacimiento + rut_u_id).
    La cadena se normaliza a minúsculas sin espacios.
    """
    entrada = f"{nombre.lower().strip()}{fecha_nacimiento.strip()}{rut_u_id.lower().strip()}"
    return hashlib.sha256(entrada.encode("utf-8")).hexdigest()


def verificar_integridad_evento(blob_cifrado: bytes, hash_almacenado: str) -> bool:
    """Verifica que el hash del blob coincida con el almacenado en DB."""
    hash_calculado = hashlib.sha256(blob_cifrado).hexdigest()
    return hash_calculado == hash_almacenado
