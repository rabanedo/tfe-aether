# Ansible Role: Tomcat

Este rol automatiza la instalación y configuración de Apache Tomcat (Servidor de Aplicaciones Java) preparándolo específicamente para alojar el motor cartográfico GeoServer en el nodo `aether-publish`. Gestiona el ciclo de vida completo: desde la instalación del JDK subyacente hasta la sintonización de la JVM y la integración nativa con Systemd.

## Descripción de la Arquitectura

El rol utiliza un enfoque de instalación "Out of bounds" (descarga directa del `.tar.gz`) en lugar de los repositorios de APT. Esto permite controlar la versión exacta de Tomcat y mantener una estructura de directorios limpia a través de enlaces simbólicos (`symlinks`), facilitando futuras actualizaciones sin tiempo de inactividad (Zero-Downtime upgrades). 

Además, inyecta configuraciones avanzadas en la Máquina Virtual de Java (`setenv.sh`), activando el recolector de basura G1GC y estableciendo los límites de memoria necesarios para el procesamiento de imágenes TIFF masivas.

## Requirements

* Sistema operativo Linux (basado en Debian/Ubuntu para la instalación del JDK).
* Descarga autorizada desde los *mirrors* de Apache.

## Role Variables

Variables principales (ver `defaults/main.yml`):

```yaml
# Versiones y Rutas
java_version: "11"
tomcat_version: "9.0.87"
tomcat_name: "apache-tomcat-{{ tomcat_version }}"
tomcat_download_url: "[https://archive.apache.org/dist/tomcat/tomcat-9](https://archive.apache.org/dist/tomcat/tomcat-9)"

catalina_home: "/opt/tomcat"
catalina_base: "/opt/tomcat"
catalina_pid: "/opt/tomcat/temp/tomcat.pid"

# Configuración GeoServer
geoserver_data_dir: "/opt/geoserver_data"

# Tuning JVM
xms: "2G"
xmx: "4G"

# Systemd
tomcat_service: "tomcat9"
bind_mounts: [] # Lista de diccionarios {src: "...", dst: "..."} para aislamientos (opcional)
