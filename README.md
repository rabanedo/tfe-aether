# Aether — Plataforma de Monitorización de Cultivos con Sentinel-2

> Trabajo de Fin de Estudios — Implementación de una plataforma distribuida para la monitorización automatizada de cultivos mediante Sentinel-2.

---

## Descripción

**Aether** es una plataforma software distribuida diseñada para la ingesta, procesamiento y publicación automatizada de imágenes Sentinel-2, orientada a la **agricultura de precisión**.

El sistema descarga periódicamente productos del programa Copernicus a través del [Copernicus Data Space Ecosystem (CDSE)](https://dataspace.copernicus.eu/), genera índices de vegetación (NDVI) y composiciones RGB, y los publica mediante estándares OGC (WMS, WMTS, WCS) a través de GeoServer. Esto permite a técnicos agrícolas y usuarios no expertos detectar de forma temprana anomalías en el vigor del cultivo o situaciones de estrés hídrico, consultando la información directamente desde QGIS o cualquier visor web compatible con OGC.

---

## Arquitectura

La plataforma se articula en **dos nodos desacoplados**, gestionados como Infraestructura como Código (IaC) mediante Ansible:

```
┌─────────────────────────────────────────────────────────┐
│              NODO 1 — Servidor de Procesamiento         │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  Timer       │    │        Aether API            │   │
│  │  systemd     │───▶│  (FastAPI / Uvicorn :8080)   │   │
│  │  (diario)    │    └──────────┬───────────────────┘   │
│  └──────────────┘               │                       │
│                         ┌───────▼────────┐              │
│                         │   Pipeline     │              │
│                         │  FeedService   │              │
│                         │  CloudService  │              │
│                         │  DownloadSvc   │              │
│                         │  ProcessSvc    │              │
│                         │  MosaicSvc     │              │
│                         └───────┬────────┘              │
│                                 │                       │
│  ┌──────────────┐    ┌──────────▼───────┐               │
│  │    CDSE API  │    │  PostgreSQL/     │               │
│  │  (Copernicus)│    │  PostGIS         │               │
│  └──────────────┘    │  (catálogo)      │               │
│                      └──────────────────┘               │
└─────────────────────────────────────────────────────────┘
                              │ productos GeoTIFF (NFS/bind mount)
┌─────────────────────────────▼───────────────────────────┐
│              NODO 2 — Servidor de Publicación           │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  GeoServer (sobre Apache Tomcat / OpenJDK)     │     │
│  │  WMS · WMTS · WCS (estándares OGC)             │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  aether-publish (Python + systemd)             │     │
│  │  Registra granulos en GeoServer vía REST API   │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  PostgreSQL/PostGIS (índice granulos GeoServer)│     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
          ▲
          │  WMS-T / WCS / WMTS
   ┌──────┴──────┐
   │  Clientes   │
   │  QGIS / Web │
   └─────────────┘
```

---

## Estructura del Repositorio

```
tfe-aether/
├── aether-process/          # Nodo 1: pipeline de descarga y procesamiento Sentinel-2
├── aether-publish/          # Nodo 2: publicación de productos en GeoServer
├── ansible/                 # IaC: playbooks y roles para despliegue automatizado
├── .gitignore
├── LICENSE
└── README.md                # Este fichero
```

Cada componente cuenta con su propio README detallado:

- [`aether-process/README.md`](aether-process/README.md) — Nodo 1: API, pipeline, instalación y configuración
- [`aether-publish/README.md`](aether-publish/README.md) — Nodo 2: publicación OGC en GeoServer
- [`ansible/README.md`](ansible/README.md) — Despliegue automatizado con Ansible

---

## Funcionalidades Principales

### Pipeline automatizado (5 etapas secuenciales)

| Etapa | Servicio | Descripción |
|-------|----------|-------------|
| 1 | **FeedService** | Consulta la API CDSE y registra nuevos productos Sentinel-2 disponibles según la geometría, tipo de producto y rango temporal de cada workspace. |
| 2 | **CloudCoverageService** | Recupera el porcentaje de cobertura nubosa de cada producto vía OData de CDSE. Permite filtrar descargas por umbral de nubosidad. |
| 3 | **DownloadService** | Descarga los productos `.SAFE.zip` respetando el umbral de nubosidad configurado. Actualiza el catálogo e inicia la cola de procesamiento. |
| 4 | **ProcessService** | Ejecuta el procesador configurable por workspace (`rgb_ndvi.py`): descomprime el `.SAFE.zip`, extrae bandas y genera productos derivados (RGB, NDVI) como Cloud Optimized GeoTIFF (COG) en EPSG:25830. |
| 5 | **MosaicService** | Compone mosaicos multitile mediante GDAL (`BuildVRT` + `Translate`) cuando todos los tiles de un orbit/fecha están procesados. |

### Productos derivados generados

| Código | Descripción | Bandas S2 | Tipo | Compresión COG |
|--------|-------------|-----------|------|----------------|
| `RGB432` | Composición color verdadero | B4, B3, B2 (10 m) | Byte | JPEG |
| `RGB1184` | Composición falso color (vegetación) | B11, B8, B4 | Byte | JPEG |
| `RGB1283` | Composición falso color (urbano) | B12, B8, B3 | Byte | JPEG |
| `NDVI` | Índice de vegetación Float32 (−1 a +1) | B8, B4 | Float32 | DEFLATE PREDICTOR=3 |
| `NDVIb` | NDVI escalado a Byte (0–100, NoData=255) | B8, B4 | Byte | LZW PREDICTOR=2 |

El conjunto de productos activo por defecto es `RGB1184 NDVIb`. Se configura mediante el parámetro `s2_process_params` del workspace en la base de datos.

### Publicación OGC

Los productos generados se publican en GeoServer (Nodo 2) como:

- **WMS / WMS-T** — visualización de capas raster con dimensión temporal
- **WMTS** — teselas en caché para visores web
- **WCS** — acceso a coberturas en bruto para análisis

---

## Stack Tecnológico

### Nodo 1 — Procesamiento (`aether-process`)

| Componente | Tecnología | Versión | Rol |
|------------|------------|---------|-----|
| Lenguaje | Python | 3.11 | Servicios, scripts, API |
| API Framework | FastAPI | 0.136.1 | Endpoints REST del pipeline |
| Servidor ASGI | Uvicorn | 0.46.0 | Servidor de producción |
| Validación | Pydantic | 2.13.3 | Schemas de entrada/salida |
| BD relacional | PostgreSQL + PostGIS | 18+ | Catálogo de tareas y productos |
| Driver BD | psycopg2 | 2.9.12 | Conexión Python ↔ PostgreSQL |
| Datos CDSE | cdsetool | 0.3.1 | Descarga y consulta Sentinel-2 |
| HTTP | requests | 2.33.1 | Consulta OData nubosidad |
| Procesamiento ráster | GDAL / PROJ / GEOS | 3.8 | VRT, GeoTIFF, reproyección |
| Gestión entorno | Miniconda | — | Aislamiento de dependencias |
| Init system | systemd | — | Servicios y timer diario |

### Nodo 2 — Publicación (`aether-publish`)

| Componente | Tecnología | Versión | Rol |
|------------|------------|---------|-----|
| Lenguaje | Python | 3.12 (sistema) | Script de publicación |
| HTTP | requests | 2.32+ | Llamadas REST a GeoServer |
| Servidor OGC | GeoServer | 2.28.4 | WMS, WMTS, WCS |
| Contenedor Java | Apache Tomcat | 9.0.118 | Runtime de GeoServer |
| JVM | OpenJDK | 17 | Entorno de ejecución Java |
| BD relacional | PostgreSQL + PostGIS | 18+ | Índice de granulos ImageMosaic |
| Init system | systemd | — | Timer de publicación periódica |

### IaC

| Componente | Tecnología | Rol |
|------------|------------|-----|
| Despliegue | Ansible | Aprovisionamiento automatizado de ambos nodos |
| Secretos | Ansible Vault | Cifrado de credenciales en repositorio |

### Fuente de datos

| Fuente | Descripción |
|--------|-------------|
| Copernicus Data Space Ecosystem (CDSE) | Productos Sentinel-2 L2A (corrección atmosférica BOA) |
| OData CDSE API | Atributos de producto (cloudCover, geometría, fechas) |

---

## Despliegue Rápido

El despliegue completo de ambos nodos se realiza mediante Ansible. Consulta [`ansible/README.md`](ansible/README.md) para los pasos detallados.

```bash
# Desde el nodo de control
ansible-playbook ansible/playbook.yml \
  -i ansible/environments/production/hosts.ini \
  --vault-password-file .vault_pass
```

Para instalación manual nodo a nodo:

- Nodo 1 → [`aether-process/README.md`](aether-process/README.md)
- Nodo 2 → [`aether-publish/README.md`](aether-publish/README.md)

---

## Licencia

Este proyecto se presenta como Trabajo de Fin de Estudios con fines académicos y se distribuye bajo la licencia **GNU GPL v3** — véase [LICENSE](LICENSE).  
Se basa íntegramente en software libre. Para componentes de terceros, consulte sus respectivos términos de licencia.