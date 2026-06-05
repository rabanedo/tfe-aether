# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Gestión integral de directorios temporales y persistentes para el código de publicación.
- Mecanismo de despliegue mediante `git clone` aislado y extracción eficiente con `ansible.posix.synchronize` del subárbol correspondiente a `aether-publish/`.
- Ajuste de permisos de ejecución para el script principal de ingesta (`run_publish.sh`).
- Despliegue dinámico y securizado de variables de entorno (`.env`) conteniendo rutas y credenciales de la API de GeoServer.
- Instalación y activación de unidades de Systemd:
  - `aether-publish.service`: Servicio `oneshot` con inyección directa del `.env` y canalización de salida hacia el `journal` del sistema.
  - `aether-publish.timer`: Temporizador tipo `cron` basado en `OnCalendar` para ejecuciones periódicas desfasadas del pipeline de procesado.
