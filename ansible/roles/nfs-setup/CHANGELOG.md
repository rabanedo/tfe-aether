# Changelog

Todos los cambios notables de este rol se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- Lógica de enrutamiento dinámico en `tasks/main.yml` basada en `inventory_hostname` para separar la ejecución entre Servidor y Cliente.
- Implementación del Servidor NFS (`server.yml`) en el nodo `aether-publish` con exportación del directorio `/dwh`.
- Configuración de exportación de NFS usando la directiva `no_root_squash` y `sync` para garantizar permisos adecuados y la integridad de los datos espaciales.
- Implementación del Cliente NFS (`client.yml`) en el nodo `aether-process` para la creación del punto de montaje `/warehouse`.
- Registro de persistencia automática en `/etc/fstab` a través del módulo `ansible.posix.mount` utilizando las opciones de resiliencia `hard` y `_netdev`.
- Inyección dinámica de direcciones IP utilizando el diccionario mágico `hostvars` de Ansible para independizar el código de la configuración de red estática.
