"""
Tests para sistema de autenticación
"""
import pytest
from app import db, UserModel
from werkzeug.security import check_password_hash

class TestAuth:
    """Tests de autenticación"""
    
    def test_register(self, client):
        """Test de registro de usuario"""
        response = client.get('/register')
        assert response.status_code == 200
        
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        assert response.status_code == 302  # Redirection
        
        # Verificar que el usuario fue creado
        with client.application.app_context():
            user = UserModel.query.filter_by(username='newuser').first()
            assert user is not None
            assert check_password_hash(user.password, 'password123')
    
    def test_register_duplicate_username(self, client, test_user):
        """Test de registro con username duplicado"""
        response = client.post('/register', data={
            'username': 'testuser',  # Ya existe
            'password': 'password123',
            'confirm_password': 'password123'
        })
        assert response.status_code == 200  # Se queda en la página con error
        assert b'Usuario ya existe' in response.data or b'error' in response.data
    
    def test_login_logout(self, auth):
        """Test de login y logout"""
        response = auth.login()
        assert response.status_code == 302  # Redirection después del login
        
        response = auth.logout()
        assert response.status_code == 302  # Redirection después del logout
    
    def test_login_invalid_credentials(self, auth):
        """Test de login con credenciales inválidas"""
        response = auth.login('testuser', 'wrongpassword')
        assert response.status_code == 200  # Se queda en login
        assert b'incorrecto' in response.data or b'error' in response.data
    
    def test_login_required(self, client):
        """Test de páginas que requieren login"""
        protected_routes = ['/perfil', '/listas', '/amigos', '/search']
        
        for route in protected_routes:
            response = client.get(route)
            assert response.status_code == 302  # Redirection a login
            assert '/login' in response.location
    
    def test_profile_access_after_login(self, client, auth, test_user):
        """Test de acceso al perfil después del login"""
        auth.login()
        response = client.get('/perfil')
        assert response.status_code == 200
        assert test_user.username.encode() in response.data
