# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Creación y limpieza atómica de directorios temporales vinculados a la ejecución del rol.
- Descarga condicional e instalación silenciosa (`-b`) de Miniconda utilizando el módulo `stat` y validación `creates` para garantizar la idempotencia.
- Despliegue de la plantilla Jinja2 `mconda_env.yml.j2` con las dependencias del proyecto.
- Aceptación automatizada de los términos de servicio (TOS) para canales específicos.
- Actualización declarativa del entorno virtual de Conda utilizando el parámetro `--prune` para purgar dependencias desactualizadas o eliminadas de la plantilla.
- Inyección automatizada de la inicialización de Conda y la activación del entorno base en el archivo `.bashrc` del usuario del sistema.
