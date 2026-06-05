# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Tarea para refrescar la caché de `apt` si tiene más de 3600 segundos de antigüedad.
- Tarea de actualización total del sistema mediante `upgrade: dist`, incluyendo `autoremove` y `autoclean` para liberar espacio.
- Instalación automatizada de dependencias definidas en la variable `apt_packages`.
- Comprobación del archivo `/var/run/reboot-required` para detectar actualizaciones de kernel o dependencias críticas.
- Reinicio automatizado y controlado mediante `ansible.builtin.reboot` con tiempos de espera configurados para restaurar la conexión tras el reinicio.
