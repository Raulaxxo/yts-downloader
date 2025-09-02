# 📸 Funcionalidad de Subida de Avatares

## ✨ Características Implementadas

### 🎯 Subida de Imágenes
- **Tipos de archivo soportados**: PNG, JPG, JPEG, GIF, WEBP
- **Tamaño máximo**: 5MB
- **Vista previa en tiempo real**: Se muestra la imagen antes de guardar
- **Nombres únicos**: Cada archivo se guarda con un UUID único
- **Validación**: Tipo de archivo y tamaño se validan tanto en frontend como backend

### 🎨 Interfaz de Usuario
- **Campo de subida de archivos**: Botón estilizado con icono
- **Vista previa inmediata**: Al seleccionar un archivo se muestra en el avatar
- **Indicador de archivo**: Muestra el nombre del archivo seleccionado
- **Alternativa de URL**: Se puede usar una URL externa en lugar de subir archivo
- **Estilos modernos**: Integrado con el diseño glassmorphism existente

### 🛠️ Funcionalidad Técnica
- **Endpoint de subida**: `/perfil/upload-avatar` (POST)
- **Almacenamiento**: Archivos guardados en `static/avatars/`
- **Nombres únicos**: Formato `{uuid}_{user_id}.{extension}`
- **Integración**: Funciona junto con el formulario de edición de perfil

## 🚀 Cómo Usar

### Para Usuarios
1. **Ir a Editar Perfil**: Navegar a `/perfil/editar`
2. **Seleccionar Imagen**: Hacer clic en "📁 Seleccionar Imagen"
3. **Vista Previa**: La imagen se mostrará inmediatamente
4. **Guardar**: Hacer clic en "💾 Guardar Cambios"

### Para Desarrolladores
- **Ruta de subida**: `POST /perfil/upload-avatar`
- **Parámetros**: `avatar_file` (multipart/form-data)
- **Respuesta**: `{"url": "/static/avatars/filename.jpg", "message": "..."}`
- **Errores**: Códigos 400/500 con mensaje descriptivo

## 📁 Estructura de Archivos

```
backend/
├── static/
│   ├── avatars/          # 📸 Avatares subidos
│   │   └── {uuid}_{user_id}.{ext}
│   ├── css/
│   │   └── profile.css   # 🎨 Estilos para subida
│   └── images/
├── templates/
│   └── edit_profile.html # 📝 Formulario con subida
└── app.py               # 🔧 Lógica del servidor
```

## 🔒 Seguridad
- **Validación de tipos**: Solo imágenes permitidas
- **Límite de tamaño**: Máximo 5MB
- **Nombres únicos**: Previene conflictos y sobreescritura
- **Sanitización**: Extensiones de archivo validadas

## 🎯 Funcionalidades Futuras Posibles
- [ ] Redimensionamiento automático de imágenes
- [ ] Compresión de imágenes grandes
- [ ] Múltiples tamaños (thumbnail, medium, large)
- [ ] Eliminación de avatares antiguos
- [ ] Integración con servicios de almacenamiento en la nube
