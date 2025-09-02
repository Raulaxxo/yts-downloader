"""
Tests para modelos de datos
"""
import pytest
from app import db, UserModel, Download, MovieList, MovieListItem, Friendship

class TestUserModel:
    """Tests del modelo User"""
    
    def test_create_user(self, app):
        """Test de creación de usuario"""
        with app.app_context():
            user = UserModel(username='testuser2', password='hashedpassword')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser2'
            assert user.created_at is not None
    
    def test_user_defaults(self, test_user):
        """Test de valores por defecto del usuario"""
        assert test_user.bio == ''
        assert test_user.avatar_url is None
        assert test_user.is_private == False
        assert test_user.notification_enabled == True
    
    def test_user_repr(self, test_user):
        """Test del método __repr__"""
        repr_str = repr(test_user)
        assert 'testuser' in repr_str
        assert 'UserModel' in repr_str

class TestDownload:
    """Tests del modelo Download"""
    
    def test_create_download(self, app, test_user):
        """Test de creación de descarga"""
        with app.app_context():
            download = Download(
                user_id=test_user.id,
                title='Test Movie',
                imdb_id='tt1234567',
                magnet_link='magnet:?xt=urn:btih:test',
                status='downloading'
            )
            db.session.add(download)
            db.session.commit()
            
            assert download.id is not None
            assert download.title == 'Test Movie'
            assert download.status == 'downloading'
            assert download.user_id == test_user.id
    
    def test_download_status_values(self, app, test_user):
        """Test de valores válidos para status"""
        valid_statuses = ['downloading', 'completed', 'failed', 'paused']
        
        with app.app_context():
            for status in valid_statuses:
                download = Download(
                    user_id=test_user.id,
                    title=f'Movie {status}',
                    imdb_id=f'tt{status}',
                    magnet_link='magnet:?xt=urn:btih:test',
                    status=status
                )
                db.session.add(download)
                db.session.commit()
                assert download.status == status

class TestMovieList:
    """Tests del modelo MovieList"""
    
    def test_create_movie_list(self, app, test_user):
        """Test de creación de lista"""
        with app.app_context():
            movie_list = MovieList(
                name='Favoritas',
                description='Mis películas favoritas',
                user_id=test_user.id
            )
            db.session.add(movie_list)
            db.session.commit()
            
            assert movie_list.id is not None
            assert movie_list.name == 'Favoritas'
            assert movie_list.user_id == test_user.id
            assert movie_list.is_public == True  # Default
    
    def test_movie_list_items(self, app, test_user, test_movie_list):
        """Test de elementos en lista"""
        with app.app_context():
            item = MovieListItem(
                movie_list_id=test_movie_list.id,
                title='Test Movie',
                imdb_id='tt1234567',
                year=2023,
                rating=8.5
            )
            db.session.add(item)
            db.session.commit()
            
            # Verificar relación
            test_movie_list = db.session.get(MovieList, test_movie_list.id)
            assert len(test_movie_list.items) == 1
            assert test_movie_list.items[0].title == 'Test Movie'

class TestFriendship:
    """Tests del modelo Friendship"""
    
    def test_create_friendship(self, app, test_user, test_user2):
        """Test de creación de amistad"""
        with app.app_context():
            friendship = Friendship(
                requester_id=test_user.id,
                addressee_id=test_user2.id,
                status='pending'
            )
            db.session.add(friendship)
            db.session.commit()
            
            assert friendship.id is not None
            assert friendship.status == 'pending'
            assert friendship.requester_id == test_user.id
            assert friendship.addressee_id == test_user2.id
    
    def test_friendship_statuses(self, app, test_user, test_user2):
        """Test de estados de amistad"""
        valid_statuses = ['pending', 'accepted', 'declined', 'blocked']
        
        with app.app_context():
            for i, status in enumerate(valid_statuses):
                # Crear usuarios adicionales para cada test
                addressee = UserModel(
                    username=f'user_{i}',
                    password='password'
                )
                db.session.add(addressee)
                db.session.flush()
                
                friendship = Friendship(
                    requester_id=test_user.id,
                    addressee_id=addressee.id,
                    status=status
                )
                db.session.add(friendship)
                db.session.commit()
                assert friendship.status == status

class TestRelationships:
    """Tests de relaciones entre modelos"""
    
    def test_user_downloads_relationship(self, app, test_user, test_download):
        """Test de relación user-downloads"""
        with app.app_context():
            user = db.session.get(UserModel, test_user.id)
            assert len(user.downloads) == 1
            assert user.downloads[0].title == test_download.title
    
    def test_user_movie_lists_relationship(self, app, test_user, test_movie_list):
        """Test de relación user-movie_lists"""
        with app.app_context():
            user = db.session.get(UserModel, test_user.id)
            assert len(user.movie_lists) == 1
            assert user.movie_lists[0].name == test_movie_list.name
    
    def test_friendship_relationships(self, app, test_user, test_user2):
        """Test de relaciones de amistad"""
        with app.app_context():
            friendship = Friendship(
                requester_id=test_user.id,
                addressee_id=test_user2.id,
                status='accepted'
            )
            db.session.add(friendship)
            db.session.commit()
            
            # Recargar usuarios
            user1 = db.session.get(UserModel, test_user.id)
            user2 = db.session.get(UserModel, test_user2.id)
            
            # Verificar relaciones
            assert len(user1.sent_requests) == 1
            assert len(user2.received_requests) == 1
            assert user1.sent_requests[0].addressee_id == user2.id
            assert user2.received_requests[0].requester_id == user1.id
