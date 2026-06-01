#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
catalog_manager.py
Conexión por operación (context manager); sin conexión persistente global.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import logging
import os

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


@dataclass
class CatalogConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


class CatalogManager:

    def __init__(self, config: CatalogConfig) -> None:
        self.config = config

    # ------------------------------------------------------------------ factory
    @classmethod
    def from_file(cls, config_file_path: str) -> "CatalogManager":
        values: Dict[str, str] = {}
        with open(config_file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                # Expande ${VAR} o $VAR con el valor del entorno en tiempo de carga
                values[key.strip()] = os.path.expandvars(value.strip())
        return cls(CatalogConfig(
            host=values.get("catalog_host", "localhost"),
            port=int(values.get("catalog_port", 5432)),
            dbname=values.get("catalog_db", ""),
            user=values.get("catalog_user", ""),
            password=values.get("catalog_pass", ""),
        ))

    # ---------------------------------------------------------------- conexión
    @contextmanager
    def _conn(self):
        conn = psycopg2.connect(
            host=self.config.host, port=self.config.port,
            dbname=self.config.dbname, user=self.config.user,
            password=self.config.password,
        )
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def _cur(self, conn):
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
        finally:
            cur.close()

    def rollback(self) -> None:
        """
        No-op intencional: esta clase usa conexiones por operación (cada método
        de CatalogManager abre y cierra su propia conexión dentro de _conn()).
        El rollback es automático en el __exit__ del context manager cuando
        ocurre una excepción, por lo que para cuando los servicios llaman a
        este método la conexión ya está cerrada y el rollback ya se ejecutó.

        Se mantiene este método para que los servicios puedan llamarlo de forma
        explícita sin romper la interfaz. Si en el futuro se refactoriza a una
        conexión persistente, este método deberá implementarse correctamente.
        """
        logger.debug("CatalogManager.rollback() called — no-op (per-operation connections)")

    # ------------------------------------------------------------ system settings
    def get_system_setting(self, param_name: str) -> Optional[str]:
        sql = "SELECT value FROM catalog.system_settings WHERE param_name = %s"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (param_name,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_system_setting(self, param_name: str, value: str,
                           units: Optional[str] = None) -> None:
        sql = """
            INSERT INTO catalog.system_settings (param_name, value, units)
            VALUES (%s, %s, %s)
            ON CONFLICT (param_name) DO UPDATE
            SET value = EXCLUDED.value, units = EXCLUDED.units
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (param_name, value, units))

    # --------------------------------------------------------------- workspaces
    def _ws_sql(self) -> str:
        return """
            SELECT id,
                   name,
                   description,
                   geom,
                   ST_AsText(geom) AS wkt,
                   s2_user,
                   s2_pass,
                   s2_download_url,
                   s2_product_type,
                   s2_time_range,
                   s2_download_path,
                   s2_process_command,
                   s2_process_params,
                   max_downloads_per_user,
                   log_path,
                   days_to_query_mosaic,
                   s2_granules_list,
                   active,
                   s2_collection,
                   s2_max_cloud_cover
            FROM catalog.workspaces
        """

    def get_active_workspaces(self) -> List[Dict[str, Any]]:
        sql = self._ws_sql() + " WHERE active IS TRUE ORDER BY id"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def get_workspace(self, workspace_id: int) -> Optional[Dict[str, Any]]:
        sql = self._ws_sql() + " WHERE id = %s"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (workspace_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_workspaces(self, workspace_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Todos los workspaces (activos e inactivos) o uno concreto."""
        if workspace_id is not None:
            row = self.get_workspace(workspace_id)
            return [row] if row else []
        sql = self._ws_sql() + " ORDER BY id"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    # -------------------------------------------------------- download queue
    def add_download_task(
        self, *,
        uuid: str,
        workspace_id: int,
        product_id: Optional[str] = None,
        path: Optional[str] = None,
        ingestion_date=None,
        sensing_date=None,
        cloud_coverage: Optional[float] = None,
        sensor: Optional[str] = None,
        orbit_number: Optional[int] = None,
        tile_id: Optional[str] = None,
        tile_data_geometry: Optional[str] = None,
        priority: int = 1,
        status: str = "waiting",
    ) -> None:
        sql = """
            INSERT INTO catalog.download_queue (
                uuid,
                priority,
                workspace_id,
                creation_time,
                status,
                product_id,
                path,
                ingestion_date,
                sensing_date,
                cloud_coverage,
                sensor,
                orbit_number,
                tile_id,
                tile_data_geometry
            ) VALUES (
                %(uuid)s, %(priority)s, %(workspace_id)s, NOW(), %(status)s,
                %(product_id)s, %(path)s, %(ingestion_date)s, %(sensing_date)s,
                %(cloud_coverage)s, %(sensor)s, %(orbit_number)s, %(tile_id)s,
                CASE WHEN %(tile_data_geometry)s IS NULL THEN NULL
                     ELSE ST_GeomFromText(%(tile_data_geometry)s, 4326) END
            )
            ON CONFLICT (uuid) DO NOTHING
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, dict(
                uuid=uuid, priority=priority, workspace_id=workspace_id,
                status=status, product_id=product_id, path=path,
                ingestion_date=ingestion_date, sensing_date=sensing_date,
                cloud_coverage=cloud_coverage, sensor=sensor,
                orbit_number=orbit_number, tile_id=tile_id,
                tile_data_geometry=tile_data_geometry,
            ))

    def download_task_exists(self, uuid: str) -> bool:
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute("SELECT 1 FROM catalog.download_queue WHERE uuid = %s", (uuid,))
            return cur.fetchone() is not None

    def exist_product(self, product_id: str) -> bool:
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(
                "SELECT 1 FROM catalog.original_products WHERE product_id = %s LIMIT 1",
                (product_id,),
            )
            return cur.fetchone() is not None

    def get_download_tasks_join_workspace(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        only_active: bool = False,
    ) -> List[Dict[str, Any]]:
        filters, params = [], []
        if status is not None:
            filters.append("dq.status = %s"); params.append(status)
        if only_active:
            filters.append("ws.active IS TRUE")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        limit_sql = f"LIMIT {int(limit)}" if limit else ""
        sql = f"""
            SELECT
                dq.id,
                dq.uuid,
                dq.priority,
                dq.workspace_id,
                dq.creation_time,
                dq.status,
                dq.init_time,
                dq.product_id,
                dq.path,
                dq.ingestion_date,
                dq.sensing_date AS sensing_date,
                dq.cloud_coverage AS cloud_coverage,
                dq.sensor,
                dq.orbit_number AS orbit_number,
                dq.tile_id AS tile_id,
                ST_AsText(dq.tile_data_geometry) AS wkt_geom,
                ws.s2_user  AS s2_user,
                ws.s2_pass AS s2_pass,
                ws.s2_download_url AS s2_download_url,
                ws.s2_download_path AS s2_download_path,
                ws.s2_process_command AS s2_process_command,
                ws.s2_process_params AS s2_process_params,
                ws.s2_collection AS s2_collection,
                ws.s2_time_range AS s2_time_range,
                ws.max_downloads_per_user AS max_downloads_per_user,
                ws.s2_max_cloud_cover AS s2_max_cloud_cover,
                ws.active
            FROM catalog.download_queue dq
            INNER JOIN catalog.workspaces ws ON ws.id = dq.workspace_id
            {where}
            ORDER BY dq.priority DESC NULLS LAST, dq.creation_time ASC NULLS LAST
            {limit_sql}
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update_download_status(
        self,
        identifier: Union[int, str],
        status: str,
        init_time: Union[bool, str, None] = None,
        path: Optional[str] = None,
    ) -> None:
        """identifier puede ser uuid (str) o id (int)."""
        sets = ["status = %s"]
        params: list = [status]
        if init_time:
            sets.append("init_time = NOW()")
        if path is not None:
            sets.append("path = %s"); params.append(path)
        if isinstance(identifier, int):
            params.append(identifier); where = "id = %s"
        else:
            params.append(str(identifier)); where = "uuid = %s"
        sql = f"UPDATE catalog.download_queue SET {', '.join(sets)} WHERE {where}"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)

    def cancel_old_download_tasks(self, timeout: Optional[int] = None) -> None:
        if timeout:
            sql = """UPDATE catalog.download_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'downloading'
                     AND init_time < NOW() - (%s || ' hours')::interval"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql, (str(timeout),))
        else:
            sql = """UPDATE catalog.download_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'downloading'"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql)

    # --------------------------------------------------------- process queue
    def add_processing_task(
        self, *,
        input_file_path: str,
        workspace_id: int,
        process_command: Optional[str] = None,
        process_params: Optional[str] = None,
        product_id: Optional[str] = None,
        uuid: Optional[str] = None,
        orbit_number: Optional[int] = None,
        sensing_date=None,
        priority: int = 1,
        status: str = "waiting",
    ) -> None:
        sql = """
            INSERT INTO catalog.process_queue (
                status, process_params, process_command, init_time, finish_time,
                input_file_path, workspace_id, priority, creation_time,
                product_id, uuid, orbit_number, sensing_date
            ) VALUES (
                %(status)s, %(process_params)s, %(process_command)s,
                NULL, NULL,
                %(input_file_path)s, %(workspace_id)s, %(priority)s, NOW(),
                %(product_id)s, %(uuid)s, %(orbit_number)s, %(sensing_date)s
            )
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, dict(
                status=status, process_params=process_params,
                process_command=process_command,
                input_file_path=input_file_path, workspace_id=workspace_id,
                priority=priority, product_id=product_id,
                uuid=uuid, orbit_number=orbit_number, sensing_date=sensing_date,
            ))

    def get_process_tasks_join_workspace(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        only_active: bool = False,
    ) -> List[Dict[str, Any]]:
        filters, params = [], []
        if status is not None:
            filters.append("pq.status = %s"); params.append(status)
        if only_active:
            filters.append("ws.active IS TRUE")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        limit_sql = f"LIMIT {int(limit)}" if limit else ""
        sql = f"""
            SELECT
                pq.id AS task_id,
                pq.status,
                pq.process_params AS process_params,
                pq.process_command AS process_command,
                pq.init_time,
                pq.finish_time,
                pq.input_file_path AS input_file_path,
                pq.workspace_id AS workspace_id,
                pq.priority,
                pq.creation_time,
                pq.product_id AS product_id,
                pq.uuid,
                pq.orbit_number AS orbit_number,
                pq.sensing_date AS sensing_date,
                ws.s2_process_command AS s2_process_command,
                ws.s2_process_params AS s2_process_params,
                ws.log_path AS log_path,
                ws.active
            FROM catalog.process_queue pq
            INNER JOIN catalog.workspaces ws ON ws.id = pq.workspace_id
            {where}
            ORDER BY pq.priority DESC NULLS LAST, pq.creation_time ASC NULLS LAST
            {limit_sql}
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update_process_status(
        self,
        task_id: int,
        status: str,
        init_time: Union[bool, str, None] = None,
        finish_time: Union[bool, str, None] = None,
    ) -> None:
        sets = ["status = %s"]; params: list = [status]
        if init_time:
            sets.append("init_time = NOW()")
        if finish_time:
            sets.append("finish_time = NOW()")
        params.append(task_id)
        sql = f"UPDATE catalog.process_queue SET {', '.join(sets)} WHERE id = %s"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)

    def cancel_old_processing_tasks(self, timeout: Optional[int] = None) -> None:
        if timeout:
            sql = """UPDATE catalog.process_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'processing'
                     AND init_time < NOW() - (%s || ' hours')::interval"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql, (str(timeout),))
        else:
            sql = """UPDATE catalog.process_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'processing'"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql)

    # ---------------------------------------------------------- mosaic queue
    def add_mosaic_task(
        self, *,
        first_date,
        workspace_id: int,
        sensing_date=None,
        orbit_id: Optional[int] = None,
        priority: int = 1,
        status: str = "waiting",
    ) -> None:
        sql = """
            INSERT INTO catalog.mosaic_queue (
                first_date, workspace_id, status, sensing_date,
                orbit_id, init_time, creation_time, priority
            ) VALUES (%s, %s, %s, %s, %s, NULL, NOW(), %s)
            ON CONFLICT ON CONSTRAINT mosaic_queue_uq_operational DO NOTHING
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (first_date, workspace_id, status,
                               sensing_date, orbit_id, priority))

    def get_mosaic_tasks_join_workspace(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        only_active: bool = False,
    ) -> List[Dict[str, Any]]:
        filters, params = [], []
        if status is not None:
            filters.append("mq.status = %s"); params.append(status)
        if only_active:
            filters.append("ws.active IS TRUE")
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        limit_sql = f"LIMIT {int(limit)}" if limit else ""
        sql = f"""
            SELECT
                mq.id AS task_id,
                mq.first_date AS first_date,
                mq.workspace_id AS workspace_id,
                mq.status,
                mq.sensing_date AS sensing_date,
                mq.orbit_id AS orbit_id,
                mq.init_time,
                mq.creation_time,
                mq.priority,
                ws.days_to_query_mosaic AS days_to_query_mosaic,
                ws.active
            FROM catalog.mosaic_queue mq
            INNER JOIN catalog.workspaces ws ON ws.id = mq.workspace_id
            {where}
            ORDER BY mq.priority DESC NULLS LAST, mq.creation_time ASC NULLS LAST
            {limit_sql}
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def update_mosaic_status(
        self,
        task_id: int,
        status: str,
        init_time: Union[bool, str, None] = None,
    ) -> None:
        sets = ["status = %s"]; params: list = [status]
        if init_time:
            sets.append("init_time = NOW()")
        params.append(task_id)
        sql = f"UPDATE catalog.mosaic_queue SET {', '.join(sets)} WHERE id = %s"
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)

    def cancel_old_mosaic_tasks(self, timeout: Optional[int] = None) -> None:
        if timeout:
            sql = """UPDATE catalog.mosaic_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'processing'
                     AND init_time < NOW() - (%s || ' hours')::interval"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql, (str(timeout),))
        else:
            sql = """UPDATE catalog.mosaic_queue SET status = 'waiting', init_time = NULL
                     WHERE status = 'processing'"""
            with self._conn() as conn, self._cur(conn) as cur:
                cur.execute(sql)

    # --------------------------------------------------- original products
    def ingest_original_product(
        self, *,
        url: Optional[str] = None,
        ingestion_date=None,
        sensing_date=None,
        tile_data_geometry: Optional[str] = None,
        cloud_coverage: Optional[float] = None,
        sensor: Optional[str] = None,
        orbit_number: Optional[int] = None,
        tile_id: Optional[str] = None,
        product_id: Optional[str] = None,
        processed: Optional[bool] = None,
        used: Optional[bool] = None,
        workspace_id: Optional[int] = None,
        # compat aliases
        file_path: Optional[str] = None,
        filepath: Optional[str] = None,
        platform_identifier: Optional[str] = None,
        footprint: Optional[str] = None,
        granule_id: Optional[str] = None,
        workspace: Optional[int] = None,
    ) -> int:
        url = url or file_path or filepath
        sensor = sensor or platform_identifier
        tile_data_geometry = tile_data_geometry or footprint
        tile_id = tile_id or granule_id
        workspace_id = workspace_id or workspace
        sql = """
            INSERT INTO catalog.original_products (
                url,
                ingestion_date,
                sensing_date,
                tile_data_geometry,
                cloud_coverage,
                sensor,
                orbit_number,
                tile_id,
                product_id,
                processed,
                used,
                workspace_id
            ) VALUES (
                %(url)s, %(ingestion_date)s, %(sensing_date)s,
                CASE WHEN %(tile_data_geometry)s IS NULL THEN NULL
                     ELSE ST_GeomFromText(%(tile_data_geometry)s, 4326) END,
                %(cloud_coverage)s, %(sensor)s, %(orbit_number)s, %(tile_id)s,
                %(product_id)s, %(processed)s, %(used)s, %(workspace_id)s
            ) RETURNING id
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, dict(
                url=url, ingestion_date=ingestion_date, sensing_date=sensing_date,
                tile_data_geometry=tile_data_geometry, cloud_coverage=cloud_coverage,
                sensor=sensor, orbit_number=orbit_number, tile_id=tile_id,
                product_id=product_id, processed=processed, used=used,
                workspace_id=workspace_id,
            ))
            return cur.fetchone()["id"]

    def get_original_product_by_product_id(
        self,
        product_id: str,
        workspace_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        filters = ["product_id = %s"]; params: list = [product_id]
        if workspace_id is not None:
            filters.append("workspace_id = %s"); params.append(workspace_id)
        sql = f"""
            SELECT 
                id,
                url,
                ingestion_date,
                sensing_date,
                ST_AsText(tile_data_geometry) AS tile_data_geometry_wkt,
                cloud_coverage,
                sensor,
                orbit_number,
                tile_id,
                product_id,
                processed,
                used,
                workspace_id
            FROM catalog.original_products
            WHERE {' AND '.join(filters)} LIMIT 1
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    # ---------------------------------------------------- derived products
    def ingest_derived_product(
        self, *,
        url: Optional[str] = None,
        product_type: Optional[str] = None,
        original_product_id: Optional[int] = None,
        ingestion_date=None,
        workspace_id: Optional[int] = None,
        derived_from_uuid: Optional[str] = None,
    ) -> int:
        sql = """
            INSERT INTO catalog.derived_products (
                product_type, original_product_id, ingestion_date,
                url, workspace_id, derived_from_uuid
            ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (product_type, original_product_id,
                               ingestion_date, url, workspace_id, derived_from_uuid))
            return cur.fetchone()["id"]

    def get_derived_products(
        self, *,
        workspace_id: Optional[int] = None,
        original_product_id: Optional[int] = None,
        derived_from_uuid: Optional[str] = None,
        product_type: Optional[str] = None,
        sensing_date=None,
        orbit_id: Optional[int] = None,
        sensor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filters, params = [], []
        if workspace_id is not None:
            filters.append("dp.workspace_id = %s"); params.append(workspace_id)
        if original_product_id is not None:
            filters.append("dp.original_product_id = %s"); params.append(original_product_id)
        if derived_from_uuid is not None:
            filters.append("dp.derived_from_uuid = %s"); params.append(derived_from_uuid)
        if product_type is not None:
            filters.append("dp.product_type = %s"); params.append(product_type)
        if sensing_date is not None:
            filters.append("op.sensing_date = %s"); params.append(sensing_date)
        if orbit_id is not None:
            filters.append("op.orbit_number = %s"); params.append(orbit_id)
        if sensor is not None:
            filters.append("op.sensor LIKE %s"); params.append(sensor)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        sql = f"""
            SELECT dp.id,
                   dp.product_type AS product_type,
                   dp.original_product_id AS original_product_id,
                   dp.ingestion_date,
                   dp.url AS derived_url,
                   dp.workspace_id AS workspace_id,
                   dp.derived_from_uuid AS derived_from_uuid,
                   op.product_id AS product_id,
                   op.tile_id AS tile_id
            FROM catalog.derived_products dp
            LEFT JOIN catalog.original_products op ON op.id = dp.original_product_id
            {where}
            ORDER BY dp.id DESC
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------- mosaic definitions
    def get_mosaic_definition(
        self, workspace_id: int, orbit_id: int
    ) -> Optional[Dict[str, Any]]:
        """Devuelve una sola definición de mosaico o None."""
        results = self.get_mosaic_definitions(workspace_id=workspace_id, orbit_id=orbit_id)
        return results[0] if results else None

    def get_mosaic_definitions(
        self,
        workspace_id: Optional[int] = None,
        orbit_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        filters, params = [], []
        if workspace_id is not None:
            filters.append("workspace_id = %s"); params.append(workspace_id)
        if orbit_id is not None:
            filters.append("orbit_id = %s"); params.append(orbit_id)
        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        sql = f"""
            SELECT workspace_id,
                   granules_list,
                   source_products_names,
                   mosaic_names,
                   mosaic_paths,
                   source_products_paths,
                   orbit_id
            FROM catalog.mosaic_definitions {where}
            ORDER BY workspace_id, orbit_id
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def upsert_mosaic_definition(
        self, *,
        workspace_id: int,
        orbit_id: int,
        granules_list: str,
        source_products_names: Optional[str] = None,
        mosaic_names: Optional[str] = None,
        mosaic_paths: Optional[str] = None,
        source_products_paths: Optional[str] = None,
    ) -> None:
        sql = """
            INSERT INTO catalog.mosaic_definitions (
                workspace_id,
                granules_list,
                source_products_names,
                mosaic_names,
                mosaic_paths,
                source_products_paths,
                orbit_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (workspace_id, orbit_id) DO UPDATE SET
                granules_list        = EXCLUDED.granules_list,
                source_products_names = EXCLUDED.source_products_names,
                mosaic_names         = EXCLUDED.mosaic_names,
                mosaic_paths         = EXCLUDED.mosaic_paths,
                source_products_paths = EXCLUDED.source_products_paths
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (workspace_id, granules_list, source_products_names,
                               mosaic_names, mosaic_paths, source_products_paths, orbit_id))

    # ------------------------------------------------- cloud coverage worker
    def get_download_tasks_without_cloud(
        self,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Devuelve tareas en estado 'waiting' cuyo cloud_coverage es NULL.
        Usadas por CloudCoverageService para rellenar el dato consultando CDSE.
        """
        limit_sql = f"LIMIT {int(limit)}" if limit else ""
        sql = f"""
            SELECT uuid,
                   product_id,
                   workspace_id
            FROM catalog.download_queue
            WHERE status = 'waiting'
              AND cloud_coverage IS NULL
            ORDER BY creation_time ASC
            {limit_sql}
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]

    def update_download_cloud_coverage(
        self,
        uuid: str,
        cloud_coverage: float,
    ) -> None:
        """Actualiza el campo cloud_coverage de una tarea por su uuid."""
        sql = """
            UPDATE catalog.download_queue
               SET cloud_coverage = %s
             WHERE uuid = %s
        """
        with self._conn() as conn, self._cur(conn) as cur:
            cur.execute(sql, (cloud_coverage, uuid))

    def reset_skipped_downloads(
            self,
            workspace_id: int | None = None,
            max_cloud: float | None = None,
    ) -> int:
        """
        Devuelve a 'waiting' las tareas skipped para que sean reevaluadas.

        Útil cuando se modifica s2_max_cloud_cover en el workspace.
        Opcionalmente filtra solo las que ahora cumplirían el nuevo umbral.

        Returns:
            Número de tareas reseteadas.
        """
        with self._conn() as conn:
            cur = conn.cursor()
            conditions = ["dq.status = 'skipped'"]
            params: list = []

            if workspace_id is not None:
                conditions.append("dq.workspace_id = %s")
                params.append(workspace_id)

            if max_cloud is not None:
                conditions.append("dq.cloud_coverage <= %s")
                params.append(max_cloud)

            where = " AND ".join(conditions)
            cur.execute(
                f"UPDATE catalog.download_queue SET status = 'waiting' "
                f"WHERE {where}",
                params,
            )
            count = cur.rowcount
            conn.commit()
        return count

    def close(self):
        """Método para evitar errores en la limpieza de la sesión"""
        pass
