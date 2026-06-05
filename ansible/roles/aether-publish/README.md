# Ansible Role: Aether Publish (Node 2)

Este rol despliega el componente de sincronización y publicación cartográfica en el nodo `aether-publish`. Su función principal es orquestar los *scripts* que escanean el *Data Warehouse* en busca de nuevos productos satelitales (procesados previamente por el nodo 1) y actualizar dinámicamente los *ImageMosaics* en GeoServer.

## Descripción de la Arquitectura

Para asegurar despliegues limpios, el rol clona el repositorio oficial de la plataforma y utiliza el módulo `synchronize` para extraer únicamente el código necesario del subdirectorio `aether-publish/`.
Las configuraciones críticas para atacar la API REST de GeoServer se inyectan de forma segura en un archivo `.env` restringido.
El ciclo de ejecución está completamente desatendido y gobernado por **Systemd**, utilizando una arquitectura de `Timer` + `Service (oneshot)`. El temporizador está programado en ventana nocturna (`06:00:00`), garantizando que la ingesta se realice una vez finalizados los procesos pesados de descarga y cálculo en el nodo de procesamiento.

## Requirements

* Git instalado en el nodo de publicación.
* Servicio GeoServer y Tomcat en ejecución (rol `geoserver-config`).
* Acceso de lectura/escritura al NFS o almacenamiento compartido donde residen las imágenes.

## Role Variables

Variables clave requeridas por el rol (ver `defaults/main.yml`):

```yaml
publish_base_dir: "/opt/cdse-publish"
api_repo_url: "[https://github.com/tu-usuario/aether.git](https://github.com/tu-usuario/aether.git)"
api_repo_version: "main"

# Integración REST GeoServer
geoserver_rest_url: "http://localhost:8080/geoserver/rest"
geoserver_products_path: "/opt/geoserver_data/data/aether"
geoserver_username: "admin"
geoserver_password: "..."
