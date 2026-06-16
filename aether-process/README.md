# Aether Process — Nodo 1: Servidor de Procesamiento

Componente de ingesta y procesamiento de la plataforma **Aether**. Descarga periódicamente productos Sentinel-2 desde el Copernicus Data Space Ecosystem (CDSE), genera índices de vegetación (NDVI) y composiciones RGB como Cloud Optimized GeoTIFF (COG), y los pone a disposición del Nodo 2 para su publicación OGC.

---

## Descripción funcional

`aether-process` expone una **API REST** (FastAPI / Uvicorn) que orquesta un pipeline de 5 etapas secuenciales. Un timer systemd diario dispara el pipeline de forma desatendida; alternativamente, cada etapa puede lanzarse de forma individual mediante llamadas HTTP, lo que facilita la depuración y la reejección selectiva de pasos.

El pipeline registra el estado de cada producto en un catálogo PostgreSQL/PostGIS y deposita los GeoTIFF resultantes en un almacén en disco, accesible desde el Nodo 2 mediante bind mounts NFS.

---

## Requisitos previos

| Componente | Versión | Notas |
|------------|---------|-------|
| Ubuntu | 26.04 LTS | |
| Python (Conda) | 3.11 | Gestionado con Miniconda |
| Miniconda3 | — | Aislamiento de dependencias nativas |
| GDAL / PROJ / GEOS | 3.8 (conda-forge) | Procesamiento ráster |
| PostgreSQL + PostGIS | 18+ | Catálogo de tareas y productos |
| systemd | — | Servicio API y timer del pipeline |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/rabanedo/tfe-aether.git
sudo mkdir -p /opt/cdse-api
sudo cp -r tfe-aether/aether-process/* /opt/cdse-api/
sudo chown -R aether:aether /opt/cdse-api
```

### 2. Crear el entorno Conda

```bash
conda create -p /opt/cdse-api/conda_envs/process_server python=3.11 -y
conda activate /opt/cdse-api/conda_envs/process_server

# Dependencias nativas (GDAL, PROJ, GEOS)
conda install -c conda-forge gdal proj geos -y

# Dependencias Python
pip install -r /opt/cdse-api/requirements.txt
```

### 3. Inicializar la base de datos

```bash
psql -U postgres -c "CREATE DATABASE aether;"
psql -U postgres -d aether -f /opt/cdse-api/db/catalog.sql
```

El esquema `catalog.sql` crea todas las tablas, índices y claves foráneas necesarias, incluida la tabla de workspaces con los parámetros de procesamiento por zona de interés.

### 4. Configurar variables de entorno

Crea el fichero de entorno (nunca versionar en el repositorio):

```bash
sudo vi /opt/cdse-api/.env
sudo chmod 600 /opt/cdse-api/.env
sudo chown root:root /opt/cdse-api/.env
```

Contenido de `.env`:

```ini
CDSE_CATALOG_USER=tu_usuario_postgres
CDSE_CATALOG_PASS=tu_contraseña_segura
CDSE_GEOSERVER_USER=tu_usuario_geoserver
CDSE_GEOSERVER_PASS=tu_contraseña_geoserver
```

### 5. Ajustar `config.txt`

Edita `/opt/cdse-api/config.txt`. Los valores `${CDSE_*}` se resuelven automáticamente desde el fichero `.env` cargado por systemd:

```ini
catalog_db=aether
catalog_host=127.0.0.1
catalog_port=5432
catalog_user=${CDSE_CATALOG_USER}
catalog_pass=${CDSE_CATALOG_PASS}

# URL REST de GeoServer con placeholder *coverage_name*
geoserver_rest_url=http://<geoserver-host>:8080/geoserver/rest/workspaces/aether/coveragestores/*coverage_name*/external.imagemosaic
geoserver_products_path=file:///dwh/data
geoserver_user=${CDSE_GEOSERVER_USER}
geoserver_pass=${CDSE_GEOSERVER_PASS}
```

### 6. Instalar los servicios systemd

```bash
sudo cp /opt/cdse-api/systemd/cdse-api.service      /etc/systemd/system/
sudo cp /opt/cdse-api/systemd/cdse-pipeline.service  /etc/systemd/system/
sudo cp /opt/cdse-api/systemd/cdse-pipeline.timer    /etc/systemd/system/
```

Asegúrate de que cada unit cargue el fichero de entorno:

```ini
# Añadir en la sección [Service] de cada unit:
EnvironmentFile=/opt/cdse-api/.env
```

Habilita e inicia:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cdse-api.service
sudo systemctl enable --now cdse-pipeline.timer
```

### 7. Verificar

```bash
# Estado del API
curl http://localhost:8080/api/v1/health

# Lanzar pipeline completo en dry-run
BASE_URL=http://localhost:8080 bash /opt/cdse-api/scripts/run_jobs.sh --dry-run
```

---

## API REST

Todos los endpoints aceptan un payload JSON con los parámetros opcionales indicados a continuación:

```json
{
  "workspace_id": 1,
  "date": "2026-04-05",
  "orbit_id": 137,
  "limit": 10,
  "dry_run": false
}
```

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/health` | Estado del servicio |
| POST | `/api/v1/feeds/run` | Ejecuta FeedService (etapa 1) |
| POST | `/api/v1/cloud/run` | Ejecuta CloudCoverageService (etapa 2) |
| POST | `/api/v1/downloads/run` | Ejecuta DownloadService (etapa 3) |
| POST | `/api/v1/processing/run` | Ejecuta ProcessService (etapa 4) |
| POST | `/api/v1/mosaics/run` | Ejecuta MosaicService (etapa 5) |
| POST | `/api/v1/pipeline/run` | Ejecuta el pipeline completo (etapas 1–5) |

---

## Pipeline de procesamiento

### Etapas secuenciales

| Etapa | Servicio | Descripción |
|-------|----------|-------------|
| 1 | **FeedService** | Consulta la API CDSE y registra en el catálogo los nuevos productos Sentinel-2 disponibles según la geometría, tipo de producto y rango temporal configurados en cada workspace. |
| 2 | **CloudCoverageService** | Recupera el porcentaje de cobertura nubosa de cada producto vía OData de CDSE. Permite filtrar descargas por umbral de nubosidad. |
| 3 | **DownloadService** | Descarga los productos `.SAFE.zip` que no superan el umbral de nubosidad configurado. Actualiza el catálogo e inicia la cola de procesamiento. |
| 4 | **ProcessService** | Ejecuta el comando de procesamiento configurado por workspace (`s2_process_command`). Por defecto invoca `rgb_ndvi.py`, que descomprime el `.SAFE.zip`, extrae las bandas necesarias y genera los productos derivados configurados (`RGB1184`, `NDVIb`, etc.) como COG en EPSG:25830. Los productos generados se ingresan en el catálogo y pasan a la cola de mosaicos. |
| 5 | **MosaicService** | Compone mosaicos multitile mediante GDAL (`BuildVRT` + `Translate`) cuando todos los tiles de un orbit/fecha están procesados. |

### Productos derivados generados por `rgb_ndvi.py`

| Código | Descripción | Bandas S2 | Tipo | Compresión COG |
|--------|-------------|-----------|------|----------------|
| `RGB432` | Composición color verdadero | B4, B3, B2 (10 m) | Byte | JPEG |
| `RGB1184` | Composición falso color (vegetación) | B11, B8, B4 | Byte | JPEG |
| `RGB1283` | Composición falso color (urbano) | B12, B8, B3 | Byte | JPEG |
| `NDVI` | Índice de vegetación Float32 (−1 a +1) | B8, B4 | Float32 | DEFLATE PREDICTOR=3 |
| `NDVIb` | NDVI escalado a Byte (0–100, NoData=255) | B8, B4 | Byte | LZW PREDICTOR=2 |

El conjunto activo por defecto es `RGB1184 NDVIb`. Se configura en la columna `s2_process_params` del workspace en la base de datos.

---

## Estructura del proyecto

```
aether-process/  [instalado en /opt/cdse-api/]
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
│       ├── rgb_ndvi.py              # Procesador de productos derivados Sentinel-2
│       └── s2_processor.py          # Lógica GDAL: create_mosaic / is_mosaic_ready
│
├── db/
│   └── catalog.sql                  # DDL schema: tablas, índices, FKs, datos iniciales
│
├── scripts/
│   ├── run_api.sh                   # Arranca uvicorn en el entorno Conda
│   └── run_jobs.sh                  # Dispara el pipeline completo vía curl
│
├── systemd/
│   ├── cdse-api.service             # Unit del servidor FastAPI
│   ├── cdse-pipeline.service        # Unit del pipeline (one-shot)
│   └── cdse-pipeline.timer          # Timer diario para el pipeline
│
├── config.txt                       # Configuración de la plataforma (sin secretos)
└── requirements.txt                 # Dependencias Python con versiones fijadas
```

---

## Automatización con systemd

El timer `cdse-pipeline.timer` lanza el pipeline diariamente de forma desatendida:

```ini
# cdse-pipeline.timer
[Timer]
OnCalendar=*-*-* 01:30:00
Persistent=true
```

El servicio `cdse-api.service` mantiene el servidor FastAPI activo de forma permanente para permitir también disparos manuales o desde otros sistemas.

Consultar logs:

```bash
# Logs del API
journalctl -u cdse-api.service -f

# Logs del pipeline
journalctl -u cdse-pipeline.service --since today
```

---

## Stack tecnológico

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
| Init system | systemd | — | Servicio API y timer diario |
| IaC | Ansible | — | Despliegue automatizado |
