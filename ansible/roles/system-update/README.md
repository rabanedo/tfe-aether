# Ansible Role: System Update

Este rol se encarga de realizar un mantenimiento base del sistema operativo (basado en Debian/Ubuntu). Actualiza la caché de repositorios, actualiza todos los paquetes del sistema (`dist-upgrade`), instala una lista de paquetes requeridos y, finalmente, comprueba si el sistema requiere un reinicio para aplicarlo automáticamente.

## Advertencia Importante de Ejecución (Reboot)

Este rol contiene una tarea que reinicia el servidor si detecta el archivo `/var/run/reboot-required`. 

**NUNCA ejecutes este rol si la máquina desde la que lanzas Ansible (Nodo de Control) está incluida en el inventario de destino.** Si el servidor se reinicia a sí mismo durante la ejecución, el proceso de Ansible morirá abruptamente, cortando la conexión y dejando el playbook sin terminar. 

Para ejecutar este rol de forma segura, el despliegue debe lanzarse siempre desde una tercera máquina (por ejemplo, tu equipo local, un servidor de CI/CD o un nodo bastión) que no sea objetivo de la actualización.

## Requirements

* Sistema operativo basado en la familia Debian (Ubuntu, Debian, etc.) compatible con el gestor de paquetes `apt`.
* Ansible 2.9 o superior.

## Role Variables

Las variables disponibles se enumeran a continuación, junto con sus valores por defecto (ver `defaults/main.yml`):

```yaml
apt_packages: []
