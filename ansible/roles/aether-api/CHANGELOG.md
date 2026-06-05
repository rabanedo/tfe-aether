# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Mecanismo de despliegue mediante `git clone` y filtrado con módulo `synchronize` hacia el directorio local destino.
- Asignación de permisos de ejecución escalonada para shell scripts (bash) y módulos de orquestación en Python.
- Despliegue dinámico y securizado (`no_log`) de credenciales usando la plantilla `config.txt.j2`.
- Despliegue de `.env` que mapea y estabiliza el entorno espacial inyectando las rutas de los compilados de `gdal` y `proj` desde la instalación de Conda.
- Creación automatizada del árbol de directorios del Data Warehouse (DWH) para la futura ingesta de los ficheros Sentinel-2.
- Registro y activación de unidades daemon de Systemd:
  - `cdse-api.service`: Servidor REST principal.
  - `cdse-pipeline.service`: Integración de cabeceras de autorización (`Bearer Token`) para el blindaje de la API interna.
  - `cdse-pipeline.timer`: Ejecución programada con control horario de la canalización de los datos.
- Manejo integral de limpieza y eliminación de artefactos temporales post-despliegue.
