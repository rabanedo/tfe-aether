# Ansible Role: PostgreSQL

Este rol provisiona y configura un servidor de bases de datos PostgreSQL optimizado para operaciones geoespaciales. Instala el motor de base de datos, la extensión PostGIS, configura las políticas de acceso de red y despliega esquemas de datos automatizados (DDL/DML) utilizando plantillas dinámicas.

## Descripción de la Arquitectura

El rol añade el repositorio oficial PGDG (PostgreSQL Global Development Group) y su firma GPG para garantizar la integridad de los paquetes. Configura el acceso cliente-servidor en el archivo `pg_hba.conf` forzando la autenticación mediante el algoritmo seguro `scram-sha-256`. 
Además, el rol es capaz de recibir un archivo SQL (o plantilla Jinja2) para inicializar la base de datos de manera atómica, crear índices espaciales (`GiST`) y otorgar los permisos (RBAC) necesarios al usuario de la aplicación.

## Requirements

* Sistema operativo basado en la familia Debian/Ubuntu.
* Privilegios de superusuario (`become: true`).

## Role Variables

Variables disponibles (ver `defaults/main.yml` o inyectadas vía grupo):

```yaml
install_postgres: true
temp_path: "/tmp/aether"

# Credenciales y BBDD (Preferiblemente en Ansible Vault)
db_name: "aether_db"
db_schema: "public"
catalog_username: "aether_user"
catalog_password: "super_secret_password"

# Fichero de inicialización SQL
sql_schema_file: "aether-publish.sql.j2" # O una plantilla .sql.j2
