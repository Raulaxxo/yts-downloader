from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import urllib.parse
import json
import os

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()

# Inicializar la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Cambiar en producción
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones con la app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

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
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Cambiar en producción
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones con la app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Inicializar modelos
from models.user_model import User
UserModel, Download = User.init_model(db)

# Registrar build_magnet en el contexto de Jinja2
app.jinja_env.globals['build_magnet'] = build_magnet

# Crear las tablas de la base de datos
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))

# Transmission configuración (dentro de Docker Compose)
TRANSMISSION_URL = "http://transmission:9091/transmission/rpc"
TRANSMISSION_USER = "admin"
TRANSMISSION_PASS = "1234"

# --- Funciones auxiliares ---
def update_movie_status(download_id, new_status):
    """Actualiza el estado de una película en la base de datos"""
    try:
        download = Download.query.get(download_id)
        if download:
            download.status = new_status
            db.session.commit()
            return True
        return False
    except Exception as e:
        app.logger.error(f"Error al actualizar estado: {str(e)}")
        return False

# --- Rutas de Autenticación ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = UserModel.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
            
        if UserModel.query.filter_by(username=username).first():
            flash('El nombre de usuario ya está en uso', 'error')
            return render_template('register.html')
            
        hashed_password = generate_password_hash(password)
        new_user = UserModel(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('¡Registro exitoso! Por favor inicia sesión', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'¡Hasta pronto, {username}! Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('login'))

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



@app.route('/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete_movie(movie_id):
    """Elimina una película de la lista y de Transmission"""
    try:
        download = Download.query.filter_by(id=movie_id, user_id=current_user.id).first()
        if not download:
            return {"error": "Película no encontrada"}, 404
            
        # Si la película está en descarga o completada, la eliminamos de Transmission
        if download.status in ['descargando', 'completado']:
            # Extraer el hash del magnet link
            magnet = download.magnet
            hash_match = magnet.split('btih:')[1].split('&')[0] if 'btih:' in magnet else None
            
            if hash_match:
                app.logger.info(f"Intentando eliminar torrent con hash: {hash_match}")
                if not delete_from_transmission(hash_match):
                    app.logger.warning("No se pudo eliminar el torrent de Transmission")
            else:
                app.logger.warning("No se encontró el hash en el magnet link")
        
        # Eliminar de la base de datos
        db.session.delete(download)
        db.session.commit()
        
        return {"message": "Película eliminada"}, 200
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
@login_required
def index():
    """Página principal que muestra las películas del usuario"""
    if not session.get('welcomed'):
        flash(f'¡Bienvenido de nuevo, {current_user.username}!', 'success')
        session['welcomed'] = True
    
    user_downloads = Download.query.filter_by(user_id=current_user.id).order_by(Download.download_date.desc()).all()
    return render_template('index.html', movies=user_downloads, is_all_movies=False)

@app.route('/all')
@login_required
def all_movies():
    """Muestra todas las películas de todos los usuarios"""
    movies = Download.query.order_by(Download.download_date.desc()).all()
    return render_template('all_movies.html', movies=movies)

@app.route('/search')
@login_required
def search():
    """Página de búsqueda de películas"""
    query = request.args.get('query', '')
    page = request.args.get('page', '1')
    try:
        page = int(page)
    except ValueError:
        page = 1
    
    results = []
    total_results = 0
    
    if query:
        try:
            url = f"https://yts.mx/api/v2/list_movies.json"
            params = {
                "query_term": query,
                "limit": 24,  # Mostrar más resultados por página
                "page": page,
                "sort_by": "year",  # Ordenar por año
                "order_by": "desc"  # Más recientes primero
            }
            
            resp = requests.get(url, params=params).json()
            if resp["status"] == "ok":
                movie_data = resp["data"]
                if movie_data.get("movies"):
                    results = movie_data["movies"]
                    total_results = movie_data.get("movie_count", 0)
        except Exception as e:
            app.logger.error(f"Error en búsqueda: {str(e)}")
            flash('Error al realizar la búsqueda. Por favor, intenta de nuevo.', 'error')
    
    return render_template(
        'search.html',
        results=results,
        query=query,
        page=page,
        total_results=total_results,
        total_pages=(total_results + 23) // 24  # Redondear hacia arriba
    )

@app.route('/add', methods=['POST'])
@login_required
def add_movie():
    """Agrega una nueva película a la lista"""
    try:
        movie_data = request.get_json()
        if not movie_data:
            return {"error": "Datos de película requeridos"}, 400

        required_fields = ['title', 'magnet']
        missing_fields = [field for field in required_fields if field not in movie_data]
        if missing_fields:
            return {"error": f"Campos requeridos faltantes: {', '.join(missing_fields)}"}, 400

        # Verificar si la película ya existe para este usuario
        existing_movie = Download.query.filter_by(
            user_id=current_user.id,
            movie_title=movie_data['title']
        ).first()
        
        if existing_movie:
            return {"error": "Ya has agregado esta película"}, 409

        # Crear una nueva entrada en la tabla Download
        new_download = Download(
            movie_title=movie_data['title'],
            movie_id=movie_data.get('imdb_code', ''),
            magnet=movie_data['magnet'],
            year=movie_data.get('year', ''),
            rating=movie_data.get('rating', ''),
            imdb_code=movie_data.get('imdb_code', ''),
            status='pendiente',
            user_id=current_user.id
        )
        db.session.add(new_download)
        db.session.commit()

        # Iniciar la descarga en Transmission
        result = add_to_transmission(movie_data['magnet'])
        
        if result:
            # Actualizar el estado si se agregó correctamente
            update_movie_status(new_download.id, 'descargando')
            flash('Película agregada y descarga iniciada', 'success')
            return {"message": "Película agregada y descarga iniciada"}, 200
        else:
            # Si falla la descarga, mantener como pendiente
            flash('Película agregada pero hubo un error al iniciar la descarga', 'warning')
            return {"message": "Película agregada pero error al iniciar descarga"}, 200
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
@login_required
def download_movie(movie_id):
    """Inicia la descarga de una película en Transmission"""
    try:
        download = Download.query.filter_by(id=movie_id, user_id=current_user.id).first()
        if not download:
            return {"error": "Película no encontrada"}, 404
            
        result = add_to_transmission(download.magnet)
        
        if result and 'result' in result and result['result'] == 'success':
            update_movie_status(movie_id, 'descargando')
            return {"message": "Descarga iniciada"}, 200
        else:
            return {"error": "Error al iniciar la descarga"}, 500
    except Exception as e:
        app.logger.error(f"Error en descarga: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


