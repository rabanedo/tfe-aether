# Aether Publish — Nodo 2: Servidor de Publicación

Componente de publicación de la plataforma **Aether**. Notifica a GeoServer vía REST API que registre cada nuevo GeoTIFF generado por el Nodo 1 como gránulo de un coveragestore ImageMosaic, haciéndolo disponible como servicio OGC (WMS-T / WMTS / WCS).

---

## Descripción funcional

`aether-publish` es un script Python ligero (`publish.py`) que recorre los directorios de productos generados por `aether-process` y, por cada fichero `.tif` no registrado aún, realiza una llamada `PUT` a la REST API de GeoServer para ingresarlo como gránulo en el ImageMosaic correspondiente. El script es invocado por un timer systemd sincronizado con el pipeline de procesamiento del Nodo 1.

No requiere Conda ni GDAL: el único paquete externo es `requests` para las llamadas REST.

---

## Requisitos previos

| Componente | Versión | Notas |
|------------|---------|-------|
| Ubuntu | 26.04 LTS | |
| Python | 3.12 (sistema) | Sin Conda — solo stdlib + `requests` |
| python3-requests | 2.32+ | `sudo apt install python3-requests` |
| GeoServer | 2.28.4 | Sobre Tomcat 9 / OpenJDK 17 |
| Apache Tomcat | 9.0.118 | Runtime de GeoServer |
| OpenJDK | 17 | Entorno de ejecución Java |
| PostgreSQL + PostGIS | 18+ | Índice de gránulos de GeoServer |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/rabanedo/tfe-aether.git
sudo mkdir -p /opt/aether-publish
sudo cp -r tfe-aether/aether-publish/* /opt/aether-publish/
sudo chown -R aether:aether /opt/aether-publish
```

### 2. Instalar dependencias

```bash
sudo apt install -y python3-requests
```

### 3. Preparar el almacén de productos

Los productos generados por el Nodo 1 se exponen al Nodo 2 mediante bind mounts, de forma que GeoServer accede a los ficheros sin copias adicionales.

Crea los puntos de montaje:

```bash
sudo mkdir -p /dwh/data/{s2ndvi,s2rgb,s2ndvi_mosaic,s2rgb_mosaic}
```

Añade los bind mounts en `/etc/fstab` para que sean persistentes tras reinicios:

```
# Aether — bind mounts productos S2 → directorios GeoServer
<ruta_productos>/NDVIb          /dwh/data/s2ndvi         none  bind  0 0
<ruta_productos>/RGB1184        /dwh/data/s2rgb          none  bind  0 0
<ruta_productos>/NDVIb_mosaic   /dwh/data/s2ndvi_mosaic  none  bind  0 0
<ruta_productos>/RGB1184_mosaic /dwh/data/s2rgb_mosaic   none  bind  0 0
```

```bash
sudo mount -a          # aplicar sin reiniciar
sudo findmnt --verify  # comprobar que no hay errores
```

### 4. Configurar variables de entorno

Copia la plantilla y rellena los valores reales:

```bash
sudo cp /opt/aether-publish/env.template /opt/aether-publish/.env
sudo nano /opt/aether-publish/.env
sudo chmod 600 /opt/aether-publish/.env
sudo chown root:root /opt/aether-publish/.env
```

Contenido de `.env`:

```ini
CDSE_GEOSERVER_USER=admin
CDSE_GEOSERVER_PASS=tu_contraseña_geoserver

# Endpoint para añadir gránulos a un ImageMosaic existente.
# *coverage_name* se sustituye en ejecución por: s2ndvi, s2rgb, s2ndvi_mosaic, s2rgb_mosaic
CDSE_GEOSERVER_REST_URL=http://localhost:8080/geoserver/rest/workspaces/aether/coveragestores/*coverage_name*/external.imagemosaic

# Directorio raíz que contiene los subdirectorios de productos
CDSE_GEOSERVER_PRODUCTS_PATH=/dwh/data
```

### 5. Inicializar la base de datos GeoServer

Crea las tablas de índice de gránulos que GeoServer usa para el ImageMosaic:

```bash
psql -U postgres -f /opt/aether-publish/aether_geoserver.sql
```

### 6. Configurar GeoServer

#### 6.1 Crear el workspace `aether`

```bash
curl -u admin:TU_PASSWORD \
  -XPOST -H "Content-Type: application/json" \
  -d '{"workspace": {"name": "aether"}}' \
  "http://localhost:8080/geoserver/rest/workspaces"
```

#### 6.2 Inicializar los coveragestores (solo la primera vez)

Este paso crea los coveragestores en GeoServer y publica la primera coverage de cada producto. Se ejecuta **una única vez**; las actualizaciones posteriores las gestiona `publish.py` automáticamente.

```bash
AUTH="admin:TU_PASSWORD"
GS="http://localhost:8080/geoserver/rest/workspaces/aether/coveragestores"

for STORE in s2ndvi s2rgb s2ndvi_mosaic s2rgb_mosaic; do
  echo "=== Inicializando $STORE ==="
  curl -s -w " → HTTP %{http_code}\n" -u "$AUTH" \
    -XPUT \
    -H "Content-Type: text/plain" \
    -d "file:///dwh/data/${STORE}" \
    "${GS}/${STORE}/external.imagemosaic"
done
# Respuesta esperada: HTTP 201 para cada store
```

#### 6.3 Verificar las coverages creadas

```bash
for STORE in s2ndvi s2rgb s2ndvi_mosaic s2rgb_mosaic; do
  echo "=== $STORE ==="
  curl -s -u "admin:TU_PASSWORD" \
    "http://localhost:8080/geoserver/rest/workspaces/aether/coveragestores/${STORE}/coverages.json" \
    | python3 -m json.tool | grep '"name"'
done
```

### 7. Permisos del script

```bash
sudo chmod +x /opt/aether-publish/scripts/run_publish.sh
```

---

## Uso

### Prueba en modo dry-run

```bash
sudo -u aether bash /opt/aether-publish/scripts/run_publish.sh --dry-run
```

Muestra las acciones que se ejecutarían sin enviar ninguna petición a GeoServer.

### Publicar todos los productos

```bash
sudo -u aether bash /opt/aether-publish/scripts/run_publish.sh
```

### Publicar solo algunos productos

```bash
sudo -u aether bash /opt/aether-publish/scripts/run_publish.sh \
  --products s2ndvi s2rgb
```

---

## Automatización con systemd

Para que la publicación se lance automáticamente tras el procesamiento del Nodo 1, instala el timer systemd. El timer se configura 30 minutos después del pipeline de procesamiento (que corre a las 05:30):

```bash
sudo tee /etc/systemd/system/aether-publish.service << 'EOF'
[Unit]
Description=Aether — Publicación de productos en GeoServer
After=network.target

[Service]
Type=oneshot
User=aether
EnvironmentFile=/opt/aether-publish/.env
ExecStart=/bin/bash /opt/aether-publish/scripts/run_publish.sh
StandardOutput=journal
StandardError=journal
EOF

sudo tee /etc/systemd/system/aether-publish.timer << 'EOF'
[Unit]
Description=Aether — Timer de publicación periódica
Requires=aether-publish.service

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now aether-publish.timer

# Verificar
sudo systemctl status aether-publish.timer
sudo systemctl list-timers aether-publish.timer
```

---

## Flujo de publicación

```
Nodo 1 (aether-process)
  └── ProcessService / MosaicService
        └── genera GeoTIFF COG en <ruta_productos>/{NDVIb,RGB1184,...}/

bind mount
  └── <ruta_productos>/NDVIb          →  /dwh/data/s2ndvi
      <ruta_productos>/RGB1184        →  /dwh/data/s2rgb
      <ruta_productos>/NDVIb_mosaic   →  /dwh/data/s2ndvi_mosaic
      <ruta_productos>/RGB1184_mosaic →  /dwh/data/s2rgb_mosaic

publish.py (Nodo 2)
  └── para cada .tif en /dwh/data/{s2ndvi,s2rgb,s2ndvi_mosaic,s2rgb_mosaic}/
        └── PUT /geoserver/rest/workspaces/aether/coveragestores/<store>/external.imagemosaic
              body: file:///dwh/data/s2ndvi/20260405_...tif
              → GeoServer registra el gránulo en la tabla s2ndvi de PostgreSQL
              → El fichero queda disponible en WMS-T con dimensión temporal
```

---

## Estructura del proyecto

```
aether-publish/  [instalado en /opt/aether-publish/]
│
├── app/
│   ├── __init__.py
│   └── webmapping/
│       └── publish.py          # Script de publicación REST → GeoServer
│
├── scripts/
│   └── run_publish.sh          # Lanzador: carga .env y ejecuta publish.py
│
├── aether_geoserver.sql        # DDL: tablas índice de gránulos ImageMosaic
├── env.template                # Plantilla de variables de entorno (sin secretos)
└── README.md                   # Este fichero
```

---

## Verificación del sistema

```bash
# 1. GeoServer responde
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/geoserver/web/
# → 200

# 2. Workspace aether existe
curl -s -u admin:TU_PASSWORD \
  http://localhost:8080/geoserver/rest/workspaces/aether.json | python3 -m json.tool

# 3. Gránulos indexados en PostgreSQL
psql -U aether_user -d aether \
  -c "SELECT COUNT(*), MIN(ingestion), MAX(ingestion) FROM public.s2ndvi;"

# 4. WMS-T operativo (sustituir bbox por la zona de tu workspace)
curl -s -o /tmp/test_wms.png \
  "http://localhost:8080/geoserver/aether/wms?SERVICE=WMS&VERSION=1.1.1\
&REQUEST=GetMap&LAYERS=aether:s2ndvi&BBOX=-7,41,-5,42\
&WIDTH=512&HEIGHT=512&SRS=EPSG:4326&FORMAT=image/png\
&TIME=2026-04-05"
file /tmp/test_wms.png   # debe ser: PNG image data
```

---

## Stack tecnológico

| Componente | Tecnología | Versión | Rol |
|------------|------------|---------|-----|
| Lenguaje | Python | 3.12 (sistema) | Script de publicación |
| HTTP | requests | 2.32+ | Llamadas REST a GeoServer |
| Servidor OGC | GeoServer | 2.28.4 | WMS, WMTS, WCS |
| Contenedor Java | Apache Tomcat | 9.0.118 | Runtime de GeoServer |
| JVM | OpenJDK | 17 | Entorno de ejecución Java |
| BD relacional | PostgreSQL + PostGIS | 18+ | Índice de gránulos ImageMosaic |
| Init system | systemd | — | Timer de publicación periódica |