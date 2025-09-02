"""
Tests para rutas de la aplicación
"""
import pytest
import json
from app import db, UserModel, MovieList, Download

class TestMainRoutes:
    """Tests de rutas principales"""
    
    def test_index_route(self, client):
        """Test de ruta principal"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'YTS Downloader' in response.data or b'login' in response.data
    
    def test_search_route_requires_login(self, client):
        """Test que search requiere login"""
        response = client.get('/search')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_search_route_with_auth(self, client, auth):
        """Test de búsqueda con autenticación"""
        auth.login()
        response = client.get('/search')
        assert response.status_code == 200
        assert b'search' in response.data or b'Buscar' in response.data
    
    def test_search_api_endpoint(self, client, auth):
        """Test del endpoint de búsqueda API"""
        auth.login()
        response = client.get('/search?q=avengers&limit=5')
        assert response.status_code == 200
        # Puede devolver JSON o HTML dependiendo de la implementación

class TestProfileRoutes:
    """Tests de rutas de perfil"""
    
    def test_profile_requires_login(self, client):
        """Test que perfil requiere login"""
        response = client.get('/perfil')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_profile_with_auth(self, client, auth, test_user):
        """Test de perfil con autenticación"""
        auth.login()
        response = client.get('/perfil')
        assert response.status_code == 200
        assert test_user.username.encode() in response.data
    
    def test_profile_update(self, client, auth, test_user):
        """Test de actualización de perfil"""
        auth.login()
        response = client.post('/perfil', data={
            'bio': 'Nueva biografía',
            'is_private': False
        })
        # Puede ser redirection o success
        assert response.status_code in [200, 302]
        
        # Verificar actualización en DB
        with client.application.app_context():
            user = UserModel.query.get(test_user.id)
            assert user.bio == 'Nueva biografía'
    
    def test_avatar_upload_endpoint(self, client, auth):
        """Test de endpoint de subida de avatar"""
        auth.login()
        
        # Simular archivo de imagen
        data = {'avatar': (b'fake_image_data', 'avatar.jpg')}
        response = client.post('/upload_avatar', 
                             data=data, 
                             content_type='multipart/form-data')
        
        # Puede ser success o error dependiendo de validación
        assert response.status_code in [200, 302, 400]

class TestMovieListRoutes:
    """Tests de rutas de listas de películas"""
    
    def test_movie_lists_requires_login(self, client):
        """Test que listas requiere login"""
        response = client.get('/listas')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_movie_lists_with_auth(self, client, auth, test_movie_list):
        """Test de listas con autenticación"""
        auth.login()
        response = client.get('/listas')
        assert response.status_code == 200
        assert test_movie_list.name.encode() in response.data
    
    def test_create_movie_list(self, client, auth):
        """Test de creación de lista"""
        auth.login()
        response = client.post('/crear_lista', data={
            'name': 'Nueva Lista',
            'description': 'Descripción de prueba',
            'is_public': True
        })
        assert response.status_code in [200, 302]
        
        # Verificar creación en DB
        with client.application.app_context():
            lista = MovieList.query.filter_by(name='Nueva Lista').first()
            assert lista is not None
            assert lista.description == 'Descripción de prueba'
    
    def test_delete_movie_list(self, client, auth, test_movie_list):
        """Test de eliminación de lista"""
        auth.login()
        response = client.post(f'/eliminar_lista/{test_movie_list.id}')
        assert response.status_code in [200, 302]
        
        # Verificar eliminación en DB
        with client.application.app_context():
            lista = MovieList.query.get(test_movie_list.id)
            assert lista is None

class TestDownloadRoutes:
    """Tests de rutas de descargas"""
    
    def test_downloads_page(self, client, auth, test_download):
        """Test de página de descargas"""
        auth.login()
        response = client.get('/descargas')
        assert response.status_code == 200
        assert test_download.title.encode() in response.data
    
    def test_download_movie_endpoint(self, client, auth):
        """Test de endpoint de descarga"""
        auth.login()
        
        # Datos de película de prueba
        movie_data = {
            'title': 'Test Movie',
            'imdb_id': 'tt1234567',
            'magnet_link': 'magnet:?xt=urn:btih:test',
            'quality': '1080p'
        }
        
        response = client.post('/download', 
                             data=json.dumps(movie_data),
                             content_type='application/json')
        
        assert response.status_code in [200, 302]
        
        # Verificar creación en DB
        with client.application.app_context():
            download = Download.query.filter_by(title='Test Movie').first()
            assert download is not None
    
    def test_cancel_download(self, client, auth, test_download):
        """Test de cancelación de descarga"""
        auth.login()
        response = client.post(f'/cancel_download/{test_download.id}')
        assert response.status_code in [200, 302]
        
        # Verificar actualización en DB
        with client.application.app_context():
            download = Download.query.get(test_download.id)
            assert download.status in ['cancelled', 'failed']

class TestFriendshipRoutes:
    """Tests de rutas de amistad"""
    
    def test_friends_page(self, client, auth):
        """Test de página de amigos"""
        auth.login()
        response = client.get('/amigos')
        assert response.status_code == 200
        assert b'amigos' in response.data or b'friends' in response.data
    
    def test_send_friend_request(self, client, auth, test_user2):
        """Test de envío de solicitud de amistad"""
        auth.login()
        response = client.post('/enviar_solicitud', data={
            'user_id': test_user2.id
        })
        assert response.status_code in [200, 302]
    
    def test_accept_friend_request(self, client, auth, test_user, test_user2):
        """Test de aceptación de solicitud"""
        # Crear solicitud primero
        with client.application.app_context():
            from app import Friendship
            friendship = Friendship(
                requester_id=test_user2.id,
                addressee_id=test_user.id,
                status='pending'
            )
            db.session.add(friendship)
            db.session.commit()
            friendship_id = friendship.id
        
        auth.login()
        response = client.post(f'/aceptar_solicitud/{friendship_id}')
        assert response.status_code in [200, 302]

class TestAPIEndpoints:
    """Tests de endpoints API"""
    
    def test_api_user_stats(self, client, auth, test_user):
        """Test de estadísticas de usuario"""
        auth.login()
        response = client.get('/api/user/stats')
        assert response.status_code == 200
        
        if response.content_type == 'application/json':
            data = response.get_json()
            assert 'downloads_count' in data or 'lists_count' in data
    
    def test_api_movie_search(self, client, auth):
        """Test de búsqueda de películas API"""
        auth.login()
        response = client.get('/api/movies/search?q=test')
        assert response.status_code in [200, 404]  # Puede no encontrar resultados
    
    def test_api_download_status(self, client, auth, test_download):
        """Test de estado de descarga API"""
        auth.login()
        response = client.get(f'/api/download/{test_download.id}/status')
        assert response.status_code == 200

class TestErrorHandling:
    """Tests de manejo de errores"""
    
    def test_404_error(self, client):
        """Test de página no encontrada"""
        response = client.get('/pagina_inexistente')
        assert response.status_code == 404
    
    def test_unauthorized_access(self, client, test_user2):
        """Test de acceso no autorizado"""
        # Intentar acceder al perfil de otro usuario sin permisos
        response = client.get(f'/perfil/{test_user2.id}')
        assert response.status_code in [302, 403, 404]
    
    def test_invalid_movie_list_access(self, client, auth, test_user2):
        """Test de acceso a lista privada"""
        # Crear lista privada de otro usuario
        with client.application.app_context():
            private_list = MovieList(
                name='Lista Privada',
                user_id=test_user2.id,
                is_public=False
            )
            db.session.add(private_list)
            db.session.commit()
            list_id = private_list.id
        
        auth.login()  # Login como test_user (no test_user2)
        response = client.get(f'/lista/{list_id}')
        assert response.status_code in [403, 404]
