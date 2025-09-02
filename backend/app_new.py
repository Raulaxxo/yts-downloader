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

# Transmission configuración (dentro de Docker Compose)
TRANSMISSION_URL = "http://transmission:19091/transmission/rpc"
TRANSMISSION_USER = "admin"
TRANSMISSION_PASS = "1234"

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

# Registrar la función build_magnet en el contexto de Jinja2
app.jinja_env.globals['build_magnet'] = build_magnet

# --- Funciones auxiliares ---
def load_movies():
    try:
        with open(MOVIES_FILE) as f:
            return json.load(f)
    except:
        return []

def save_movies(movies):
    with open(MOVIES_FILE, "w") as f:
        json.dump(movies, f, indent=2)

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

        # Agregar a la lista
        movies.append(movie_info)
        save_movies(movies)
        
        # Iniciar descarga en Transmission
        session = requests.Session()
        session.auth = (TRANSMISSION_USER, TRANSMISSION_PASS)
        
        # Primera llamada para obtener el token
        resp = session.post(TRANSMISSION_URL)
        if resp.status_code == 409:
            token = resp.headers['X-Transmission-Session-Id']
            session.headers.update({'X-Transmission-Session-Id': token})
        
        # Llamada real para agregar el torrent
        data = {
            "method": "torrent-add",
            "arguments": {
                "filename": movie_info['magnet'],
                "paused": False
            }
        }
        resp = session.post(TRANSMISSION_URL, json=data)
        
        if resp.status_code == 200:
            return {"message": "Película agregada y descarga iniciada"}, 200
        else:
            return {"error": "Error al iniciar la descarga"}, 500
            
    except Exception as e:
        app.logger.error(f"Error al agregar película: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
