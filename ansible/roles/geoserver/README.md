# Ansible Role: GeoServer

Este rol automatiza el despliegue del motor cartográfico GeoServer sobre un contenedor de Servlets Apache Tomcat. Gestiona la descarga del empaquetado Web Archive (`.war`), la externalización del directorio de datos para garantizar la persistencia, y la inyección dinámica de plugins o extensiones oficiales.

## Descripción de la Arquitectura

El rol garantiza la **idempotencia** comprobando la existencia previa del despliegue. Si es una instalación nueva, orquesta la extracción del WAR para que Tomcat lo despliegue y espera activamente a que se genere la carpeta `WEB-INF`. 
Posteriormente, separa el estado de la aplicación del binario, moviendo la carpeta `data/` hacia el directorio persistente (`geoserver_data_dir`) definido en el rol de Tomcat. Finalmente, realiza inyecciones de dependencias (JARs) descargando extensiones de la comunidad u oficiales (ej. `vectortiles`, `css`) e implementa un *Health Check* mediante llamadas HTTP para asegurar que el motor está levantado antes de continuar con la configuración.

## Requirements

* Servicio Apache Tomcat instalado y configurado (rol `tomcat`).
* Acceso a internet para descargar binarios desde SourceForge.

## Role Variables

Variables requeridas para el aprovisionamiento (definidas habitualmente en `defaults` o a nivel de inventario/grupo):

```yaml
geoserver_version: "2.25.0" # O la versión específica que estés usando
temp_path: "/tmp/aether_gs"
catalina_home: "/opt/tomcat"
geoserver_data_dir: "/opt/geoserver_data"
sys_user: "aether_user"
sys_group: "aether_group"
tomcat_service: "tomcat9"

# Lista de extensiones oficiales a descargar
geoserver_extensions:
  - "vectortiles"
  - "ysld"
