#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
rgb_ndvi.py — Procesador de productos derivados Sentinel-2 (RGB y NDVI)
"""

from __future__ import annotations

import argparse
import importlib.util
import logging
import os
import shlex
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path
from subprocess import run
from typing import List, Optional

from osgeo import gdal

gdal.UseExceptions()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _run_cmd(cmd: str, allowed_rc: tuple = ()) -> None:
    """Ejecuta un comando. Lanza RuntimeError si falla."""
    result = run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0 and result.returncode not in allowed_rc:
        raise RuntimeError(
            f"Comando fallido (rc={result.returncode}):\n"
            f"  CMD: {cmd}\n"
            f"  STDERR: {result.stderr.strip()}"
        )


def _gdal_translate_sds(xml_path: str, out_vrt_base: str) -> None:
    """
    Equivalente Python a 'gdal_translate -of VRT -sds xml out.vrt'.
    Evita el segfault de GDAL >= 3.9 en el cleanup del proceso externo.
    Escribe out_VRT_1.vrt, out_VRT_2.vrt, ... por cada subdataset.
    """
    from osgeo import gdal as _gdal
    _gdal.UseExceptions()
    ds = _gdal.Open(xml_path, _gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"GDAL no pudo abrir: {xml_path}")
    subdatasets = ds.GetSubDatasets()
    ds = None
    if not subdatasets:
        raise RuntimeError(f"Sin subdatasets en: {xml_path}")
    for idx, (sd_name, _sd_desc) in enumerate(subdatasets, start=1):
        out_path = f"{out_vrt_base}_{idx}.vrt"
        sd_ds = _gdal.Open(sd_name, _gdal.GA_ReadOnly)
        if sd_ds is None:
            raise RuntimeError(f"No se pudo abrir subdataset: {sd_name}")
        drv = _gdal.GetDriverByName("VRT")
        vrt_ds = drv.CreateCopy(out_path, sd_ds)
        if vrt_ds is None:
            raise RuntimeError(f"No se pudo crear VRT: {out_path}")
        vrt_ds.FlushCache()
        vrt_ds = None
        sd_ds = None
    logger.debug("_gdal_translate_sds: %d subdatasets escritos en %s_*.vrt",
                 len(subdatasets), out_vrt_base)


def _remove_files(*paths: str) -> None:
    for p in paths:
        try:
            os.remove(p)
        except FileNotFoundError:
            pass


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Procesadores de bandas
# ---------------------------------------------------------------------------

def _to_cog(
    src: str,
    dst: str,
    compress: str = "LZW",
    predictor: int = 2,
    blocksize: int = 512,
    nodata: str | None = None,
    srs: str = "EPSG:25830",
) -> None:
    """
    Reproyecta src a srs y escribe dst como Cloud Optimized GeoTIFF.

    El driver COG de GDAL (>= 3.1) genera en un único paso:
      - Tiles internos de blocksize x blocksize píxeles
      - Overviews internos con remuestreo AVERAGE
      - Cabecera con IFDs al inicio del fichero (requisito COG)

    Compresiones recomendadas por tipo de dato:
      - RGB Byte visual  → JPEG   (lossy, ~5x más pequeño, válido para WMS)
      - NDVIb Byte       → LZW  + PREDICTOR=2 (lossless, preserva nodata exacto)
      - NDVI Float32     → DEFLATE + PREDICTOR=3 (lossless float, mejor que LZW)

    Args:
        src:       Fichero fuente (cualquier formato GDAL).
        dst:       Fichero COG de salida (.tif).
        compress:  Algoritmo de compresión (LZW, DEFLATE, JPEG).
        predictor: Predictor de compresión (2=int, 3=float; ignorado por JPEG).
        blocksize: Tamaño de tile interno en píxeles.
        nodata:    Valor nodata como string, o None para no establecer.
        srs:       SRS destino para gdalwarp.
    """
    warped = dst + "_warp_tmp.tif"
    try:
        nodata_opt = f"-dstnodata {nodata}" if nodata is not None else ""
        _run_cmd(
            f"gdalwarp -t_srs {srs} {nodata_opt} -overwrite {src} {warped}"
        )
        predictor_opt = (
            f"-co PREDICTOR={predictor}"
            if compress.upper() not in ("JPEG",)
            else ""
        )
        _run_cmd(
            f"gdal_translate -of COG "
            f"-a_srs {srs} "
            f"-co COMPRESS={compress} {predictor_opt} "
            f"-co BLOCKSIZE={blocksize} "
            f"-co OVERVIEW_RESAMPLING=AVERAGE "
            f"-co BIGTIFF=IF_SAFER "
            f"{warped} {dst}"
        )
    finally:
        _remove_files(warped)


def compute_rgb432(xml_path: str, out_path: str,
                   coef_r: float = 0.05, coef_g: float = 0.05, coef_b: float = 0.05) -> None:
    vrt = out_path + "_VRT.vrt"
    ds1 = out_path + "_VRT_1.vrt"
    b4_vrt, b3_vrt, b2_vrt = out_path + "_b4.vrt", out_path + "_b3.vrt", out_path + "_b2.vrt"
    b4_tif, b3_tif, b2_tif = out_path + "_b4.tif", out_path + "_b3.tif", out_path + "_b2.tif"
    tmp = out_path + "_original_srs.tif"

    _gdal_translate_sds(xml_path, vrt.removesuffix(".vrt"))
    _run_cmd(f"gdal_translate -of VRT -b 1 {ds1} {b4_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 2 {ds1} {b3_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 3 {ds1} {b2_vrt}")

    calc = "(A.astype(float)*B*C!=0)*(A*{c}*(A*{c}<=255)+(A*{c}>255)*255)"
    _run_cmd(f"gdal_calc.py -A {b4_vrt} -B {b3_vrt} -C {b2_vrt} --outfile={b4_tif} "
             f"--calc=\'{calc.format(c=coef_r)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b3_vrt} -B {b4_vrt} -C {b2_vrt} --outfile={b3_tif} "
             f"--calc=\'{calc.format(c=coef_g)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b2_vrt} -B {b4_vrt} -C {b3_vrt} --outfile={b2_tif} "
             f"--calc=\'{calc.format(c=coef_b)}\' --type=Byte --NoDataValue=0 --overwrite")

    _run_cmd(f"gdal_merge.py -separate -ot Byte -o {tmp} {b4_tif} {b3_tif} {b2_tif}")
    _to_cog(tmp, out_path, compress="JPEG", nodata="0")

    _remove_files(
        out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt",
        out_path + "_VRT_3.vrt", out_path + "_VRT_4.vrt",
        b4_vrt, b3_vrt, b2_vrt, b4_tif, b3_tif, b2_tif, tmp,
    )


def compute_rgb1184(xml_path: str, out_path: str,
                    coef_r: float = 0.05, coef_g: float = 0.05, coef_b: float = 0.05) -> None:
    vrt = out_path + "_VRT.vrt"
    ds1, ds2 = out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt"
    b4_vrt, b8_vrt = out_path + "_b4.vrt", out_path + "_b8.vrt"
    b11_20_vrt, b11_vrt = out_path + "_b11_20.vrt", out_path + "_b11.vrt"
    b4_tif, b8_tif, b11_tif = out_path + "_b4.tif", out_path + "_b8.tif", out_path + "_b11.tif"
    tmp = out_path + "_original_srs.tif"

    _gdal_translate_sds(xml_path, vrt.removesuffix(".vrt"))
    _run_cmd(f"gdal_translate -of VRT -b 5 {ds2} {b11_20_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 4 {ds1} {b8_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 1 {ds1} {b4_vrt}")
    _run_cmd(f"gdalwarp -tr 10 10 -of VRT {b11_20_vrt} {b11_vrt}")

    calc = "(A.astype(float)*B*C!=0)*(A*{c}*(A*{c}<=255)+(A*{c}>255)*255)"
    _run_cmd(f"gdal_calc.py -A {b11_vrt} -B {b8_vrt} -C {b4_vrt} --outfile={b11_tif} "
             f"--calc=\'{calc.format(c=coef_r)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b8_vrt} -B {b11_vrt} -C {b4_vrt} --outfile={b8_tif} "
             f"--calc=\'{calc.format(c=coef_g)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b4_vrt} -B {b11_vrt} -C {b8_vrt} --outfile={b4_tif} "
             f"--calc=\'{calc.format(c=coef_b)}\' --type=Byte --NoDataValue=0 --overwrite")

    _run_cmd(f"gdal_merge.py -separate -ot Byte -o {tmp} {b11_tif} {b8_tif} {b4_tif}")
    _to_cog(tmp, out_path, compress="JPEG", nodata="0")

    _remove_files(
        out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt",
        out_path + "_VRT_3.vrt", out_path + "_VRT_4.vrt",
        b4_vrt, b8_vrt, b11_20_vrt, b11_vrt, b4_tif, b8_tif, b11_tif, tmp,
    )


def compute_rgb1283(xml_path: str, out_path: str,
                    coef_r: float = 0.05, coef_g: float = 0.05, coef_b: float = 0.05) -> None:
    vrt = out_path + "_VRT.vrt"
    ds1, ds2 = out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt"
    b3_vrt, b8_vrt = out_path + "_b3.vrt", out_path + "_b8.vrt"
    b12_20_vrt, b12_vrt = out_path + "_b12_20.vrt", out_path + "_b12.vrt"
    b3_tif, b8_tif, b12_tif = out_path + "_b3.tif", out_path + "_b8.tif", out_path + "_b12.tif"
    tmp = out_path + "_original_srs.tif"

    _gdal_translate_sds(xml_path, vrt.removesuffix(".vrt"))
    _run_cmd(f"gdal_translate -of VRT -b 6 {ds2} {b12_20_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 4 {ds1} {b8_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 2 {ds1} {b3_vrt}")
    _run_cmd(f"gdalwarp -tr 10 10 -of VRT {b12_20_vrt} {b12_vrt}")

    calc = "(A.astype(float)*B*C!=0)*(A*{c}*(A*{c}<=255)+(A*{c}>255)*255)"
    _run_cmd(f"gdal_calc.py -A {b12_vrt} -B {b8_vrt} -C {b3_vrt} --outfile={b12_tif} "
             f"--calc=\'{calc.format(c=coef_r)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b8_vrt} -B {b12_vrt} -C {b3_vrt} --outfile={b8_tif} "
             f"--calc=\'{calc.format(c=coef_g)}\' --type=Byte --NoDataValue=0 --overwrite")
    _run_cmd(f"gdal_calc.py -A {b3_vrt} -B {b12_vrt} -C {b8_vrt} --outfile={b3_tif} "
             f"--calc=\'{calc.format(c=coef_b)}\' --type=Byte --NoDataValue=0 --overwrite")

    _run_cmd(f"gdal_merge.py -separate -ot Byte -o {tmp} {b12_tif} {b8_tif} {b3_tif}")
    _to_cog(tmp, out_path, compress="JPEG", nodata="0")

    _remove_files(
        out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt",
        out_path + "_VRT_3.vrt", out_path + "_VRT_4.vrt",
        b3_vrt, b8_vrt, b12_20_vrt, b12_vrt, b3_tif, b8_tif, b12_tif, tmp,
    )


def compute_ndvi(xml_path: str, out_path: str) -> None:
    vrt = out_path + "_VRT.vrt"
    ds1 = out_path + "_VRT_1.vrt"
    b4_vrt, b8_vrt = out_path + "_b4.vrt", out_path + "_b8.vrt"
    tmp = out_path + "_original_srs.tif"

    _gdal_translate_sds(xml_path, vrt.removesuffix(".vrt"))
    _run_cmd(f"gdal_translate -of VRT -b 1 {ds1} {b4_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 4 {ds1} {b8_vrt}")

    calc = (
        "(A.astype(float)*B!=0)*(A.astype(float)-B)/"
        "(A.astype(float)+B+(A.astype(float)*B==0))+(A.astype(float)*B==0)*9999"
    )
    _run_cmd(
        f"gdal_calc.py -A {b8_vrt} -B {b4_vrt} --outfile={tmp} "
        f"--calc=\'{calc}\' --type=Float32 --NoDataValue=9999 --overwrite"
    )
    _to_cog(tmp, out_path, compress="DEFLATE", predictor=3, nodata="9999")

    _remove_files(
        out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt",
        out_path + "_VRT_3.vrt", out_path + "_VRT_4.vrt",
        b4_vrt, b8_vrt, tmp,
    )


def compute_ndvi_byte(xml_path: str, out_path: str) -> None:
    vrt = out_path + "_VRT.vrt"
    ds1 = out_path + "_VRT_1.vrt"
    b4_vrt, b8_vrt = out_path + "_b4.vrt", out_path + "_b8.vrt"
    tmp = out_path + "_original_srs.tif"

    _gdal_translate_sds(xml_path, vrt.removesuffix(".vrt"))
    _run_cmd(f"gdal_translate -of VRT -b 1 {ds1} {b4_vrt}")
    _run_cmd(f"gdal_translate -of VRT -b 4 {ds1} {b8_vrt}")

    calc = (
        "(A.astype(float)*B!=0)*(A.astype(float)-B)/"
        "(A.astype(float)+B+(A.astype(float)*B==0))*100"
        "+(A.astype(float)*B==0)*255"
    )
    _run_cmd(
        f"gdal_calc.py -A {b8_vrt} -B {b4_vrt} --outfile={tmp} "
        f"--calc=\'{calc}\' --type=Byte --NoDataValue=255 --overwrite"
    )
    _to_cog(tmp, out_path, compress="LZW", predictor=2, nodata="255")

    _remove_files(
        out_path + "_VRT_1.vrt", out_path + "_VRT_2.vrt",
        out_path + "_VRT_3.vrt", out_path + "_VRT_4.vrt",
        b4_vrt, b8_vrt, tmp,
    )


# ---------------------------------------------------------------------------
# CatalogManager — import diferido
# ---------------------------------------------------------------------------

def _resolve_config_file() -> str:
    return str(Path(__file__).resolve().parent.parent.parent / "config.txt")


def _get_catalog_manager(config_path: str):
    try:
        import sys as _sys
        spec = importlib.util.spec_from_file_location(
            "catalog_manager",
            str(Path(__file__).resolve().parent.parent / "repositories" / "catalog_manager.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        _sys.modules["catalog_manager"] = mod
        spec.loader.exec_module(mod)
        return mod.CatalogManager.from_file(config_path)
    except Exception as e:
        logger.error(f"No se pudo cargar CatalogManager: {e}")
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_zip_metadata(filename: str, date_field: int = 2) -> dict:
    parts = filename.split("_")
    return {
        "sensing_date":    parts[date_field].split("T")[0] if len(parts) > date_field else "",
        "generation_time": parts[6].split("T")[1].split(".")[0] if len(parts) > 6 else "000000",
        "granule_id":      parts[5] if len(parts) > 5 else "",
        "orbit_id":        parts[4] if len(parts) > 4 else "",
        "product_id":      parts[0] + "_" + parts[1] if len(parts) > 1 else parts[0],
    }


def _output_path(base: str, product_type: str, use_folders: bool,
                 sensing_date: str, generation_time: str,
                 product_id: str, granule_id: str, orbit_id: str) -> str:
    folder = base
    if use_folders:
        folder = os.path.join(base, product_type)
        _ensure_dir(folder)
    filename = f"{sensing_date}_{generation_time}_{product_id}_{granule_id}_{orbit_id}_{product_type}.tif"
    return os.path.join(folder, filename)


# ---------------------------------------------------------------------------
# Procesador principal de un ZIP
# ---------------------------------------------------------------------------

def process_zip(
    zip_path: str,
    output_path: str,
    tmp_path: str,
    product_list: List[str],
    publish_list: List[str],
    product_folders: bool = False,
    ingest_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    delete_source: bool = False,
    red_coef: float = 0.05,
    green_coef: float = 0.05,
    blue_coef: float = 0.05,
    date_field: int = 2,
    config_path: Optional[str] = None,
) -> None:
    filename = os.path.basename(zip_path)
    if not filename.lower().endswith(".zip"):
        logger.warning(f"No es un ZIP: {filename}")
        return

    meta = _parse_zip_metadata(filename, date_field)
    sensing_date    = meta["sensing_date"]
    generation_time = meta["generation_time"]
    granule_id      = meta["granule_id"]
    orbit_id        = meta["orbit_id"]
    product_id      = meta["product_id"]

    unzipped = os.path.join(tmp_path, filename.replace(".zip", "").replace(".ZIP", ""))
    if not unzipped.endswith(".SAFE"):
        unzipped += ".SAFE"

    logger.info(f"Descomprimiendo {filename} -> {unzipped}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_path)

    xml_path = os.path.join(unzipped, "MTD_MSIL2A.xml")
    if not os.path.exists(xml_path):
        xml_path = os.path.join(unzipped, "MTD_MSIL1C.xml")
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"No se encontró MTD_MSIL2A.xml ni MTD_MSIL1C.xml en {unzipped}")

    # Catálogo — sólo si se pide ingestión
    catalog = None
    if ingest_id:
        cfg = config_path or _resolve_config_file()
        catalog = _get_catalog_manager(cfg)

    def out(ptype: str) -> str:
        return _output_path(
            output_path, ptype, product_folders,
            sensing_date, generation_time, product_id, granule_id, orbit_id,
        )

    def ingest(file_path: str, ptype: str) -> None:
        if catalog and ingest_id:
            try:
                original = catalog.get_original_product_by_product_id(ingest_id)
                if original:
                    catalog.ingest_derived_product(
                        product_type=ptype,
                        original_product_id=original["id"],
                        ingestion_date=date.today(),
                        url=file_path,
                        workspace_id=workspace_id,
                        derived_from_uuid=ingest_id,
                    )
            except Exception as e:
                logger.error(f"Error ingesting {ptype}: {e}")

    # --- Productos ---

    if "RGB432" in product_list:
        p = out("RGB432")
        logger.info(f"Calculando RGB432 -> {p}")
        compute_rgb432(xml_path, p, red_coef, green_coef, blue_coef)
        ingest(p, "S2RGB432")

    if "RGB1184" in product_list:
        p = out("RGB1184")
        logger.info(f"Calculando RGB1184 -> {p}")
        compute_rgb1184(xml_path, p, red_coef, green_coef, blue_coef)
        ingest(p, "S2RGB1184")

    if "RGB1283" in product_list:
        p = out("RGB1283")
        logger.info(f"Calculando RGB1283 -> {p}")
        compute_rgb1283(xml_path, p, red_coef, green_coef, blue_coef)
        ingest(p, "S2RGB1283")

    if "NDVI" in product_list:
        p = out("NDVI")
        logger.info(f"Calculando NDVI -> {p}")
        compute_ndvi(xml_path, p)
        ingest(p, "S2NDVI")

    if "NDVIb" in product_list:
        p = out("NDVIb")
        logger.info(f"Calculando NDVIb -> {p}")
        compute_ndvi_byte(xml_path, p)
        ingest(p, "S2NDVIb")

    # NDVIb_mosaic: gestionado por mosaic_queue del servicio, no aquí
    if "NDVIb_mosaic" in product_list:
        logger.debug("NDVIb_mosaic se gestiona via mosaic_queue, saltando.")

    logger.info(f"Eliminando directorio descomprimido: {unzipped}")
    shutil.rmtree(unzipped, ignore_errors=True)

    if delete_source:
        logger.info(f"Eliminando fuente: {zip_path}")
        os.remove(zip_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Procesador de productos derivados Sentinel-2 (RGB y NDVI)"
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("-i", "--input",     dest="input_path",
                     help="Directorio con ZIPs Sentinel-2")
    src.add_argument("-f", "--inputfile", dest="input_file",
                     help="Fichero ZIP Sentinel-2 concreto")

    p.add_argument("-o", "--output",  dest="output_path", required=True,
                   help="Directorio de salida para productos derivados")
    p.add_argument("-t", "--tmp",     dest="tmp_path",    required=True,
                   help="Directorio temporal para descomprimir")
    p.add_argument("-r", "--red",     dest="red_coef",    type=float, default=0.05)
    p.add_argument("-g", "--green",   dest="green_coef",  type=float, default=0.05)
    p.add_argument("-b", "--blue",    dest="blue_coef",   type=float, default=0.05)

    p.add_argument("--ingest_id",     dest="ingest_id",   default=None,
                   help="UUID del producto original para ingestar derivados en catálogo")
    p.add_argument("--product_list",  dest="product_list",
                   default="RGB1184 NDVIb",
                   help="Productos separados por espacio: RGB432 RGB1184 RGB1283 NDVI NDVIb")
    p.add_argument("--publish_list",  dest="publish_list",
                   default="NONE",
                   help="Productos a publicar separados por espacio, o NONE")
    p.add_argument("--product_folders", dest="product_folders",
                   action="store_true", default=False,
                   help="Guardar salidas en subcarpetas por tipo de producto")
    p.add_argument("--initial_date",  dest="initial_date", default=None)
    p.add_argument("--final_date",    dest="final_date",   default=None)
    p.add_argument("--date_field",    dest="date_field",   type=int, default=2)
    p.add_argument("--workspace",     dest="workspace",    type=int, default=None,
                   help="ID del workspace")
    p.add_argument("--delete_source", dest="delete_source",
                   action="store_true", default=False,
                   help="Eliminar el ZIP fuente tras procesar")
    p.add_argument("--config",        dest="config",       default=None,
                   help="Ruta al config.txt (se autodetecta si no se indica)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s -- %(message)s",
    )
    args = build_parser().parse_args(argv)

    if args.input_file:
        zip_files = [os.path.abspath(args.input_file)]
    else:
        zip_files = sorted(
            os.path.join(args.input_path, f)
            for f in os.listdir(args.input_path)
            if f.lower().endswith(".zip")
        )

    product_list = args.product_list.split()
    publish_list = (
        [] if args.publish_list.upper() in ("NONE", "")
        else args.publish_list.split()
    )

    initial_date = args.initial_date or "00000000"
    final_date   = args.final_date   or "30001231"

    errors = 0
    for zip_path in zip_files:
        fname = os.path.basename(zip_path)

        # Filtro por fecha
        if args.initial_date or args.final_date:
            parts = fname.split("_")
            if len(parts) > args.date_field:
                fdate = parts[args.date_field].split("T")[0]
                if not (initial_date <= fdate <= final_date):
                    logger.debug(f"Saltando {fname} por fecha ({fdate})")
                    continue

        try:
            process_zip(
                zip_path=zip_path,
                output_path=args.output_path,
                tmp_path=args.tmp_path,
                product_list=product_list,
                publish_list=publish_list,
                product_folders=args.product_folders,
                ingest_id=args.ingest_id,
                workspace_id=args.workspace,
                delete_source=args.delete_source,
                red_coef=args.red_coef,
                green_coef=args.green_coef,
                blue_coef=args.blue_coef,
                date_field=args.date_field,
                config_path=args.config,
            )
        except Exception as e:
            logger.error(f"Error procesando {fname}: {e}", exc_info=True)
            errors += 1

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
