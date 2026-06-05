# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-05

### Added
- Implementación de sondeo (*polling*) activo mediante el módulo `uri` para detener la ejecución hasta que GeoServer finalice su secuencia de arranque.
- Creación idempotente del espacio de trabajo (`workspace`) principal de la plataforma.
- Generación de jerarquías de directorios físicos para los almacenes raster.
- Despliegue de plantillas (`datastore.properties.j2`) y configuración paramétrica (`indexer.properties`, `timeregex.properties`) para habilitar *ImageMosaics* indexados en PostGIS con soporte para la dimensión Tiempo (`TimeAttribute=ingestion`).
- Lógica de purga automática de tablas de índices en PostgreSQL (módulo `postgresql_table`) en caso de discrepancia de estado con GeoServer.
- Consumo dinámico de la API REST para la inicialización (`PUT`) de almacenes externos y la publicación (`POST`) de *coverages*.
- Subida de ficheros de estilo OGC SLD estáticos (`sld_ndvi.sld`, `sld_rgb1184.sld`) y vinculación automatizada como estilos predeterminados a sus respectivas capas mediante peticiones `PUT`.
