# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Despliegue de la plantilla `tomcat-users.xml.j2` con asignación completa de roles administrativos (`manager-gui`, `manager-script`, `manager-status`, `admin-gui`).
- Securización en tiempo de ejecución del volcado de logs (`no_log: true`) para evitar fugas de credenciales de administración.
- Disparador (`handler`) para reiniciar automáticamente el servicio de Tomcat en caso de que se detecten cambios en la configuración de usuarios.

### Removed
- (Refactorización): Se ha eliminado la lógica de montajes compartidos (`ansible.posix.mount`), delegando esta responsabilidad directamente a las directivas de la unidad de `systemd` (`BindPaths`) en el rol principal para mejorar el aislamiento del servicio y evitar ensuciar el `/etc/fstab`.
