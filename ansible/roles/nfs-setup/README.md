# Ansible Role: NFS Setup

Este rol orquesta la capa de almacenamiento compartido (NFS) entre los nodos de la plataforma Aether. Implementa una arquitectura cliente-servidor dinámica basada en el inventario de Ansible, donde el nodo de publicación expone el almacenamiento y el nodo de procesamiento lo monta de forma persistente.

## Descripción de la Arquitectura

Para optimizar el rendimiento de lectura del servidor cartográfico (GeoServer), el disco físico reside en el nodo `publish`. El rol utiliza las variables mágicas de Ansible (`hostvars`) para resolver las direcciones IP dinámicamente, asegurando que el despliegue sea completamente agnóstico de la red subyacente. 

Además, se apoya en la coherencia de identidades (mismo UID/GID en ambos nodos) y en la directiva `no_root_squash` para evitar problemas de permisos cruzados sin comprometer la seguridad.

## Requirements

* Sistema operativo de la familia Debian/Ubuntu.
* Ansible 2.9 o superior.
* Es **altamente recomendable** que el rol `system-config` se haya ejecutado previamente en ambos nodos para garantizar que el usuario y grupo del sistema (`aether_user`:`aether_group`) existan con los mismos identificadores (UID/GID).

## Role Variables

Las variables principales definen las rutas de montaje y la resolución de IPs a través del inventario. Valores por defecto (ver `defaults/main.yml`):

```yaml
nfs_export_path: "/dwh"
nfs_mount_path: "/warehouse"

# Resolución dinámica de red mediante variables mágicas
nfs_server_ip: "{{ hostvars['aether-publish']['ansible_host'] }}"
nfs_allowed_clients: "{{ hostvars['aether-process']['ansible_host'] }}"

sys_user: "aether_user"
sys_group: "aether_group"
