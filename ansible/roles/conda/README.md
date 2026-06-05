# Ansible Role: Conda

Este rol instala Miniconda y orquesta el entorno virtual de Python necesario para la ejecución del pipeline de procesamiento y la API en el nodo `aether-process`. Garantiza una instalación idempotente y mantiene el entorno sincronizado de forma declarativa.

## Descripción de la Arquitectura

El rol utiliza el gestor de paquetes de Conda para crear un entorno aislado (`{{ api_conda_env }}`). Se emplea la bandera `--prune` durante la actualización para asegurar que el estado del servidor refleje exactamente las dependencias definidas en la plantilla, eliminando automáticamente cualquier paquete huérfano o no deseado. Además, configura el perfil de usuario (`.bashrc`) para que el entorno esté siempre activo por defecto en las sesiones interactivas y servicios orquestados.

## Requirements

* Sistema operativo basado en Linux.
* Acceso a internet para la descarga del instalador y los paquetes desde los repositorios de Conda/Anaconda.

## Role Variables

Variables principales utilizadas por el rol (se recomiendan definir a nivel global o en `defaults/main.yml`):

```yaml
sys_user: "aether_user"
sys_group: "aether_group"
temp_path: "/tmp/aether_conda"

api_conda_base: "/opt/miniconda3"
api_conda_env: "cdse-api"
conda_installer_url: "[https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh)"
conda_terms: 
  - "conda-forge"
