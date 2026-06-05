# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Creación de grupo del sistema (`sys_group`) con GID específico para asegurar consistencia entre nodos.
- Creación de usuario del sistema (`sys_user`) con UID específico y directorio *home*.
- Creación de árbol de directorios para almacenamiento de logs y archivos temporales con permisos estrictos (0755) vinculados al usuario del sistema.
- Despliegue de la plantilla `logrotate-aether.j2` para gestionar la rotación automática de los ficheros de log de la plataforma.
