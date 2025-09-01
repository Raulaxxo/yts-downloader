from flask import Flask, request, render_template, redirect
import requests
import urllib.parse
import json

# Trackers recomendados
TRACKERS = [
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.openbittorrent.com:80",
    "udp://tracker.coppersurfer.tk:6969",
    "udp://tracker.leechers-paradise.org:6969"
]

def build_magnet(movie):
    """Construye el magnet link usando el primer torrent en 1080p"""
    torrent = movie["torrents"][0]
    hash_ = torrent["hash"]
    name = urllib.parse.quote(movie["title_long"])
    magnet = f"magnet:?xt=urn:btih:{hash_}&dn={name}"
    for tr in TRACKERS:
        magnet += f"&tr={urllib.parse.quote(tr)}"
    return magnet

app = Flask(__name__)
MOVIES_FILE = "movies.json"

# Registrar build_magnet en el contexto de Jinja2
app.jinja_env.globals['build_magnet'] = build_magnet

# Transmission configuración (dentro de Docker Compose)
TRANSMISSION_URL = "http://transmission:9091/transmission/rpc"
TRANSMISSION_USER = "admin"
TRANSMISSION_PASS = "1234"
# También habilitamos el modo debug para ver más detalles
app.debug = True

# --- Funciones ---
def get_transmission_token():
    """Obtiene el token de sesión de Transmission"""
    try:
        response = requests.get(TRANSMISSION_URL, auth=(TRANSMISSION_USER, TRANSMISSION_PASS))
        return response.headers.get('X-Transmission-Session-Id')
    except Exception as e:
        app.logger.error(f"Error obteniendo token de Transmission: {str(e)}")
        return None

def delete_from_transmission(hash_value):
    """Elimina un torrent de Transmission usando su hash"""
    try:
        # Obtener token de sesión
        token = get_transmission_token()
        if not token:
            return False

        # Preparar headers y datos
        headers = {
            'X-Transmission-Session-Id': token,
            'Content-Type': 'application/json'
        }
        
        data = {
            "method": "torrent-remove",
            "arguments": {
                "ids": [hash_value],
                "delete-local-data": True  # Esto eliminará también los archivos descargados
            }
        }

        # Enviar solicitud a Transmission
        response = requests.post(
            TRANSMISSION_URL,
            json=data,
            headers=headers,
            auth=(TRANSMISSION_USER, TRANSMISSION_PASS)
        )

        app.logger.info(f"Respuesta de Transmission al eliminar: Status {response.status_code}")
        if response.status_code == 200:
            return True
        return False

    except Exception as e:
        app.logger.error(f"Error eliminando torrent de Transmission: {str(e)}")
        return False

def load_movies():
    try:
        with open(MOVIES_FILE) as f:
            return json.load(f)
    except:
        return []

def save_movies(movies):
    with open(MOVIES_FILE, "w") as f:
        json.dump(movies, f, indent=2)

@app.route('/delete/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    """Elimina una película de la lista y de Transmission"""
    try:
        movies = load_movies()
        if 0 <= movie_id < len(movies):
            movie = movies[movie_id]
            
            # Si la película está en descarga o completada, la eliminamos de Transmission
            if movie.get('status') in ['descargando', 'completado']:
                # Extraer el hash del magnet link
                magnet = movie.get('magnet', '')
                hash_match = magnet.split('btih:')[1].split('&')[0] if 'btih:' in magnet else None
                
                if hash_match:
                    app.logger.info(f"Intentando eliminar torrent con hash: {hash_match}")
                    if not delete_from_transmission(hash_match):
                        app.logger.warning("No se pudo eliminar el torrent de Transmission")
                else:
                    app.logger.warning("No se encontró el hash en el magnet link")
            
            # Eliminar de la lista
            del movies[movie_id]
            save_movies(movies)
            return {"message": "Película eliminada"}, 200
        return {"error": "Película no encontrada"}, 404
    except Exception as e:
        app.logger.error(f"Error al eliminar película: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

def get_movie(query):
    """Busca película en YTS API filtrando 1080p"""
    url = f"https://yts.mx/api/v2/list_movies.json?query_term={query}&quality=1080p&limit=1"
    resp = requests.get(url).json()
    if resp["status"] != "ok" or not resp["data"]["movies"]:
        return None
    return resp["data"]["movies"][0]

@app.route('/')
def index():
    """Página principal que muestra la lista de películas"""
    movies = load_movies()
    return render_template('index.html', movies=movies)

@app.route('/search')
def search():
    """Página de búsqueda de películas"""
    query = request.args.get('query', '')
    results = []
    if query:
        try:
            url = f"https://yts.mx/api/v2/list_movies.json?query_term={query}&quality=1080p&limit=10"
            resp = requests.get(url).json()
            if resp["status"] == "ok" and resp["data"]["movies"]:
                results = resp["data"]["movies"]
        except Exception as e:
            app.logger.error(f"Error en búsqueda: {str(e)}")
    return render_template('search.html', results=results, query=query)

@app.route('/add', methods=['POST'])
def add_movie():
    """Agrega una nueva película a la lista"""
    try:
        movie_data = request.get_json()
        if not movie_data:
            return {"error": "Datos de película requeridos"}, 400

        required_fields = ['title', 'magnet', 'subs']
        missing_fields = [field for field in required_fields if field not in movie_data]
        if missing_fields:
            return {"error": f"Campos requeridos faltantes: {', '.join(missing_fields)}"}, 400

        # Verificar si la película ya existe
        movies = load_movies()
        if any(m['title'] == movie_data['title'] for m in movies):
            return {"error": "La película ya está en la lista"}, 409

        # Preparar datos
        movie_info = {
            'title': movie_data['title'],
            'magnet': movie_data['magnet'],
            'subs': movie_data['subs'],
            'year': movie_data.get('year', ''),
            'rating': movie_data.get('rating', ''),
            'status': 'pendiente',
            'imdb_code': movie_data.get('imdb_code', '')
        }

        # Agregar a la lista y guardar
        movies.append(movie_info)
        try:
            save_movies(movies)
        except Exception as e:
            app.logger.error(f"Error al guardar películas: {str(e)}")
            return {"error": "Error al guardar la película"}, 500

        # Intentar iniciar la descarga
        result = add_to_transmission(movie_info['magnet'])
        if result is None:
            return {"message": "Película agregada, pero hubo un error al iniciar la descarga. Intente descargarla más tarde."}, 200
        
        movie_info['status'] = 'descargando'
        try:
            save_movies(movies)
        except Exception as e:
            app.logger.error(f"Error al actualizar estado: {str(e)}")
            # No devolvemos error porque la película ya está agregada
            return {"message": "Película agregada y descarga iniciada, pero hubo un error al actualizar el estado"}, 200
            
        return {"message": "Película agregada y descarga iniciada"}, 200
            
    except Exception as e:
        app.logger.error(f"Error al agregar película: {str(e)}")
        return {"error": f"Error interno del servidor: {str(e)}"}, 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Error interno del servidor"), 500

def add_to_transmission(magnet):
    """Agrega torrent a Transmission vía API"""
    try:
        app.logger.info(f"Intentando agregar torrent: {magnet[:60]}...")
        session = requests.Session()
        session.auth = (TRANSMISSION_USER, TRANSMISSION_PASS)
        
        # Primera llamada para obtener el token
        app.logger.info(f"Obteniendo token de Transmission desde {TRANSMISSION_URL}")
        resp = session.post(TRANSMISSION_URL)
        app.logger.info(f"Respuesta inicial: Status {resp.status_code}")
        
        if resp.status_code == 409:  # Se espera este código cuando falta el token
            token = resp.headers.get('X-Transmission-Session-Id')
            app.logger.info(f"Token recibido: {token}")
            session.headers.update({
                'X-Transmission-Session-Id': token
            })
        else:
            app.logger.error(f"Error inesperado al obtener token. Status: {resp.status_code}")
            return None
        
        # Llamada real para agregar el torrent
        payload = {
            "method": "torrent-add",
            "arguments": {
                "filename": magnet,
                "download-dir": "/downloads/complete",
                "paused": False
            }
        }
        
        app.logger.info("Enviando solicitud para agregar torrent")
        resp = session.post(TRANSMISSION_URL, json=payload)
        app.logger.info(f"Respuesta de agregar torrent: Status {resp.status_code}")
        
        if resp.status_code != 200:
            app.logger.error(f"Error al agregar torrent: Status code {resp.status_code}")
            app.logger.error(f"Respuesta: {resp.text}")
            return None
            
        result = resp.json()
        app.logger.info(f"Respuesta JSON: {result}")
        
        if "result" in result and result["result"] == "success":
            app.logger.info("Torrent agregado exitosamente")
            return result
            
        app.logger.error(f"Error en respuesta de Transmission: {result}")
        return None
    except Exception as e:
        app.logger.error(f"Error al agregar torrent: {str(e)}")
        app.logger.error(f"Detalles del error: {repr(e)}")
        return None

@app.route('/download/<int:movie_id>', methods=['POST'])
def download_movie(movie_id):
    """Inicia la descarga de una película en Transmission"""
    try:
        movies = load_movies()
        if 0 <= movie_id < len(movies):
            movie = movies[movie_id]
            result = add_to_transmission(movie['magnet'])
            
            if result and 'result' in result and result['result'] == 'success':
                movies[movie_id]['status'] = 'descargando'
                save_movies(movies)
                return {"message": "Descarga iniciada"}, 200
            else:
                return {"error": "Error al iniciar la descarga"}, 500
        return {"error": "Película no encontrada"}, 404
    except Exception as e:
        app.logger.error(f"Error en descarga: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


