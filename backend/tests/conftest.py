"""
Configuración de tests para YTS Downloader
"""
import os
import tempfile
import pytest
from app import app, db, UserModel, Download, MovieList, MovieListItem, Friendship
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='session')
def test_app():
    """Configurar app de testing"""
    # Crear base de datos temporal
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(test_app):
    """Cliente de testing"""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Runner de comandos CLI"""
    return test_app.test_cli_runner()

@pytest.fixture
def auth(client):
    """Helper para autenticación"""
    return AuthActions(client)

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='testuser', password='testpass'):
        return self._client.post(
            '/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/logout')

@pytest.fixture
def test_user(test_app):
    """Usuario de prueba"""
    with test_app.app_context():
        user = UserModel(
            username='testuser',
            password=generate_password_hash('testpass'),
            full_name='Usuario de Prueba',
            email='test@example.com',
            bio='Usuario para testing'
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_user2(test_app):
    """Segundo usuario de prueba"""
    with test_app.app_context():
        user = UserModel(
            username='testuser2',
            password=generate_password_hash('testpass2'),
            full_name='Usuario 2',
            email='test2@example.com'
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_movie_list(test_app, test_user):
    """Lista de películas de prueba"""
    with test_app.app_context():
        movie_list = MovieList(
            title='Lista de Prueba',
            description='Descripción de prueba',
            creator_id=test_user.id,
            is_public=True
        )
        db.session.add(movie_list)
        db.session.commit()
        return movie_list

@pytest.fixture
def test_download(test_app, test_user):
    """Descarga de prueba"""
    with test_app.app_context():
        download = Download(
            movie_title='Película de Prueba',
            year='2023',
            rating='8.5',
            magnet='magnet:?xt=urn:btih:test',
            imdb_code='tt1234567',
            status='completado',
            user_id=test_user.id
        )
        db.session.add(download)
        db.session.commit()
        return download
