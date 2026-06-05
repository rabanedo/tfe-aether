# Ansible Role: Aether API (Processing Node)

Este rol orquesta el despliegue de la aplicación base de Aether (FastAPI) y su motor de procesamiento de imágenes satelitales (Pipeline) en el nodo `aether-process`. Se encarga de clonar el código fuente, configurar los secretos y variables de entorno, y registrar la aplicación como un conjunto de servicios robustos en `systemd`.

## Descripción de la Arquitectura

El rol utiliza el módulo `synchronize` para extraer de forma limpia el código del subdirectorio del repositorio correspondiente. Las configuraciones sensibles (credenciales de BBDD, API Tokens y contraseñas de CDSE) se inyectan a través de plantillas Jinja2 securizadas (`no_log: true`). 
El rol configura el ecosistema base apoyándose fuertemente en el entorno de Conda previamente instalado, definiendo variables globales críticas (`PROJ_LIB`, `GDAL_DATA`) para garantizar la estabilidad geométrica de la librería GDAL. Finalmente, orquesta la ejecución a través de `systemd`, separando el proceso servidor (FastAPI) de las tareas programadas (Timer + Service del Pipeline).

## Requirements

* Git instalado en el nodo destino.
* Entorno virtual de Conda configurado (dependencia del rol `conda`).
* Acceso a los repositorios de GitHub/GitLab correspondientes.

## Role Variables

Variables clave requeridas por el rol (usualmente definidas en `group_vars/all/applications.yml` y `applications_encrypted.yml`):

```yaml
api_base_dir: "/opt/cdse-api"
api_repo_url: "[https://github.com/tu-usuario/aether.git](https://github.com/tu-usuario/aether.git)"
api_repo_version: "main"

api_dwh_directories:
  - "/warehouse/products/S2/original_products"
  - "/warehouse/products/S2/derived_products"

# Secretos (Deberían estar en Vault)
api_token: "super_secret_bearer_token"
catalog_username: "aether_user"
catalog_password: "..."
geoserver_username: "admin"
geoserver_password: "..."
