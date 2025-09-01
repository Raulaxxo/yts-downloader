import pytest
from app import app, get_movie, build_magnet
import responses
from unittest.mock import mock_open, patch

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Registrar la función build_magnet en el contexto de Jinja2
    app.jinja_env.globals['build_magnet'] = build_magnet
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_movies_data():
    return [
        {
            "title": "Test Movie",
            "magnet": "magnet:?xt=test",
            "subs": "es",
            "year": "2023",
            "rating": "8.5",
            "status": "pendiente",
            "imdb_code": "tt1234567"
        }
    ]

def test_index_route(client, mock_movies_data):
    with patch('app.load_movies', return_value=mock_movies_data):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Movie' in response.data

@responses.activate
def test_search_route_with_results(client):
    # Simular respuesta de la API de YTS
    mock_response = {
        "status": "ok",
        "data": {
            "movies": [{
                "title": "Test Movie",
                "year": 2023,
                "rating": 8.5,
                "imdb_code": "tt1234567",
                "title_long": "Test Movie (2023)",
                "torrents": [{"hash": "1234567890abcdef"}]
            }]
        }
    }
    responses.add(
        responses.GET,
        'https://yts.mx/api/v2/list_movies.json?query_term=test&quality=1080p&limit=10',
        json=mock_response,
        status=200
    )
    
    response = client.get('/search?query=test')
    assert response.status_code == 200
    assert b'Test Movie' in response.data

@responses.activate
def test_search_route_no_results(client):
    # Simular respuesta sin resultados
    mock_response = {
        "status": "ok",
        "data": {
            "movies": []
        }
    }
    responses.add(
        responses.GET,
        'https://yts.mx/api/v2/list_movies.json?query_term=nonexistent&quality=1080p&limit=10',
        json=mock_response,
        status=200
    )
    
    response = client.get('/search?query=nonexistent')
    assert response.status_code == 200
    assert b'No se encontraron resultados' in response.data

def test_add_movie_route(client):
    movie_data = {
        "title": "New Test Movie",
        "magnet": "magnet:?xt=test2",
        "subs": "es",
        "year": "2023",
        "rating": "8.5",
        "imdb_code": "tt7654321"
    }
    
    with patch('app.load_movies', return_value=[]):
        with patch('app.save_movies') as mock_save:
            response = client.post('/add',
                                json=movie_data,
                                content_type='application/json')
            
            assert response.status_code == 200
            mock_save.assert_called_once()

def test_add_duplicate_movie(client, mock_movies_data):
    movie_data = mock_movies_data[0]
    
    with patch('app.load_movies', return_value=mock_movies_data):
        response = client.post('/add',
                            json=movie_data,
                            content_type='application/json')
        
        assert response.status_code == 409
        response_data = response.get_json()
        assert "error" in response_data
        assert "ya está en la lista" in response_data["error"]

def test_build_magnet():
    movie = {
        "title_long": "Test Movie (2023)",
        "torrents": [{
            "hash": "1234567890abcdef"
        }]
    }
    
    magnet = build_magnet(movie)
    assert magnet.startswith("magnet:?xt=urn:btih:1234567890abcdef")
    assert "Test%20Movie%20%282023%29" in magnet
    for tracker in ["open.demonii.com", "tracker.opentrackr.org"]:
        assert tracker in magnet
