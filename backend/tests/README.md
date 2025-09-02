# 🧪 Tests - YTS Downloader

Sistema de testing completo para la aplicación YTS Downloader.

## 📁 Estructura de Tests

```
tests/
├── conftest.py              # Configuración y fixtures compartidas
├── test_auth.py            # Tests de autenticación
├── test_models.py          # Tests de modelos de datos
├── test_routes.py          # Tests de rutas y endpoints
├── test_features.py        # Tests de funcionalidades específicas
└── README.md               # Esta documentación
```

## 🚀 Ejecutar Tests

### Todos los tests
```bash
# Opción 1: Script personalizado
python run_tests.py

# Opción 2: Pytest directo
pytest tests/ -v
```

### Tests específicos
```bash
# Por archivo
python run_tests.py --file test_auth.py
pytest tests/test_auth.py -v

# Por función específica
python run_tests.py --file test_auth.py --test test_login_logout
pytest tests/test_auth.py::TestAuth::test_login_logout -v

# Por categoría (usando markers)
pytest -m "auth" -v          # Solo tests de autenticación
pytest -m "models" -v        # Solo tests de modelos
pytest -m "not slow" -v      # Excluir tests lentos
```

### Con coverage
```bash
pytest tests/ --cov=app --cov-report=html
python run_tests.py --coverage  # Abrir report en navegador
```

## 📊 Tipos de Tests

### 🔐 Tests de Autenticación (`test_auth.py`)
- **Registro de usuarios**: Validación de datos, duplicados
- **Login/Logout**: Credenciales válidas e inválidas
- **Protección de rutas**: Acceso sin autenticación
- **Sesiones**: Manejo de estado de usuario

```python
class TestAuth:
    def test_register(self, client):
        """Test de registro de usuario"""
    
    def test_login_logout(self, auth):
        """Test de login y logout"""
    
    def test_login_required(self, client):
        """Test de páginas que requieren login"""
```

### 🗄️ Tests de Modelos (`test_models.py`)
- **Creación de objetos**: Usuarios, descargas, listas
- **Validaciones**: Datos requeridos, formatos
- **Relaciones**: Foreign keys, asociaciones
- **Métodos de modelo**: Funcionalidades específicas

```python
class TestUserModel:
    def test_create_user(self, app):
        """Test de creación de usuario"""
    
    def test_user_defaults(self, test_user):
        """Test de valores por defecto"""

class TestDownload:
    def test_create_download(self, app, test_user):
        """Test de creación de descarga"""
```

### 🛣️ Tests de Rutas (`test_routes.py`)
- **Endpoints principales**: Index, search, profile
- **Códigos de respuesta**: 200, 302, 404, etc.
- **Contenido de respuesta**: Datos esperados
- **Redirecciones**: Login, logout, acciones

```python
class TestMainRoutes:
    def test_search_route_with_auth(self, client, auth):
        """Test de búsqueda con autenticación"""

class TestProfileRoutes:
    def test_profile_update(self, client, auth, test_user):
        """Test de actualización de perfil"""
```

### ⚡ Tests de Funcionalidades (`test_features.py`)
- **Upload de avatares**: Validación de archivos
- **Sistema de amistad**: Solicitudes, aceptación
- **Búsqueda de películas**: API integration, mocking
- **Descargas**: Prevención duplicados, historial
- **Privacidad**: Perfiles y listas privadas
- **Seguridad**: XSS, SQL injection, validación

```python
class TestAvatarUpload:
    def test_valid_image_upload(self, client, auth, app):
        """Test de subida de imagen válida"""

class TestFriendshipSystem:
    def test_send_friend_request(self, client, auth, test_user2):
        """Test de envío de solicitud de amistad"""
```

## 🔧 Fixtures Disponibles

### Aplicación y Base de Datos
- `app`: Instancia de Flask configurada para testing
- `client`: Cliente de test para hacer requests
- `runner`: CLI runner para comandos

### Autenticación
- `auth`: Helper para login/logout
- `test_user`: Usuario de prueba principal
- `test_user2`: Segundo usuario para tests de interacción

### Datos de Prueba
- `test_download`: Descarga de ejemplo
- `test_movie_list`: Lista de películas de ejemplo

```python
def test_example(client, auth, test_user):
    """Usar fixtures en tests"""
    auth.login()  # Login automático
    response = client.get('/perfil')
    assert test_user.username.encode() in response.data
```

## 🏷️ Markers Disponibles

```python
@pytest.mark.slow
def test_large_operation():
    """Test que toma mucho tiempo"""

@pytest.mark.integration
def test_api_integration():
    """Test de integración con APIs externas"""

@pytest.mark.auth
def test_login_feature():
    """Test relacionado con autenticación"""
```

Ejecutar por markers:
```bash
pytest -m "auth and not slow" -v
pytest -m "integration" -v
pytest -m "unit" -v
```

## 📈 Coverage

El sistema genera reportes de cobertura de código:

```bash
# HTML report (recomendado)
pytest --cov=app --cov-report=html
# Ver en htmlcov/index.html

# Terminal report
pytest --cov=app --cov-report=term-missing

# XML report (para CI/CD)
pytest --cov=app --cov-report=xml
```

### Objetivos de Coverage
- **Modelos**: >95% - Lógica crítica de datos
- **Rutas**: >90% - Endpoints principales
- **Funcionalidades**: >85% - Features completas
- **Total**: >85% - Cobertura general

## 🔍 Debugging Tests

### Verbose output
```bash
pytest tests/ -v -s  # -s para ver prints
```

### Parar en primer fallo
```bash
pytest tests/ -x
```

### Debugger
```python
def test_debug_example():
    import pdb; pdb.set_trace()  # Breakpoint
    # Tu código de test aquí
```

### Solo tests que fallaron
```bash
pytest --lf  # Last failed
pytest --ff  # Failed first
```

## 🚀 Integración Continua

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pip install -r requirements.txt
    python -m pytest tests/ --cov=app --cov-report=xml
```

### Pre-commit hooks
```bash
# Ejecutar tests antes de commit
pytest tests/ --maxfail=1 -q
```

## 📝 Escribir Nuevos Tests

### Estructura básica
```python
class TestNuevaFuncionalidad:
    """Tests para nueva funcionalidad"""
    
    def test_caso_basico(self, client, auth):
        """Test del caso básico"""
        auth.login()
        response = client.get('/nueva-ruta')
        assert response.status_code == 200
    
    def test_caso_error(self, client):
        """Test de manejo de errores"""
        response = client.get('/nueva-ruta')
        assert response.status_code == 302  # Redirect a login
    
    @pytest.mark.slow
    def test_caso_performance(self, client, auth):
        """Test de rendimiento"""
        # Test que puede tardar más tiempo
        pass
```

### Buenas prácticas
1. **Nombres descriptivos**: `test_user_can_upload_valid_image`
2. **Arrange-Act-Assert**: Preparar, ejecutar, verificar
3. **Un concepto por test**: Tests específicos y focalizados
4. **Usar fixtures**: Reutilizar configuración
5. **Mock dependencias externas**: APIs, filesystem, etc.
6. **Limpiar después**: Fixtures se encargan automáticamente

## 🎯 Comandos Rápidos

```bash
# Setup inicial
pip install pytest pytest-cov pytest-flask

# Ejecutar todo
python run_tests.py

# Solo lo rápido
pytest -m "not slow"

# Solo autenticación
pytest -m "auth"

# Con coverage completo
pytest --cov=app --cov-report=html --cov-report=term

# Debug mode
pytest -v -s --pdb

# Actualizar snapshots (si usas)
pytest --snapshot-update
```

## 🏆 Métricas de Calidad

- **Tests ejecutándose**: ✅ 100%
- **Coverage objetivo**: 85%+
- **Tiempo ejecución**: <30 segundos
- **Tests por funcionalidad**: Mínimo 3 (happy path, error, edge case)
- **Documentación**: Cada test con docstring descriptivo

¡Con este sistema de testing completo, tu aplicación YTS Downloader está protegida contra regresiones y lista para crecimiento continuo! 🚀
