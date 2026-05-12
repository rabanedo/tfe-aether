#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
s2_processor.py — Creación y verificación de mosaicos Sentinel-2.
Usa la API de CatalogManager con kwargs explícitos.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from osgeo import gdal

gdal.UseExceptions()


# ------------------------------------------------------------------ helpers

def _normalize_to_date(value) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
    raise ValueError(f"Unsupported date value: {value!r}")


def _split_values(value) -> list[str]:
    if value is None:
        return []
    return str(value).split()


def _derived_granules(derived_products: Iterable[dict]) -> list[str]:
    return [f"T{p['tile_id']}" for p in derived_products if p.get("tile_id")]


def _get_mosaic_definition(catalog, workspace_id: int, orbit_id: int) -> dict:
    definition = catalog.get_mosaic_definition(workspace_id, orbit_id)
    if not definition:
        raise ValueError(
            f"No mosaic definition for workspace_id={workspace_id}, orbit_id={orbit_id}"
        )
    return definition


def _build_output_path(base_path: str, sensing_date: date,
                        sensor: str, orbit_id: int, product_name: str) -> Path:
    name = (
        f"{sensing_date.strftime('%Y%m%d')}_{sensor}_mosaic_"
        f"R{int(orbit_id):03d}_{product_name}"
    )
    return Path(base_path) / name


# ------------------------------------------------------------------ public API

def create_mosaic(catalog, task: dict) -> None:
    workspace_id = task["workspace_id"]
    orbit_id     = task["orbit_id"]
    sensing_date = _normalize_to_date(task["sensing_date"])

    mosaic_def    = _get_mosaic_definition(catalog, workspace_id, orbit_id)
    product_names = _split_values(mosaic_def.get("source_products_names"))
    mosaic_paths  = _split_values(mosaic_def.get("mosaic_paths"))

    if not product_names:
        raise ValueError(
            f"Mosaic definition workspace_id={workspace_id} orbit_id={orbit_id}"
            " has no source_products_names"
        )
    if len(product_names) != len(mosaic_paths):
        raise ValueError(
            "source_products_names and mosaic_paths length mismatch"
        )

    for product_name, mosaic_path in zip(product_names, mosaic_paths):
        derived = catalog.get_derived_products(
            sensing_date=sensing_date,
            product_type=product_name,
            orbit_id=orbit_id,
            sensor="Sentinel%",
            workspace_id=workspace_id,
        )
        if not derived:
            raise ValueError(
                f"No derived products for sensing_date={sensing_date} "
                f"product={product_name} orbit_id={orbit_id} workspace_id={workspace_id}"
            )

        derived_paths = [p["derived_url"] for p in derived if p.get("derived_url")]
        if not derived_paths:
            raise ValueError(
                f"Derived products for product={product_name} have no derived_url"
            )

        product_id = derived[0].get("product_id")
        if not product_id:
            raise ValueError(
                f"Derived product for product={product_name} missing product_id"
            )
        sensor = str(product_id).split("_")[0]

        output_base = _build_output_path(mosaic_path, sensing_date, sensor,
                                          orbit_id, product_name)
        output_base.parent.mkdir(parents=True, exist_ok=True)
        vrt_path = str(output_base.with_suffix(".vrt"))
        tif_path = str(output_base.with_suffix(".tif"))

        gdal.BuildVRT(vrt_path, derived_paths)
        ds = gdal.Open(vrt_path)
        if ds is None:
            raise RuntimeError(f"Cannot open VRT: {vrt_path}")
        ds = gdal.Translate(tif_path, ds, creationOptions=["COMPRESS=DEFLATE"])
        if ds is None:
            raise RuntimeError(f"Cannot translate to GeoTIFF: {tif_path}")
        ds = None

        catalog.ingest_derived_product(
            url=tif_path,
            product_type=f"{product_name}_mosaic",
            original_product_id=None,
            ingestion_date=date.today(),
            workspace_id=workspace_id,
        )

        if os.path.exists(vrt_path):
            os.remove(vrt_path)


def is_mosaic_ready(catalog, task: dict) -> bool:
    workspace_id = task["workspace_id"]
    orbit_id     = task["orbit_id"]
    sensing_date = _normalize_to_date(task["sensing_date"])

    mosaic_def    = _get_mosaic_definition(catalog, workspace_id, orbit_id)
    product_names = _split_values(mosaic_def.get("source_products_names"))
    granules_list = _split_values(mosaic_def.get("granules_list"))

    if not product_names or not granules_list:
        return False

    for product_name in product_names:
        derived = catalog.get_derived_products(
            sensing_date=sensing_date,
            product_type=product_name,
            orbit_id=orbit_id,
            sensor="Sentinel%",
            workspace_id=workspace_id,
        )
        if not derived:
            return False
        if not all(g in _derived_granules(derived) for g in granules_list):
            return False

    return True
