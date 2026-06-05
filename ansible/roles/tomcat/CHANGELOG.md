# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Gestión atómica de directorios temporales para la descarga de binarios.
- Instalación automatizada del Java Development Kit (OpenJDK) mediante APT.
- Despliegue de Apache Tomcat desde fuentes oficiales (tarball) con validación de idempotencia (`stat` y `creates`).
- Implementación de patrón de enlace simbólico (`/opt/tomcat` -> `/opt/apache-tomcat-X.X.X`) para abstraer la versión de las rutas de ejecución.
- Creación y asignación de permisos seguros para el directorio externo de datos de GeoServer (`GEOSERVER_DATA_DIR`).
- Inyección de la plantilla `setenv.sh.j2` con variables de entorno críticas y sintonización de la JVM (`-Xms`, `-Xmx`, `-XX:+UseG1GC`, y soporte *headless*).
- Creación de unidad demonio `tomcat9.service` en Systemd con soporte de dependencias de arranque (`After=network.target postgresql.service`), soporte `Type=forking` e inyección opcional de montajes virtuales (`BindPaths`).
