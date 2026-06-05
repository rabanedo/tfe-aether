# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Descarga segura de la llave GPG de PostgreSQL e integración del repositorio oficial PGDG.
- Instalación automatizada de PostgreSQL 18 y PostGIS 3.
- Creación de base de datos dedicada, usuario aplicativo y activación nativa de la extensión `postgis`.
- Despliegue de esquemas de datos (tablas, secuencias, primary keys e índices `GiST` espaciales) a través de archivos provistos por la variable `sql_schema_file`.
- Aplicación estricta del principio de mínimo privilegio (RBAC), limitando los permisos del usuario a acciones DML y creación en esquemas autorizados.
- Plantilla dinámica `pg_hba.conf.j2` configurada para exigir el cifrado criptográfico robusto `scram-sha-256` en todas las conexiones locales y de red de la aplicación.
- Tareas atómicas de creación y purga de directorios temporales para salvaguardar la higiene del sistema tras la inyección del esquema.
