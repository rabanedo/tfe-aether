from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from cdsetool.query import geojson_to_wkt, query_features

from app.services.catalog_provider import catalog_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_attr(feed: dict, name: str, default=None):
    """Lee un atributo del bloque 'Attributes' del formato OData (si existe)."""
    for attr in feed.get("Attributes") or []:
        if attr.get("Name") == name:
            return attr.get("Value", default)
    return default


def _parse_name(name: str) -> dict:
    """
    Extrae sensor, orbit y tile del nombre del producto Sentinel-2.

    Ejemplo:
      S2B_MSIL2A_20260420T110619_N0512_R137_T30TTM_20260420T132449.SAFE
       0     1          2           3     4     5           6

    - parts[0] = 'S2B'   → sensor 'Sentinel-2B'
    - parts[4] = 'R137'  → orbit  137
    - parts[5] = 'T30TTM'→ tile
    """
    clean = name.replace(".SAFE", "")
    parts = clean.split("_")
    sensor = ""
    orbit  = None
    tile   = ""

    if len(parts) > 0:
        raw = parts[0]           # 'S2A', 'S2B', 'S2C' ...
        # S2A -> Sentinel-2A
        if raw.startswith("S2"):
            sensor = f"Sentinel-{raw[1:]}"   # S2B -> Sentinel-2B

    if len(parts) > 4:
        raw_orbit = parts[4]     # 'R137'
        if raw_orbit.startswith("R") and raw_orbit[1:].isdigit():
            orbit = int(raw_orbit[1:])

    if len(parts) > 5:
        tile = parts[5]          # 'T30TTM'

    return {"sensor": sensor, "orbit": orbit, "tile": tile}


def _parse_feed(feed: dict) -> dict:
    """
    Devuelve un dict normalizado tanto si el item viene en formato
    GeoJSON antiguo (feed["properties"]) como en formato OData nuevo
    (feed["Id"], feed["Name"], ...).
    """
    # -- Formato GeoJSON (cdsetool < 0.6 aprox.) --------------------------
    if "properties" in feed:
        props = feed["properties"]
        title = props.get("title", "")
        parsed = _parse_name(title)
        return {
            "uuid":         feed["id"],
            "product_id":   title.rsplit(".", 1)[0],
            "title":        title,
            "published":    props.get("published"),
            "sensing_date": props.get("completionDate"),
            "cloud":        props.get("cloudCover"),
            "platform":     props.get("platform", parsed["sensor"]),
            "orbit":        props.get("relativeOrbitNumber", parsed["orbit"]),
            "tile":         parsed["tile"] or title.split("_")[-2],
            "geometry_wkt": geojson_to_wkt(feed["geometry"]),
        }

    # -- Formato OData (cdsetool >= 0.6) ----------------------------------
    name = feed.get("Name", "")
    parsed = _parse_name(name)

    # Geometría desde Footprint: "geography'SRID=4326;POLYGON (...)'"
    footprint = feed.get("Footprint") or ""
    if ";" in footprint:
        wkt = footprint.split(";", 1)[1].rstrip("'")
    else:
        # Fallback: reconstruir desde GeoFootprint si existe
        geo = feed.get("GeoFootprint")
        wkt = geojson_to_wkt(geo) if geo else footprint

    content_date = feed.get("ContentDate") or {}
    sensing_date = content_date.get("End") or content_date.get("Start")

    # cloudCover puede venir en Attributes (si la API lo incluye) o no venir
    cloud = _get_attr(feed, "cloudCover") or _get_attr(feed, "cloudCoverPercentage")

    return {
        "uuid":         feed.get("Id") or feed.get("id"),
        "product_id":   name.rsplit(".", 1)[0],
        "title":        name,
        "published":    feed.get("PublicationDate") or feed.get("OriginDate"),
        "sensing_date": sensing_date,
        "cloud":        cloud,           # None si la API no lo devuelve
        "platform":     parsed["sensor"],
        "orbit":        parsed["orbit"],
        "tile":         parsed["tile"],
        "geometry_wkt": wkt,
    }


# ---------------------------------------------------------------------------
# Service: Gestiona la búsqueda y sincronización de productos Sentinel en CDSE.
#          Normaliza datos de múltiples formatos (GeoJSON/OData) y registra
#          nuevas tareas de descarga en el catálogo local.
# ---------------------------------------------------------------------------

class FeedService:
    def run(
        self,
        workspace_id: int | None = None,
        date: str | None = None,
        orbit_id: int | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        inserted = 0
        scanned = 0

        with catalog_session() as catalog:
            workspaces = catalog.get_workspaces(workspace_id)

            for workspace in workspaces:
                if not workspace.get("active"):
                    continue

                if date:
                    init_day = dt.datetime.strptime(date, "%Y-%m-%d").date()
                    last_day = init_day + dt.timedelta(days=1)
                else:
                    last_day = dt.date.today()
                    init_day = last_day - dt.timedelta(
                        days=int(workspace["s2_time_range"] or 1)
                    )

                search_terms: dict[str, Any] = {
                    "contentDateStartGt": init_day.strftime("%Y-%m-%d"),
                    "contentDateEndLt":   last_day.strftime("%Y-%m-%d"),
                    "productType":        workspace["s2_product_type"],
                    "geometry":           workspace["wkt"],
                    "cloudCover":         "[0,100]",
                }
                if orbit_id:
                    search_terms["relativeOrbitNumberEq"] = orbit_id

                for feed in query_features(workspace["s2_collection"], search_terms):
                    scanned += 1

                    try:
                        item = _parse_feed(feed)
                    except Exception:
                        logger.exception("Cannot parse feed item: %s", feed)
                        continue

                    tile = item["tile"]
                    granules = workspace.get("s2_granules_list")
                    if granules and tile not in granules.split():
                        logger.debug("Skipping tile=%s not in granules_list", tile)
                        continue

                    logger.debug(
                        "Feed item: product_id=%s tile=%s sensor=%s orbit=%s cloud=%s",
                        item["product_id"], tile, item["platform"],
                        item["orbit"], item["cloud"],
                    )

                    if dry_run:
                        inserted += 1
                        continue

                    catalog.add_download_task(
                        uuid=item["uuid"],
                        workspace_id=workspace["id"],
                        product_id=item["product_id"],
                        ingestion_date=item["published"],
                        sensing_date=item["sensing_date"],
                        cloud_coverage=item["cloud"],
                        sensor=item["platform"],
                        orbit_number=item["orbit"],
                        tile_id=tile[1:],   # T30TTM -> 30TTM
                        tile_data_geometry=item["geometry_wkt"],
                    )
                    inserted += 1

        logger.info("FeedService.run inserted=%s scanned=%s", inserted, scanned)
        return {"inserted": inserted, "scanned": scanned, "dry_run": dry_run}
