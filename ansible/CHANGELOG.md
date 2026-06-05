# Changelog

Todos los cambios notables en el despliegue de Infraestructura como Código (IaC) de **Aether Platform** se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- **Arquitectura Base de IaC:**
  - Creación del `playbook.yml` principal con ejecución de tareas mediante `tags` semánticos.
  - Diseño de estructura Multi-Entorno (`development` / `production`) para un escalado predecible.
  - Implementación de `ansible.cfg` optimizado para alto rendimiento (`pipelining`, `ControlMaster`, y formateo de salida `yaml`).
  - Integración de `Ansible Vault` para la protección en reposo de las contraseñas, tokens y credenciales de la plataforma.

- **Roles de Sistema Operativo y Red:**
  - `system-update` y `system-config`: Preparación unificada del SO, gestión declarativa del usuario principal y rotación de bitácoras (`logrotate`).
  - `nfs-setup`: Creación de un Data Warehouse distribuido entre el nodo de cálculo (Server) y el nodo de visualización (Client).

- **Roles de Backend y Bases de Datos:**
  - `postgres`: Despliegue modular de PostgreSQL 18 y PostGIS 3. Renderización paramétrica de configuraciones DDL y asignación de RBAC adaptado a cada nodo (catálogo vs. índices cartográficos).
  - `conda`: Instalación idempotente de entornos virtuales aislados con resolución estricta de dependencias C++ espaciales (GDAL, PROJ).

- **Roles de Capa de Aplicación:**
  - `aether-api`: Orquestación de repositorios Git, variables de entorno securizadas, inyección de variables espaciales y servicios de orquestación `systemd`.
  - `tomcat` y `tomcat-config`: Instalación out-of-bounds del contenedor Java, tuning paramétrico del Garbage Collector (`G1GC`), y limitación de asignación de memoria. Delegación de aislamientos por volumen mediante `BindPaths` de systemd.
  - `geoserver` y `geoserver-config`: Despliegue dinámico de WAR, externalización atómica del directorio de datos, consumo de API REST para publicar *ImageMosaics* de series temporales y carga automatizada de estilos OGC (SLD).
  - `aether-publish`: Configuración de *Timers* nocturnos en el Nodo 2 para sincronización desatendida del DWH.
