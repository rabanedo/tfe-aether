# Ansible Role: System Config

Este rol se encarga de la configuración base del sistema para la plataforma Aether. Su objetivo principal es el "scaffolding" o andamiaje del sistema operativo: creación de usuarios y grupos dedicados, generación de la estructura de directorios estándar y configuración de las políticas de rotación de logs.

## Requirements

* Sistema operativo Linux estándar.
* Ansible 2.9 o superior.

## Role Variables

Las variables disponibles permiten parametrizar los identificadores, usuarios y rutas base del sistema. Valores por defecto (ver `defaults/main.yml`):

```yaml
sys_user: aether_user
sys_uid: 1001
sys_group: aether_group
sys_gid: 1001
logs_path: /var/log/aether
rotate_path: /etc/logrotate.d