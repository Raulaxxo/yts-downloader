# YTS Downloader

Sistema automatizado para descargar películas en 1080p desde YTS, gestionarlas con Transmission y reproducirlas con Plex.

## Características

- 🎬 Búsqueda y descarga de películas desde YTS
- 📥 Gestión automática de descargas con Transmission
- 🎯 Soporte para torrents en calidad 1080p
- 📺 Integración con Plex para streaming
- 💬 Enlaces directos a subtítulos
- 🚀 Interfaz web responsive

## Requisitos

- Docker
- Docker Compose

## Instalación

1. Clonar el repositorio:
```bash
git clone <tu-repositorio>
cd yts-downloader
```

2. Configurar las variables de entorno (opcional):
   - Editar los valores en `docker-compose.yml` según necesites
   - Puedes modificar usuarios, contraseñas y puertos

3. Crear y configurar las carpetas necesarias:
```bash
# Crear carpetas para descargas
mkdir -p downloads/complete downloads/incomplete

# Establecer permisos (importante para que Transmission funcione)
sudo chmod -R 777 downloads
sudo chown -R 1000:1000 downloads
```

4. Iniciar los servicios:
```bash
docker-compose up -d
```

## Acceso a los servicios

- **Interfaz web**: http://localhost:15000
- **Transmission**: http://localhost:19091
  - Usuario: admin
  - Contraseña: 1234
- **Plex**: http://localhost:32401/web

## Solución de problemas

### Permisos de Transmission
Si ves errores de permisos en los logs de Transmission como:
```
stat: cannot statx '/downloads/complete': No such file or directory
```
Asegúrate de haber ejecutado los comandos de permisos:
```bash
sudo chmod -R 777 downloads
sudo chown -R 1000:1000 downloads
```

### Puertos en uso
Si recibes errores como "ports are not available", asegúrate de que los puertos no estén siendo utilizados por otros servicios. Los puertos utilizados son:
- 15000 (Backend)
- 19091 (Transmission)
- 32401 (Plex)
- 51413 (Transmission peer)

## Estructura de directorios

```
├── backend/              # Aplicación Flask
│   ├── app.py           # Lógica principal
│   ├── requirements.txt # Dependencias Python
│   └── templates/       # Plantillas HTML
├── downloads/           # Descargas de películas
├── transmission_config/ # Configuración de Transmission
├── plex_config/        # Configuración de Plex
└── docker-compose.yml  # Configuración de servicios
```

## Desarrollo

Para desarrollo local:

1. Configura un entorno virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instala las dependencias:
```bash
cd backend
pip install -r requirements.txt
```

3. Ejecuta el servidor de desarrollo:
```bash
flask run
```

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## Licencia

MIT
