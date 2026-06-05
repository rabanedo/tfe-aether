# Changelog

Todos los cambios notables del proyecto **Aether Platform** se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-04

### Added
- **Arquitectura de Infraestructura como Código (IaC):**
  - Orquestación completa mediante Ansible (`playbook.yml`) para el aprovisionamiento Zero-Touch de nodos de procesamiento y publicación.
  - Implementación del patrón de Inventarios Múltiples (Multi-stage environments) aislando variables de `development` y `production`.
  - Configuración optimizada del motor Ansible (`pipelining=True`, `ControlMaster`, `stdout_callback=yaml`) para maximizar el rendimiento.

- **Almacenamiento Distribuido (NFS):**
  - Despliegue de un Data Warehouse centralizado basado en NFSv4 para la compartición transparente de imágenes satelitales (.SAFE y COG) entre el nodo de procesamiento (escritura) y el nodo de publicación (lectura).

- **Backend de Procesamiento (Nodo 1):**
  - Despliegue aislado de Python mediante Miniconda para garantizar la estabilidad de las librerías binarias geoespaciales (GDAL, PROJ).
  - Configuración de bases de datos relacionales PostgreSQL 18 + PostGIS para la gestión del catálogo de misiones y colas de tareas.
  - Generación de unidades de Systemd (`cdse-api.service`, `cdse-pipeline.timer`) para la ejecución programada de la API FastAPI.

- **Motor Cartográfico (Nodo 2):**
  - Instalación y tuning de máquina virtual Java (OpenJDK 17 + G1GC) y contenedor de Servlets Apache Tomcat 9.
  - Despliegue automatizado de GeoServer 2.28.
  - Consumo dinámico de la API REST de GeoServer para la inicialización y publicación declarativa de *ImageMosaics* apoyados por índices temporales en PostGIS.
  - Vinculación automatizada de estilos OGC (SLD) para productos de vegetación (NDVI) y falso color (RGB1184).

### Security
- Aislamiento estricto de secretos, contraseñas de BBDD, API Tokens y credenciales de Copernicus CDSE mediante **Ansible Vault** (`applications_encrypted.yml`).
- Implementación de directivas `no_log: true` en la renderización de plantillas sensibles.
- Aplicación de Principle of Least Privilege (PoLP) separando los UID/GID del sistema operativo (`sys_user`) de los de base de datos (`postgres`).
