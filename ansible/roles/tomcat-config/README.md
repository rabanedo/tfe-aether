# Ansible Role: Tomcat Config

Este rol gestiona la configuración de post-instalación de Apache Tomcat. Su principal objetivo es inyectar la configuración de seguridad y acceso administrativo (`tomcat-users.xml`) de forma automatizada y protegida para el entorno Aether.

## Descripción de la Arquitectura

A diferencia de la instalación base (gestionada por el rol `tomcat`), este rol se centra exclusivamente en la capa de configuración aplicativa. Utiliza el módulo de plantillas de Ansible para definir dinámicamente los roles (`manager-gui`, `admin-gui`, etc.) y las credenciales de administración.

**Nota de Seguridad:** Las credenciales se inyectan utilizando la directiva `no_log: true` de Ansible, garantizando que ninguna contraseña ni dato sensible quede registrado en los logs de la consola o del sistema de Integración Continua (CI/CD).

## Requirements

* El rol `tomcat` debe haberse ejecutado previamente para garantizar la existencia de las rutas base (`{{ catalina_home }}`) y el usuario del sistema.

## Role Variables

Variables requeridas para la configuración de accesos (se recomiendan almacenar en Ansible Vault):

```yaml
tomcat_admin: "admin"
tomcat_admin_password: "super_secret_password"

# Variables heredadas del rol base o inventario
catalina_home: "/opt/tomcat"
sys_user: "aether_user"
sys_group: "aether_group"
