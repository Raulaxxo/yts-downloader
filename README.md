# 🎬 YTS Downloader - Sistema Completo de Películas

<div align="center">

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

*Sistema automatizado para descargar, gestionar y reproducir películas con interfaz social*

</div>

## 🌟 Características Principales

### 🎯 Core Features
- 🎬 **Búsqueda avanzada** de películas desde YTS
- 📥 **Gestión automática** de descargas con Transmission
- 🎯 **Soporte completo** para torrents en calidad 1080p
- 📺 **Integración con Plex** para streaming
- 💬 **Enlaces directos** a subtítulos
- 🚀 **Interfaz web responsive** y moderna

### 👥 Sistema Social
- 👤 **Perfiles de usuario** completos con avatares personalizados
- 👫 **Sistema de amigos** con solicitudes y gestión
- 🎬 **Listas de películas** compartibles y organizables
- 📊 **Estadísticas personales** de descargas y actividad
- 🔒 **Configuraciones de privacidad** flexibles

### 🎨 Interfaz Moderna
- 🌙 **Modo oscuro/claro** con transiciones suaves
- 💎 **Diseño glassmorphism** con efectos visuales
- 📱 **Totalmente responsive** para móviles y tablets
- 🎛️ **Navegación intuitiva** con pestañas y modales
- 📸 **Subida de avatares** con vista previa en tiempo real

## 📚 Documentación Detallada

| Funcionalidad | Descripción | Documentación |
|---------------|-------------|---------------|
| 📚 **Índice Completo** | Navegación a toda la documentación | [📖 Ver Índice](./DOCS_INDEX.md) |
| 🎬 **Listas de Películas** | Sistema completo de listas compartibles | [📖 Ver Guía](./LISTAS_GUIA.md) |
| 📸 **Subida de Avatares** | Personalización de perfiles con imágenes | [📖 Ver Guía](./AVATAR_UPLOAD.md) |
| 📋 **Historial de Cambios** | Versiones y actualizaciones del proyecto | [📖 Ver Changelog](./CHANGELOG.md) |

## 🚀 Instalación Rápida

### Prerrequisitos
- Docker
- Docker Compose
- Puerto 15000, 19091, 32401, 51413 disponibles

### 1️⃣ Clonar y Configurar
```bash
git clone https://github.com/Raulaxxo/yts-downloader.git
cd yts-downloader

# Crear estructura de directorios
mkdir -p downloads/complete downloads/incomplete
sudo chmod -R 777 downloads
sudo chown -R 1000:1000 downloads
```

### 2️⃣ Iniciar Servicios
```bash
docker-compose up -d
```

### 3️⃣ Acceder al Sistema
- **🌐 Interfaz Principal**: http://localhost:15000
- **⚡ Transmission**: http://localhost:19091 (admin/1234)
- **🎭 Plex**: http://localhost:32401/web

## 🎯 Funcionalidades por Sección

### 🏠 Dashboard Principal
- Mis películas descargadas
- Búsqueda y exploración de catálogo
- Estado de descargas en tiempo real

### 👤 Sistema de Perfiles
- **Información personal**: Nombre, bio, ubicación, email
- **Avatar personalizado**: Subida de imágenes (PNG, JPG, GIF, WEBP)
- **Estadísticas**: Descargas, listas, amigos
- **Configuraciones**: Privacidad, notificaciones

### 🎬 Listas de Películas
- **Crear listas temáticas**: Horror, Acción, Comedias, etc.
- **Compartir con amigos**: Códigos de compartir únicos
- **Gestión avanzada**: Público/privado, descripciones, fechas
- **Seguimiento**: Películas vistas/pendientes

### 👥 Sistema Social
- **Solicitudes de amistad**: Enviar, aceptar, rechazar
- **Ver actividad**: Descargas y listas de amigos
- **Privacidad**: Controlar qué información es visible

## 🛠️ Arquitectura Técnica

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Services      │
│   (Templates)   │◄──►│   (Flask)       │◄──►│   (Docker)      │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │    │ • Python/SQLite │    │ • Transmission  │
│ • Glassmorphism │    │ • Authentication│    │ • Plex          │
│ • Responsive    │    │ • File Upload   │    │ • YTS API       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🗄️ Base de Datos
- **SQLite** para desarrollo
- **Modelos**: Usuario, Descarga, Lista, Amistad, ItemLista
- **Migraciones**: Automáticas con campos de perfil extendidos

### 📂 Estructura del Proyecto

```
yts-downloader/
├── 📁 backend/                 # Aplicación Flask
│   ├── 🐍 app.py              # Lógica principal y rutas
│   ├── 📋 requirements.txt     # Dependencias Python
│   ├── 📁 models/             # Modelos de base de datos
│   ├── 📁 templates/          # Plantillas HTML
│   ├── 📁 static/             # Archivos estáticos
│   │   ├── 🎨 css/           # Estilos (glassmorphism)
│   │   ├── ⚡ js/            # JavaScript interactivo
│   │   ├── 📸 avatars/       # Avatares subidos
│   │   └── 🖼️ images/        # Imágenes del sistema
│   └── 🗃️ instance/          # Base de datos SQLite
├── 📁 downloads/              # Películas descargadas
├── 📁 transmission_config/    # Configuración Transmission
├── 📁 plex_config/           # Configuración Plex
├── 🐳 docker-compose.yml     # Servicios containerizados
├── 📖 README.md              # Este archivo
├── 📖 LISTAS_GUIA.md         # Guía de listas de películas
└── 📖 AVATAR_UPLOAD.md       # Guía de subida de avatares
```

## 🔧 Desarrollo

### 🌐 Entorno Local
```bash
# Configurar entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
cd backend
pip install -r requirements.txt

# Ejecutar servidor de desarrollo
flask run
```

### 🐳 Desarrollo con Docker
```bash
# Ver logs en tiempo real
docker-compose logs -f backend

# Reiniciar servicios
docker-compose restart

# Acceder al contenedor
docker exec -it yts_backend bash
```

## 🔍 Solución de Problemas

### ❌ Problemas Comunes

| Problema | Solución |
|----------|----------|
| **Error de permisos** | `sudo chmod -R 777 downloads && sudo chown -R 1000:1000 downloads` |
| **Puertos ocupados** | Verificar que 15000, 19091, 32401, 51413 estén libres |
| **Error de base de datos** | Reiniciar contenedor: `docker-compose restart backend` |
| **Subida de avatar falla** | Verificar formato (PNG/JPG/GIF/WEBP) y tamaño (<5MB) |

### 📋 Logs de Debugging
```bash
# Ver todos los logs
docker-compose logs

# Solo backend
docker-compose logs backend

# Seguir logs en vivo
docker-compose logs -f
```

## 🚦 Estados del Sistema

### ✅ Funcional
- ✅ Descarga de películas YTS
- ✅ Sistema de usuarios con perfiles
- ✅ Listas de películas compartibles
- ✅ Sistema de amigos
- ✅ Subida de avatares
- ✅ Interfaz responsive

### 🔄 En Desarrollo
- 🔄 Notificaciones en tiempo real
- 🔄 Sistema de recomendaciones
- 🔄 Integración con más fuentes
- 🔄 App móvil nativa

## 🤝 Contribuir

1. **Fork** el proyecto
2. **Crear** rama feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** cambios (`git commit -m 'Add AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abrir** Pull Request

### 🎯 Áreas de Contribución
- 🐛 **Bug fixes** y optimizaciones
- 🎨 **Mejoras de UI/UX**
- 📱 **Responsive design**
- 🔧 **Nuevas funcionalidades**
- 📚 **Documentación**

## 📈 Estadísticas del Proyecto

- **Funcionalidades**: 20+ características implementadas
- **Templates**: 15+ páginas con diseño moderno
- **Modelos de BD**: 5 tablas relacionales
- **Rutas API**: 30+ endpoints
- **Archivos de documentación**: 3 guías especializadas

## 📞 Soporte

- 📧 **Issues**: [GitHub Issues](https://github.com/Raulaxxo/yts-downloader/issues)
- 📖 **Documentación**: Ver archivos `.md` en el proyecto
- 💬 **Discusiones**: [GitHub Discussions](https://github.com/Raulaxxo/yts-downloader/discussions)

## 📜 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">

**🎬 ¡Disfruta de tus películas! 🍿**

*Desarrollado con ❤️ por [Raulaxxo](https://github.com/Raulaxxo)*

</div>
