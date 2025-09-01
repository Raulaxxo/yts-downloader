from flask import Flask, request, render_template, redirect
import requests
import urllib.parse
import json

app = Flask(__name__)
MOVIES_FILE = "movies.json"

# Trackers recomendados
TRACKERS = [
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://tracker.openbittorrent.com:80",
    "udp://tracker.coppersurfer.tk:6969",
    "udp://tracker.leechers-paradise.org:6969"
]

# Transmission configuración (dentro de Docker Compose)
TRANSMISSION_URL = "http://transmission:9091/transmission/rpc"
TRANSMISSION_USER = "admin"
TRANSMISSION_PASS = "1234"

# --- Funciones ---
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

def build_magnet(movie):
    """Construye el magnet link usando el primer torrent en 1080p"""
    torrent = movie["torrents"][0]
    hash_ = torrent["hash"]
    name = urllib.parse.quote(movie["title_long"])
    magnet = f"magnet:?xt=urn:btih:{hash_}&dn={name}"
    for tr in TRACKERS:
        magnet += f"&tr={urllib.parse.quote(tr)}"
    return magnet

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

        # Preparar datos de la película
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
            'status': 'pendiente'
        }

        # Agregar a la lista
        movies.append(movie_info)
        save_movies(movies)

        return {"message": "Película agregada correctamente"}, 200
    except Exception as e:
        app.logger.error(f"Error al agregar película: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Página no encontrada"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Error interno del servidor"), 500
    return magnet

def add_to_transmission(magnet):
    """Agrega torrent a Transmission vía API"""
    headers = {"X-Transmission-Session-Id": ""}
    auth = (TRANSMISSION_USER, TRANSMISSION_PASS)

    # Obtener session-id de Transmission
    r = requests.post(TRANSMISSION_URL, auth=auth)
    headers["X-Transmission-Session-Id"] = r.headers.get("X-Transmission-Session-Id", "")

    payload = {"method": "torrent-add", "arguments": {"filename": magnet}}
    r = requests.post(TRANSMISSION_URL, json=payload, headers=headers, auth=auth)
    return r.json()

def get_subtitles_link(movie):
    """Devuelve link a subtítulos de YTS-subs usando IMDb ID"""
    return f"https://yts-subs.com/movie-imdb/{movie['imdb_code']}"

# --- Rutas ---
@app.route("/", methods=["GET", "POST"])
def index():
    movies = load_movies()
    if request.method == "POST":
        name = request.form["name"]
        movie_data = get_movie(name)
        if movie_data:
            magnet = build_magnet(movie_data)
            add_to_transmission(magnet)
            subs = get_subtitles_link(movie_data)
            movies.append({
                "title": movie_data["title_long"],
                "magnet": magnet,
                "subs": subs,
                "status": "Descargando"
            })
        else:
            movies.append({"title": name, "status": "No encontrado"})
        save_movies(movies)
        return redirect("/")
    return render_template("index.html", movies=movies)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


