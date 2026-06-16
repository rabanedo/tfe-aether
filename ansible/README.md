# Aether Ansible — Despliegue automatizado de la plataforma

Playbooks de Ansible para el despliegue completo de la plataforma **Aether** en sus dos nodos:

- **aether-process** (Nodo 1): Pipeline de descarga y procesamiento Sentinel-2.
- **aether-publish** (Nodo 2): Publicación de servicios OGC vía GeoServer.

---

## Estructura

```
ansible/
├── playbook.yml                         # Playbook principal de despliegue
├── ansible.cfg                          # Configuración del motor de Ansible
├── .gitignore
│
├── global_vars/
│   ├── applications.yml                 # Variables globales no sensibles
│   └── applications_encrypted.yml       # Variables sensibles (cifradas con Vault)
│
├── environments/
│   ├── development/
│   │   ├── hosts.ini                    # Inventario de desarrollo
│   │   ├── group_vars/all/
│   │   │   └── environment.yml          # Nombre del entorno
│   │   └── host_vars/
│   │       ├── aether-process/
│   │       │   ├── applications.yml     # Paquetes, rutas, parámetros Nodo 1
│   │       │   └── postgres.yml         # Configuración PostgreSQL Nodo 1
│   │       └── aether-publish/
│   │           ├── applications.yml     # Paquetes, bind mounts Nodo 2
│   │           ├── postgres.yml         # Configuración PostgreSQL Nodo 2
│   │           └── tomcat.yml           # Parámetros JVM y Catalina
│   └── production/                      # Misma estructura que development
│
└── roles/
    ├── system-update/                   # Actualización del sistema y paquetes base
    ├── system-config/                   # Usuarios, directorios, logrotate
    ├── nfs-setup/                       # Configuración servidor y cliente NFSv4
    ├── postgres/                        # PostgreSQL 18 + PostGIS (ambos nodos)
    ├── conda/                           # Miniconda + GDAL/PROJ/GEOS (Nodo 1)
    ├── aether-api/                      # FastAPI + systemd pipeline (Nodo 1)
    ├── tomcat/                          # Apache Tomcat 9 (Nodo 2)
    ├── tomcat-config/                   # Usuarios manager, bind mounts
    ├── geoserver/                       # GeoServer 2.28 + extensiones (Nodo 2)
    ├── geoserver-config/                # Workspace, coveragestores, ImageMosaics
    └── aether-publish/                  # Script de publicación y timer (Nodo 2)
```

---

## Variables

### `global_vars/applications.yml` — Variables globales no sensibles

| Variable | Descripción |
|----------|-------------|
| `sys_user` / `sys_group` | Usuario y grupo del sistema para ambos nodos |
| `logs_path` | Ruta de logs (`/var/log/aether`) |
| `rotate_path` | Directorio de configuración de logrotate |
| `temp_path` | Ruta temporal de descarga de instaladores |
| `api_base_dir` | Directorio base del Nodo 1 (`/opt/cdse-api`) |
| `api_conda_env` | Nombre del entorno Conda |
| `api_conda_base` | Ruta de instalación de Miniconda |
| `api_port` | Puerto de la API FastAPI |
| `conda_packages` | Paquetes nativos conda (gdal, proj, geos) |
| `pip_packages` | Paquetes Python con versiones fijadas |
| `geoserver_version` | Versión de GeoServer a instalar |
| `geoserver_data_dir` | Directorio de datos externo de GeoServer |
| `geoserver_workspace` | Nombre del workspace OGC (`aether`) |
| `geoserver_stores` | Lista de coveragestores ImageMosaic |
| `geoserver_extensions` | Extensiones a instalar (imagepyramid, css) |
| `tomcat_version` | Versión de Apache Tomcat 9 |
| `tomcat_home` | Directorio de instalación de Tomcat |
| `java_version` | Versión de OpenJDK |
| `publish_base_dir` | Directorio base del Nodo 2 (`/opt/aether-publish`) |
| `publish_products_dir` | Directorio de productos GeoServer (`/dwh/data`) |

### `global_vars/applications_encrypted.yml` — Variables sensibles (Vault)

| Variable | Descripción |
|----------|-------------|
| `catalog_database` | Nombre de la BD del catálogo |
| `catalog_host` | Host de PostgreSQL Nodo 1 |
| `catalog_port` | Puerto de PostgreSQL |
| `catalog_username` | Usuario de BD del catálogo |
| `catalog_password` | Contraseña de BD del catálogo |
| `geoserver_db_name` | Nombre de la BD de GeoServer |
| `geoserver_db_user` | Usuario de BD de GeoServer |
| `geoserver_db_pass` | Contraseña de BD de GeoServer |
| `geoserver_username` | Usuario admin de GeoServer |
| `geoserver_password` | Contraseña admin de GeoServer |
| `geoserver_rest_url` | URL REST de GeoServer con placeholder `*coverage_name*` |
| `geoserver_products_path` | Ruta base de productos raster en Nodo 2 |
| `tomcat_admin` | Usuario del Tomcat Manager |
| `tomcat_admin_password` | Contraseña del Tomcat Manager |
| `sys_uid` / `sys_gid` | UID/GID del usuario `aether` |

### `environments/<env>/host_vars/aether-process/`

| Fichero | Variable | Descripción |
|---------|----------|-------------|
| `applications.yml` | `apt_packages` | Paquetes del sistema |
| `applications.yml` | `s2_process_command` | Ejecutable Python del entorno Conda |
| `applications.yml` | `s2_process_params` | Productos a generar (`RGB1184 NDVIb`) |
| `applications.yml` | `s2_output_path` | Ruta de salida de productos derivados |
| `postgres.yml` | `install_postgres` | Bool — instalar PostgreSQL en este nodo |
| `postgres.yml` | `db_name` | Nombre de la BD |
| `postgres.yml` | `sql_schema_file` | Ruta al fichero SQL de esquema |

### `environments/<env>/host_vars/aether-publish/`

| Fichero | Variable | Descripción |
|---------|----------|-------------|
| `applications.yml` | `apt_packages` | Paquetes del sistema |
| `applications.yml` | `bind_mounts` | Lista de bind mounts src→dst |
| `postgres.yml` | `install_postgres` | Bool — instalar PostgreSQL en este nodo |
| `postgres.yml` | `sql_schema_file` | Ruta al SQL del esquema GeoServer |
| `tomcat.yml` | `catalina_home` / `catalina_base` | Rutas de Catalina |
| `tomcat.yml` | `xms` / `xmx` | Heap JVM inicial y máximo |

---

## Requisitos previos

```bash
# En el nodo de control (máquina orquestadora)
pip install ansible

# Verificar versión (>= 2.15 recomendado)
ansible --version

# Establecer confianza SSH sin contraseña hacia los nodos destino
ssh-copy-id <usuario>@<IP_NODO1>
ssh-copy-id <usuario>@<IP_NODO2>
```

---

## Configuración inicial

### 1. Ajustar el inventario

Edita `environments/production/hosts.ini` con las IPs y credenciales reales:

```ini
[aether_process]
aether-process ansible_host=192.168.1.221 ansible_user=ubuntu

[aether_publish]
aether-publish ansible_host=192.168.1.222 ansible_user=ubuntu
```

### 2. Configurar variables del entorno

Edita los ficheros en `environments/production/host_vars/` con las rutas y parámetros específicos de tu instalación.

### 3. Configurar y cifrar los secretos

Copia la plantilla de variables sensibles y rellena los valores reales:

```bash
cp global_vars/applications_encrypted.yml global_vars/applications_encrypted.yml.bak
nano global_vars/applications_encrypted.yml
```

Cifra el fichero con Ansible Vault:

```bash
ansible-vault encrypt global_vars/applications_encrypted.yml
# Introduce y confirma la contraseña del vault
```

Para no introducir la contraseña en cada ejecución, guárdala en un fichero local (excluido del repositorio por `.gitignore`):

```bash
echo "mi_contraseña_vault" > .vault_pass
chmod 600 .vault_pass
```

---

## Ejecución

### Despliegue completo de ambos nodos

```bash
ansible-playbook playbook.yml \
  -i environments/production/hosts.ini \
  --vault-password-file .vault_pass
```

### Despliegue de un rol concreto (con tags)

```bash
# Solo actualizar sistema
ansible-playbook playbook.yml -i environments/production/hosts.ini \
  --vault-password-file .vault_pass --tags system-update

# Solo Nodo 1 completo (Conda + API)
ansible-playbook playbook.yml -i environments/production/hosts.ini \
  --vault-password-file .vault_pass --tags "conda,aether-api"

# Solo GeoServer
ansible-playbook playbook.yml -i environments/production/hosts.ini \
  --vault-password-file .vault_pass --tags geoserver

# Solo script de publicación
ansible-playbook playbook.yml -i environments/production/hosts.ini \
  --vault-password-file .vault_pass --tags aether-publish
```

### Verificar sin ejecutar (dry-run)

```bash
ansible-playbook playbook.yml \
  -i environments/production/hosts.ini \
  --vault-password-file .vault_pass \
  --check --diff
```

### Comprobar conectividad con los nodos

```bash
ansible all -i environments/production/hosts.ini -m ping
```

---

## Tags disponibles

| Tag | Roles ejecutados | Nodo(s) |
|-----|------------------|---------|
| `system-update` | system-update | Ambos |
| `system-config` | system-config | Ambos |
| `nfs-setup` | nfs-setup | Ambos |
| `postgres` | postgres | Ambos |
| `conda` | conda | aether-process |
| `aether-api` | conda, aether-api | aether-process |
| `tomcat` | tomcat, tomcat-config | aether-publish |
| `geoserver` | tomcat-config, geoserver, geoserver-config | aether-publish |
| `aether-publish` | aether-publish | aether-publish |

---

## Gestión del vault

```bash
# Ver contenido cifrado
ansible-vault view global_vars/applications_encrypted.yml

# Editar en caliente
ansible-vault edit global_vars/applications_encrypted.yml

# Cambiar contraseña del vault
ansible-vault rekey global_vars/applications_encrypted.yml

# Descifrar temporalmente (no recomendado en producción)
ansible-vault decrypt global_vars/applications_encrypted.yml
```

---

## Stack desplegado

### Nodo 1 — aether-process

| Componente | Versión |
|------------|---------|
| Ubuntu | 26.04 LTS |
| Python (Conda) | 3.11 |
| FastAPI | 0.136.1 |
| Uvicorn | 0.46.0 |
| Pydantic | 2.13.3 |
| psycopg2-binary | 2.9.12 |
| cdsetool | 0.3.1 |
| requests | 2.33.1 |
| GDAL / PROJ / GEOS | conda-forge latest |
| PostgreSQL + PostGIS | 18 |

### Nodo 2 — aether-publish

| Componente | Versión |
|------------|---------|
| Ubuntu | 26.04 LTS |
| Python (sistema) | 3.12 |
| python3-requests | sistema |
| OpenJDK | 17 |
| Apache Tomcat | 9.0.118 |
| GeoServer | 2.28.4 |
| PostgreSQL + PostGIS | 18 |