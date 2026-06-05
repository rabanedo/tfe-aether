# Ansible Role: GeoServer Config

Este rol orquesta la configuración aplicativa e integración de datos de GeoServer a través de su API REST. Configura el entorno de trabajo (Workspace), inicializa almacenes de datos tipo *ImageMosaic* respaldados por PostGIS para la gestión de series temporales, publica las capas (coverages) y asocia estilos cartográficos avanzados (SLD).

## Descripción de la Arquitectura

A diferencia de un despliegue manual, este rol automatiza la ingesta de repositorios de imágenes satelitales distribuidos. Inyecta los ficheros de configuración de GeoTools (`datastore.properties`, `indexer.properties`, `timeregex.properties`) directamente en el *Data Warehouse* (montado vía NFS) para delegar el indexado del mosaico a PostgreSQL. 

El rol gestiona el estado de forma declarativa: comprueba si las capas o los almacenes ya existen, purga índices obsoletos en la base de datos si hay discrepancias, y garantiza que las capas se publiquen con sus respectivas rampas de color y realces visuales (NDVI y Falso Color RGB) listos para su consumo vía WMS/WCS.

## Requirements

* GeoServer levantado y accesible.
* Base de datos PostgreSQL/PostGIS accesible (rol `postgres`).
* Almacenamiento persistente o compartido configurado (rol `nfs-setup`).

## Role Variables

Variables requeridas (definidas típicamente en `applications.yml` o `applications_encrypted.yml`):

```yaml
geoserver_workspace: "aether"
geoserver_products_path: "/opt/geoserver_data/data/aether"
geoserver_stores:
  - "s2ndvi"
  - "s2rgb"
  - "s2ndvi_mosaic"
  - "s2rgb_mosaic"

# Credenciales de acceso a GeoServer REST API
geoserver_username: "admin"
geoserver_password: "..."

# Conexión PostGIS para el indexador del ImageMosaic
catalog_host: "127.0.0.1"
catalog_port: 5432
geoserver_db_name: "aether_db"
geoserver_db_user: "aether_user"
geoserver_db_pass: "..."
