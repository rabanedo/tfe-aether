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
│  └──────────────┘    │  (catalog)       │               │
│                      └──────────────────┘               │
└─────────────────────────────────────────────────────────┘
                              │ productos GeoTIFF
┌─────────────────────────────▼───────────────────────────┐
│              NODO 2 — Servidor de Publicación           │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  GeoServer (sobre Apache Tomcat / OpenJDK)     │     │
│  │  WMS · WMTS · WCS (estándares OGC)             │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  PostgreSQL/PostGIS (almacén vectorial y meta) │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
          ▲
          │  WMS-T / WCS / WMTS
   ┌──────┴──────┐
   │ Clientes    │
   │ QGIS / Web  │
   └─────────────┘
```

---

## Funcionalidades Principales

### Pipeline automatizado (5 etapas secuenciales)

| Etapa | Servicio | Descripción |
|---|---|---|
| 1 | **FeedService** | Consulta la API CDSE y registra nuevos productos Sentinel-2 disponibles según la geometría, tipo de producto y rango temporal de cada workspace. |
| 2 | **CloudCoverageService** | Recupera el porcentaje de cobertura nubosa de cada producto vía OData de CDSE. Permite filtrar descargas por umbral de nubosidad. |
| 3 | **DownloadService** | Descarga los productos `.SAFE.zip` respetando el umbral de nubosidad configurado. Actualiza el catálogo e inicia la cola de procesamiento. |
| 4 | **ProcessService** | Ejecuta comandos de procesamiento configurable por workspace (generación de NDVI, RGB u otros índices) sobre los productos descargados. |
| 5 | **MosaicService** | Compone mosaicos multitile mediante GDAL (`BuildVRT` + `Translate`) cuando todos los tiles de un orbit/fecha están procesados. |

### API REST (FastAPI)

Cada etapa puede lanzarse individualmente o en conjunto a través de endpoints HTTP:

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/v1/health` | Estado del servicio |
| POST | `/api/v1/feeds/run` | Ejecuta FeedService |
| POST | `/api/v1/cloud/run` | Ejecuta CloudCoverageService |
| POST | `/api/v1/downloads/run` | Ejecuta DownloadService |
| POST | `/api/v1/processing/run` | Ejecuta ProcessService |
| POST | `/api/v1/mosaics/run` | Ejecuta MosaicService |
| POST | `/api/v1/pipeline/run` | Ejecuta el pipeline completo |

Todos los endpoints aceptan un payload JSON con parámetros opcionales:

```json
{
  "workspace_id": 1,
  "date": "2026-04-05",
  "orbit_id": 137,
  "limit": 10,
  "dry_run": false
}
```

### Publicación OGC

Los productos generados se publican en GeoServer como:
- **WMS / WMS-T** — visualización de capas raster por fecha
- **WMTS** — teselas en caché para visores web
- **WCS** — acceso a coberturas en bruto para análisis

---

## Instalación y Configuración

### Requisitos previos

- Ubuntu 26.04 LTS (o compatible)
- Miniconda3
- PostgreSQL 18+ con extensión PostGIS
- GeoServer 2.28+ sobre Tomcat 9 / OpenJDK 17 (Nodo 2)

### 1. Clonar el repositorio

```bash
git clone https://github.com/rabanedo/tfe-aether.git /opt/cdse-api
cd /opt/cdse-api
```

### 2. Crear el entorno Conda

```bash
conda create -p /opt/cdse-api/conda_envs/process_server python=3.11 -y
conda activate /opt/cdse-api/conda_envs/process_server

# Dependencias nativas (GDAL, PROJ, GEOS)
conda install -c conda-forge gdal proj geos -y

# Dependencias Python
pip install -r requirements.txt
```

### 3. Inicializar la base de datos

```bash
psql -U postgres -c "CREATE DATABASE aether;"
psql -U postgres -d aether -f catalog.sql
```

### 4. Configurar variables de entorno

Crea el fichero de entorno (nunca en el repositorio):

```bash
sudo vi /opt/cdse-api/.env
```

```dotenv
CDSE_CATALOG_USER=tu_usuario_postgres
CDSE_CATALOG_PASS=tu_contraseña_segura
CDSE_GEOSERVER_USER=tu_usuario_geoserver
CDSE_GEOSERVER_PASS=tu_contraseña_geoserver
```

```bash
sudo chmod 600 /opt/cdse-api/.env
```

### 5. Ajustar config.txt

Edita `/opt/cdse-api/config.txt` para apuntar la instancia de PostgreSQL y GeoServer. Los valores `${CDSE_*}` se resolverán automáticamente desde las variables de entorno definidas en el paso anterior:

```ini
catalog_db=aether
catalog_host=127.0.0.1
catalog_port=5432
catalog_user=${CDSE_CATALOG_USER}
catalog_pass=${CDSE_CATALOG_PASS}

geoserver_rest_url=http://<geoserver-host>:8080/geoserver/rest/...
geoserver_products_path=file:///almacen/data
geoserver_user=${CDSE_GEOSERVER_USER}
geoserver_pass=${CDSE_GEOSERVER_PASS}
```

### 6. Instalar los servicios systemd

```bash
sudo cp cdse-api.service     /etc/systemd/system/
sudo cp cdse-pipeline.service /etc/systemd/system/
sudo cp cdse-pipeline.timer   /etc/systemd/system/

# Añadir referencia al fichero de entorno en el unit:
# EnvironmentFile=/opt/cdse-api/.env

sudo systemctl daemon-reload
sudo systemctl enable --now cdse-api.service
sudo systemctl enable --now cdse-pipeline.timer
```

### 7. Verificar

```bash
# Estado del API
curl http://localhost:8080/api/v1/health

# Lanzar pipeline manualmente (dry-run)
BASE_URL=http://localhost:8080 PAYLOAD='{"dry_run": true}' bash run_jobs.sh
```

---

## Estructura del Proyecto

```
aether-process [/opt/cdse-api/]
│
├── app/
│   ├── api/
│   │   └── main.py                  # FastAPI — definición de endpoints
│   ├── core/
│   │   ├── config.py                # AppSettings (dataclass, os.getenv)
│   │   └── logging_config.py        # Configuración de logging
│   ├── models/
│   │   └── schemas.py               # Modelos Pydantic (RunRequest, JobResponse)
│   ├── repositories/
│   │   └── catalog_manager.py       # Acceso a BD (CatalogManager, CatalogConfig)
│   └── services/
│       ├── catalog_provider.py      # Context manager de sesión de catálogo
│       ├── cloud_service.py         # Etapa 2: cobertura nubosa vía OData CDSE
│       ├── download_service.py      # Etapa 3: descarga productos .SAFE.zip
│       ├── feed_service.py          # Etapa 1: consulta y registro de feeds CDSE
│       ├── mosaic_service.py        # Etapa 5: composición de mosaicos multitile
│       ├── pipeline_service.py      # Orquestador: ejecuta las 5 etapas
│       ├── process_service.py       # Etapa 4: procesamiento (NDVI, RGB, ...)
│       ├── rgb_ndvi.py              # Procesador de productos derivados Sentinel-2 (RGB y NDVI)
│       └── s2_processor.py          # Lógica GDAL: create_mosaic / is_mosaic_ready
│
├── db/
│   └── catalog.sql                  # DDL schema: tablas, índices, FKs, datos
│
├── scripts/
│   ├── run_api.sh                   # Arranca uvicorn en el entorno Conda
│   └── run_jobs.sh                  # Dispara el pipeline vía curl
│
├── systemd/
│   ├── cdse-api.service             # Unit del servidor FastAPI
│   ├── cdse-pipeline.service        # Unit del pipeline (one-shot)
│   └── cdse-pipeline.timer          # Timer diario para el pipeline
│
├── config.txt                       # Configuración de la plataforma (no secretos)
└── requirements.txt                 # Dependencias Python con versiones fijadas
```

---

## Stack Tecnológico

### Nodo 1 — Procesamiento

| Componente | Tecnología | Versión | Rol |
|---|---|---------|---|
| Lenguaje | Python | 3.11    | Servicios, scripts, API |
| API Framework | FastAPI | 0.136.1   | Endpoints REST del pipeline |
| Servidor ASGI | Uvicorn | 0.46.0    | Servidor de producción |
| Validación | Pydantic | 2.13.3    | Schemas de entrada/salida |
| BD relacional | PostgreSQL + PostGIS | 18+     | Catálogo de tareas y productos |
| Driver BD | psycopg2 | 2.9.12     | Conexión Python ↔ PostgreSQL |
| Datos CDSE | cdsetool | 0.3.1     | Descarga y consulta Sentinel-2 |
| HTTP | requests | 2.33.1    | Consulta OData nubosidad |
| Procesamiento ráster | GDAL / PROJ / GEOS | 3.8     | VRT, GeoTIFF, reproyección |
| Gestión entorno | Miniconda | —       | Aislamiento de dependencias |
| Init system | systemd | —       | Servicios y timer diario |
| IaC | Ansible | —       | Despliegue automatizado |

### Nodo 2 — Publicación

| Componente | Tecnología | Versión | Rol |
|---|---|---------|---|
| Servidor OGC | GeoServer | 2.28+   | WMS, WMTS, WCS |
| Contenedor Java | Apache Tomcat | 9       | Runtime de GeoServer |
| JVM | OpenJDK | 17      | Entorno de ejecución Java |
| BD relacional | PostgreSQL + PostGIS | 18+     | Metadatos vectoriales |

### Fuente de datos

| Fuente | Descripción |
|---|---|
| Copernicus Data Space Ecosystem (CDSE) | Productos Sentinel-2 L2A (corrección atmosférica BOA) |
| OData CDSE API | Atributos de producto (cloudCover, geometría, fechas) |

---

## Licencia

Este proyecto se presenta como Trabajo de Fin de Estudios con fines académicos y se distribuye bajo la licencia GNU GPL v3 [LICENSE](LICENSE). 
Se basa íntegramente en software libre. Para componentes de terceros, por favor consulte sus respectivos términos de licencia.