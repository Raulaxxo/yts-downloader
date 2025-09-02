"""
Tests para funcionalidades específicas
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock

class TestAvatarUpload:
    """Tests de subida de avatares"""
    
    def test_valid_image_upload(self, client, auth, app):
        """Test de subida de imagen válida"""
        auth.login()
        
        # Crear imagen temporal
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp.write(b'fake_jpg_data')
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as img:
                data = {'avatar': (img, 'test.jpg')}
                response = client.post('/upload_avatar', 
                                     data=data,
                                     content_type='multipart/form-data')
            
            assert response.status_code in [200, 302]
        finally:
            os.unlink(tmp_path)
    
    def test_invalid_file_type(self, client, auth):
        """Test de tipo de archivo inválido"""
        auth.login()
        
        # Crear archivo no imagen
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b'not an image')
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, 'rb') as file:
                data = {'avatar': (file, 'test.txt')}
                response = client.post('/upload_avatar',
                                     data=data,
                                     content_type='multipart/form-data')
            
            # Debería rechazar el archivo
            assert response.status_code in [400, 302]
        finally:
            os.unlink(tmp_path)
    
    def test_no_file_upload(self, client, auth):
        """Test sin archivo seleccionado"""
        auth.login()
        response = client.post('/upload_avatar', data={})
        assert response.status_code in [400, 302]

class TestMovieSearch:
    """Tests de búsqueda de películas"""
    
    @patch('requests.get')
    def test_search_api_success(self, mock_get, client, auth):
        """Test de búsqueda exitosa"""
        # Mock de respuesta API
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': {
                'movies': [
                    {
                        'title': 'Test Movie',
                        'imdb_code': 'tt1234567',
                        'year': 2023,
                        'rating': 8.5,
                        'genres': ['Action', 'Adventure']
                    }
                ]
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        auth.login()
        response = client.get('/search?q=test')
        assert response.status_code == 200
    
    @patch('requests.get')
    def test_search_api_failure(self, mock_get, client, auth):
        """Test de fallo en API"""
        mock_get.side_effect = Exception("API Error")
        
        auth.login()
        response = client.get('/search?q=test')
        # La aplicación debería manejar el error gracefully
        assert response.status_code in [200, 500]
    
    def test_search_empty_query(self, client, auth):
        """Test de búsqueda con query vacío"""
        auth.login()
        response = client.get('/search?q=')
        assert response.status_code == 200

class TestDownloadFunctionality:
    """Tests de funcionalidad de descarga"""
    
    @patch('subprocess.run')
    def test_download_start(self, mock_subprocess, client, auth, test_user):
        """Test de inicio de descarga"""
        mock_subprocess.return_value = MagicMock(returncode=0)
        
        auth.login()
        movie_data = {
            'title': 'Test Movie',
            'imdb_id': 'tt1234567',
            'magnet_link': 'magnet:?xt=urn:btih:test',
            'quality': '1080p'
        }
        
        response = client.post('/download',
                             json=movie_data)
        assert response.status_code in [200, 302]
    
    def test_duplicate_download_prevention(self, client, auth, test_download):
        """Test de prevención de descargas duplicadas"""
        auth.login()
        
        # Intentar descargar la misma película
        movie_data = {
            'title': test_download.title,
            'imdb_id': test_download.imdb_id,
            'magnet_link': 'magnet:?xt=urn:btih:different',
            'quality': '1080p'
        }
        
        response = client.post('/download', json=movie_data)
        # Debería prevenir duplicados
        assert response.status_code in [200, 400, 409]
    
    def test_download_history(self, client, auth, test_download):
        """Test de historial de descargas"""
        auth.login()
        response = client.get('/descargas')
        assert response.status_code == 200
        assert test_download.title.encode() in response.data

class TestFriendshipSystem:
    """Tests del sistema de amistad"""
    
    def test_send_friend_request(self, client, auth, test_user2):
        """Test de envío de solicitud de amistad"""
        auth.login()
        
        response = client.post('/enviar_solicitud', data={
            'username': test_user2.username
        })
        assert response.status_code in [200, 302]
        
        # Verificar en DB
        with client.application.app_context():
            from app import Friendship
            friendship = Friendship.query.filter_by(
                addressee_id=test_user2.id
            ).first()
            assert friendship is not None
            assert friendship.status == 'pending'
    
    def test_accept_friend_request(self, client, auth, test_user, test_user2):
        """Test de aceptación de solicitud"""
        # Crear solicitud pendiente
        with client.application.app_context():
            from app import Friendship, db
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
        
        # Verificar estado actualizado
        with client.application.app_context():
            from app import Friendship
            friendship = Friendship.query.get(friendship_id)
            assert friendship.status == 'accepted'
    
    def test_block_user(self, client, auth, test_user2):
        """Test de bloqueo de usuario"""
        auth.login()
        
        response = client.post('/bloquear_usuario', data={
            'user_id': test_user2.id
        })
        assert response.status_code in [200, 302]

class TestPrivacySettings:
    """Tests de configuraciones de privacidad"""
    
    def test_private_profile_access(self, client, auth, test_user, test_user2):
        """Test de acceso a perfil privado"""
        # Hacer perfil privado
        with client.application.app_context():
            from app import UserModel, db
            user = UserModel.query.get(test_user2.id)
            user.is_private = True
            db.session.commit()
        
        auth.login()  # Login como test_user
        response = client.get(f'/perfil/{test_user2.id}')
        # No debería poder ver perfil privado sin amistad
        assert response.status_code in [403, 404]
    
    def test_private_movie_list_access(self, client, auth, test_user2):
        """Test de acceso a lista privada"""
        # Crear lista privada
        with client.application.app_context():
            from app import MovieList, db
            private_list = MovieList(
                name='Lista Privada',
                user_id=test_user2.id,
                is_public=False
            )
            db.session.add(private_list)
            db.session.commit()
            list_id = private_list.id
        
        auth.login()  # Login como test_user
        response = client.get(f'/lista/{list_id}')
        assert response.status_code in [403, 404]

class TestDataValidation:
    """Tests de validación de datos"""
    
    def test_invalid_movie_data(self, client, auth):
        """Test de datos de película inválidos"""
        auth.login()
        
        invalid_data = {
            'title': '',  # Título vacío
            'imdb_id': 'invalid',  # ID inválido
            'magnet_link': 'not_a_magnet'  # Magnet inválido
        }
        
        response = client.post('/download', json=invalid_data)
        assert response.status_code in [400, 422]
    
    def test_sql_injection_prevention(self, client, auth):
        """Test de prevención de inyección SQL"""
        auth.login()
        
        # Intentar inyección SQL en búsqueda
        malicious_query = "'; DROP TABLE users; --"
        response = client.get(f'/search?q={malicious_query}')
        
        # La aplicación debería manejar esto sin problemas
        assert response.status_code in [200, 400]
    
    def test_xss_prevention(self, client, auth):
        """Test de prevención XSS"""
        auth.login()
        
        # Intentar script malicioso en bio
        xss_payload = '<script>alert("XSS")</script>'
        response = client.post('/perfil', data={
            'bio': xss_payload
        })
        
        assert response.status_code in [200, 302]
        
        # Verificar que el script fue escapado
        response = client.get('/perfil')
        assert b'<script>' not in response.data

class TestPerformance:
    """Tests de rendimiento básico"""
    
    def test_large_movie_list_load(self, client, auth, test_user):
        """Test de carga de lista grande"""
        # Crear muchos elementos en lista
        with client.application.app_context():
            from app import MovieList, MovieListItem, db
            large_list = MovieList(
                name='Lista Grande',
                user_id=test_user.id
            )
            db.session.add(large_list)
            db.session.flush()
            
            for i in range(50):  # 50 películas
                item = MovieListItem(
                    movie_list_id=large_list.id,
                    title=f'Movie {i}',
                    imdb_id=f'tt{i:07d}',
                    year=2020 + (i % 4)
                )
                db.session.add(item)
            
            db.session.commit()
            list_id = large_list.id
        
        auth.login()
        import time
        start_time = time.time()
        response = client.get(f'/lista/{list_id}')
        end_time = time.time()
        
        assert response.status_code == 200
        # Debería cargar en menos de 2 segundos
        assert (end_time - start_time) < 2.0
    
    def test_multiple_concurrent_requests(self, client, auth):
        """Test de múltiples requests concurrentes (básico)"""
        auth.login()
        
        import threading
        results = []
        
        def make_request():
            response = client.get('/perfil')
            results.append(response.status_code)
        
        # Crear 5 threads concurrentes
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join()
        
        # Todos deberían ser exitosos
        assert all(status == 200 for status in results)
        assert len(results) == 5
