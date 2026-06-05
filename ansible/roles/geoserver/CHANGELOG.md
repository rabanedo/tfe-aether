# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Implementación de barreras de idempotencia mediante el módulo `stat` para evitar redespliegues del archivo `.war`.
- Lógica de externalización atómica del directorio `data/` usando el módulo `shell` (`cp -rn`) para preservar configuraciones y metadatos (Zero Data-Loss).
- Inclusión dinámica de tareas (`install_extension.yml`) basada en bucles para desacoplar y modularizar la instalación de plugins (JARs).
- Manipulación segura de permisos en los binarios desempaquetados (`chown`) asignando propiedad al usuario del sistema Tomcat.
- Desarrollo de rutinas de *Health Check* en los *handlers* (`Wait for GeoServer`) que sondean el endpoint HTTP del servicio web usando `uri` con un temporizador activo (hasta 120 segundos) para asegurar que el contexto de Java ha arrancado por completo.
- Limpieza automatizada de los directorios de trabajo temporales (`/tmp`) post-ejecución.
