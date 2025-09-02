from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import urllib.parse
import json
import os
import uuid

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

# Inicializar modelos
from models.user_model import User
UserModel, Download, MovieList, MovieListItem, Friendship = User.init_model(db)

# Registrar build_magnet en el contexto de Jinja2
app.jinja_env.globals['build_magnet'] = build_magnet

# Crear las tablas de la base de datos
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return UserModel.query.get(int(user_id))

# Configuración de Transmission y Plex
TRANSMISSION_URL = "http://transmission:9091/transmission/rpc"
TRANSMISSION_USER = "admin"
TRANSMISSION_PASS = "1234"
PLEX_URL = "http://plex:32400"
PLEX_TOKEN = ""  # Se puede configurar después

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

def get_transmission_session():
    """Obtiene una sesión autenticada de Transmission"""
    try:
        session = requests.Session()
        session.auth = (TRANSMISSION_USER, TRANSMISSION_PASS)
        
        # Primera llamada para obtener el token
        resp = session.post(TRANSMISSION_URL)
        
        if resp.status_code == 409:
            token = resp.headers.get('X-Transmission-Session-Id')
            session.headers.update({
                'X-Transmission-Session-Id': token
            })
            return session
        else:
            app.logger.error(f"Error al obtener token de Transmission: {resp.status_code}")
            return None
    except Exception as e:
        app.logger.error(f"Error al conectar con Transmission: {str(e)}")
        return None

def refresh_plex_library():
    """Actualiza la biblioteca de Plex"""
    try:
        # Si no hay token configurado, intentar sin autenticación (para redes locales)
        headers = {}
        if PLEX_TOKEN:
            headers['X-Plex-Token'] = PLEX_TOKEN
        
        # Obtener las secciones de biblioteca
        sections_url = f"{PLEX_URL}/library/sections"
        resp = requests.get(sections_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            app.logger.warning(f"No se pudo obtener secciones de Plex: {resp.status_code}")
            return False
        
        # Buscar la sección de películas
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.content)
        movie_section_id = None
        
        for directory in root.findall('.//Directory'):
            if directory.get('type') == 'movie':
                movie_section_id = directory.get('key')
                break
        
        if not movie_section_id:
            app.logger.warning("No se encontró sección de películas en Plex")
            return False
        
        # Actualizar la sección de películas
        refresh_url = f"{PLEX_URL}/library/sections/{movie_section_id}/refresh"
        resp = requests.get(refresh_url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            app.logger.info("Biblioteca de Plex actualizada exitosamente")
            return True
        else:
            app.logger.error(f"Error al actualizar Plex: {resp.status_code}")
            return False
            
    except Exception as e:
        app.logger.error(f"Error al conectar con Plex: {str(e)}")
        return False

def check_downloads_status():
    """Consulta el estado de todas las descargas en Transmission y actualiza la BD"""
    try:
        session = get_transmission_session()
        if not session:
            return False
        
        # Obtener lista de torrents
        payload = {
            "method": "torrent-get",
            "arguments": {
                "fields": ["id", "name", "status", "percentDone", "error", "errorString"]
            }
        }
        
        resp = session.post(TRANSMISSION_URL, json=payload)
        if resp.status_code != 200:
            app.logger.error(f"Error al obtener torrents: {resp.status_code}")
            return False
        
        result = resp.json()
        torrents = result.get('arguments', {}).get('torrents', [])
        
        # Obtener todas las descargas activas de la BD
        active_downloads = Download.query.filter(
            Download.status.in_(['pendiente', 'descargando'])
        ).all()
        
        newly_completed = []  # Lista de películas recién completadas
        
        for download in active_downloads:
            # Buscar el torrent correspondiente por nombre
            movie_title = download.movie_title.lower()
            matching_torrent = None
            
            for torrent in torrents:
                torrent_name = torrent.get('name', '').lower()
                if movie_title in torrent_name or torrent_name in movie_title:
                    matching_torrent = torrent
                    break
            
            if matching_torrent:
                torrent_status = matching_torrent.get('status')
                percent_done = matching_torrent.get('percentDone', 0)
                error = matching_torrent.get('error')
                
                # Estados de Transmission:
                # 0: Torrent is stopped
                # 1: Queued to check files
                # 2: Checking files
                # 3: Queued to download
                # 4: Downloading
                # 5: Queued to seed
                # 6: Seeding
                
                new_status = None
                if error and error != 0:
                    new_status = 'error'
                elif torrent_status in [4] and percent_done < 1.0:  # Descargando
                    new_status = 'descargando'
                elif torrent_status in [5, 6] or percent_done >= 1.0:  # Completado
                    new_status = 'completado'
                    # Si cambió a completado, agregar a la lista
                    if download.status != 'completado':
                        newly_completed.append(download.movie_title)
                elif torrent_status in [0, 1, 2, 3]:  # Parado o en cola
                    new_status = 'pendiente'
                
                if new_status and new_status != download.status:
                    app.logger.info(f"Actualizando estado de '{download.movie_title}': {download.status} -> {new_status}")
                    update_movie_status(download.id, new_status)
        
        # Si hay películas recién completadas, actualizar Plex
        if newly_completed:
            app.logger.info(f"Películas completadas: {', '.join(newly_completed)}")
            refresh_plex_library()
        
        return True
        
    except Exception as e:
        app.logger.error(f"Error al verificar estados de descarga: {str(e)}")
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
        session = get_transmission_session()
        if not session:
            return None
        
        # Llamada para agregar el torrent
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

@app.route('/api/check-status', methods=['POST'])
@login_required
def check_status():
    """Verifica y actualiza el estado de todas las descargas"""
    try:
        success = check_downloads_status()
        if success:
            return {"message": "Estados actualizados correctamente"}, 200
        else:
            return {"error": "Error al verificar estados"}, 500
    except Exception as e:
        app.logger.error(f"Error al verificar estados: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

@app.route('/api/transmission-status')
@login_required
def transmission_status():
    """Obtiene el estado de conexión con Transmission"""
    try:
        session = get_transmission_session()
        if not session:
            return {"connected": False, "message": "No se pudo conectar con Transmission"}, 500
        
        # Hacer una consulta simple para verificar la conexión
        payload = {
            "method": "session-get",
            "arguments": {}
        }
        
        resp = session.post(TRANSMISSION_URL, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            session_info = result.get('arguments', {})
            return {
                "connected": True, 
                "message": "Conectado correctamente",
                "version": session_info.get('version', 'Desconocida')
            }, 200
        else:
            return {"connected": False, "message": f"Error de conexión: {resp.status_code}"}, 500
            
    except Exception as e:
        app.logger.error(f"Error al verificar Transmission: {str(e)}")
        return {"connected": False, "message": f"Error: {str(e)}"}, 500

@app.route('/api/webhook/complete', methods=['POST'])
def webhook_complete():
    """Endpoint para el webhook de Transmission cuando se completa una descarga"""
    try:
        data = request.get_json()
        if not data or 'torrent_name' not in data:
            return {"error": "torrent_name requerido"}, 400
        
        torrent_name = data['torrent_name'].lower()
        app.logger.info(f"Webhook recibido para: {torrent_name}")
        
        # Buscar la película en la base de datos por nombre similar
        all_downloads = Download.query.filter(
            Download.status.in_(['pendiente', 'descargando'])
        ).all()
        
        movie_found = False
        for download in all_downloads:
            movie_title = download.movie_title.lower()
            
            # Comparar nombres (buscar coincidencias parciales)
            if (movie_title in torrent_name or 
                torrent_name in movie_title or
                any(word in torrent_name for word in movie_title.split() if len(word) > 3)):
                
                # Actualizar estado a completado
                download.status = 'completado'
                db.session.commit()
                
                app.logger.info(f"Película completada: {download.movie_title}")
                movie_found = True
                break
        
        if movie_found:
            return {
                "message": "Película marcada como completada", 
                "movie_found": True,
                "organization_info": {
                    "original_name": torrent_name,
                    "organized_path": "/downloads/movies/",
                    "note": "Los archivos serán organizados y renombrados automáticamente"
                }
            }, 200
        else:
            app.logger.warning(f"No se encontró película para torrent: {torrent_name}")
            return {
                "message": "Torrent no encontrado en base de datos", 
                "movie_found": False,
                "organization_info": {
                    "original_name": torrent_name,
                    "organized_path": "/downloads/movies/",
                    "note": "Archivos organizados automáticamente aunque no esté en la base de datos"
                }
            }, 200
            
    except Exception as e:
        app.logger.error(f"Error en webhook: {str(e)}")
        return {"error": f"Error interno: {str(e)}"}, 500

@app.route('/api/plex-refresh', methods=['POST'])
@login_required
def plex_refresh():
    """Actualiza manualmente la biblioteca de Plex"""
    try:
        success = refresh_plex_library()
        if success:
            return {"message": "Biblioteca de Plex actualizada correctamente"}, 200
        else:
            return {"error": "Error al actualizar la biblioteca de Plex"}, 500
    except Exception as e:
        app.logger.error(f"Error al actualizar Plex: {str(e)}")
        return {"error": "Error interno del servidor"}, 500

@app.route('/api/plex-status')
@login_required
def plex_status():
    """Verifica el estado de conexión con Plex"""
    try:
        headers = {}
        if PLEX_TOKEN:
            headers['X-Plex-Token'] = PLEX_TOKEN
        
        # Hacer una consulta simple para verificar la conexión
        resp = requests.get(f"{PLEX_URL}/library/sections", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            # Contar secciones de películas
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            movie_sections = [d for d in root.findall('.//Directory') if d.get('type') == 'movie']
            
            return {
                "connected": True,
                "message": "Conectado correctamente",
                "movie_sections": len(movie_sections)
            }, 200
        else:
            return {"connected": False, "message": f"Error de conexión: {resp.status_code}"}, 500
            
    except Exception as e:
        app.logger.error(f"Error al verificar Plex: {str(e)}")
        return {"connected": False, "message": f"Error: {str(e)}"}, 500

# === RUTAS PARA LISTAS DE PELÍCULAS ===

@app.route('/listas')
@login_required
def movie_lists():
    """Mostrar todas las listas del usuario actual"""
    user_lists = MovieList.query.filter_by(creator_id=current_user.id).order_by(MovieList.updated_at.desc()).all()
    return render_template('movie_lists.html', lists=user_lists)

@app.route('/api/listas')
@login_required
def api_movie_lists():
    """API: Obtener todas las listas del usuario actual en formato JSON"""
    user_lists = MovieList.query.filter_by(creator_id=current_user.id).order_by(MovieList.updated_at.desc()).all()
    
    lists_data = []
    for movie_list in user_lists:
        # Contar películas en la lista
        movie_count = MovieListItem.query.filter_by(list_id=movie_list.id).count()
        
        lists_data.append({
            'id': movie_list.id,
            'title': movie_list.title,
            'description': movie_list.description,
            'is_public': movie_list.is_public,
            'movie_count': movie_count,
            'created_at': movie_list.created_at.isoformat(),
            'updated_at': movie_list.updated_at.isoformat()
        })
    
    return jsonify(lists_data)

@app.route('/lista/nueva', methods=['GET', 'POST'])
@login_required
def new_movie_list():
    """Crear una nueva lista de películas"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            is_public = data.get('is_public', False)
            
            if not title:
                return {"error": "El título es obligatorio"}, 400
            
            # Crear nueva lista
            new_list = MovieList(
                title=title,
                description=description,
                is_public=is_public,
                creator_id=current_user.id
            )
            
            db.session.add(new_list)
            db.session.commit()
            
            return {
                "message": "Lista creada exitosamente",
                "list_id": new_list.id,
                "share_code": new_list.share_code
            }, 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al crear lista: {str(e)}")
            return {"error": "Error al crear la lista"}, 500
    
    return render_template('new_movie_list.html')

@app.route('/lista/<int:list_id>')
def view_movie_list(list_id):
    """Ver una lista específica de películas"""
    movie_list = MovieList.query.get_or_404(list_id)
    
    # Verificar permisos
    if not movie_list.is_public and (not current_user.is_authenticated or movie_list.creator_id != current_user.id):
        flash('No tienes permisos para ver esta lista', 'error')
        return redirect(url_for('search'))
    
    movies = MovieListItem.query.filter_by(list_id=list_id).order_by(MovieListItem.added_at.desc()).all()
    is_owner = current_user.is_authenticated and movie_list.creator_id == current_user.id
    
    return render_template('view_movie_list.html', 
                         movie_list=movie_list, 
                         movies=movies, 
                         is_owner=is_owner)

@app.route('/lista/compartir/<share_code>')
def shared_movie_list(share_code):
    """Ver una lista compartida usando el código de compartir"""
    movie_list = MovieList.query.filter_by(share_code=share_code).first_or_404()
    movies = MovieListItem.query.filter_by(list_id=movie_list.id).order_by(MovieListItem.added_at.desc()).all()
    is_owner = current_user.is_authenticated and movie_list.creator_id == current_user.id
    
    return render_template('view_movie_list.html', 
                         movie_list=movie_list, 
                         movies=movies, 
                         is_owner=is_owner,
                         is_shared_view=True)

@app.route('/lista/<int:list_id>/agregar', methods=['POST'])
@login_required
def add_movie_to_list(list_id):
    """Agregar una película a una lista"""
    movie_list = MovieList.query.get_or_404(list_id)
    
    # Verificar que el usuario sea el creador
    if movie_list.creator_id != current_user.id:
        return {"error": "No tienes permisos para modificar esta lista"}, 403
    
    try:
        data = request.get_json()
        
        # Verificar que la película no esté ya en la lista
        existing = MovieListItem.query.filter_by(
            list_id=list_id,
            imdb_code=data.get('imdb_code')
        ).first()
        
        if existing:
            return {"error": "La película ya está en la lista"}, 400
        
        # Agregar película a la lista
        movie_item = MovieListItem(
            movie_title=data.get('title', ''),
            year=data.get('year', ''),
            rating=data.get('rating', ''),
            imdb_code=data.get('imdb_code', ''),
            poster_url=data.get('poster_url', ''),
            notes=data.get('notes', ''),
            list_id=list_id
        )
        
        db.session.add(movie_item)
        movie_list.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"message": "Película agregada a la lista exitosamente"}, 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al agregar película a lista: {str(e)}")
        return {"error": "Error al agregar la película"}, 500

@app.route('/lista/<int:list_id>/pelicula/<int:movie_id>/toggle-watched', methods=['POST'])
@login_required
def toggle_watched(list_id, movie_id):
    """Marcar/desmarcar película como vista"""
    movie_list = MovieList.query.get_or_404(list_id)
    
    if movie_list.creator_id != current_user.id:
        return {"error": "No tienes permisos para modificar esta lista"}, 403
    
    try:
        movie_item = MovieListItem.query.filter_by(id=movie_id, list_id=list_id).first_or_404()
        movie_item.watched = not movie_item.watched
        movie_list.updated_at = datetime.utcnow()
        db.session.commit()
        
        status = "vista" if movie_item.watched else "no vista"
        return {"message": f"Película marcada como {status}", "watched": movie_item.watched}, 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al actualizar estado: {str(e)}")
        return {"error": "Error al actualizar el estado"}, 500

@app.route('/lista/<int:list_id>/pelicula/<int:movie_id>/eliminar', methods=['POST'])
@login_required
def remove_from_list(list_id, movie_id):
    """Eliminar película de una lista"""
    movie_list = MovieList.query.get_or_404(list_id)
    
    if movie_list.creator_id != current_user.id:
        return {"error": "No tienes permisos para modificar esta lista"}, 403
    
    try:
        movie_item = MovieListItem.query.filter_by(id=movie_id, list_id=list_id).first_or_404()
        db.session.delete(movie_item)
        movie_list.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"message": "Película eliminada de la lista"}, 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar película: {str(e)}")
        return {"error": "Error al eliminar la película"}, 500

@app.route('/lista/<int:list_id>/eliminar', methods=['POST'])
@login_required
def delete_movie_list(list_id):
    """Eliminar una lista completa"""
    movie_list = MovieList.query.get_or_404(list_id)
    
    if movie_list.creator_id != current_user.id:
        return {"error": "No tienes permisos para eliminar esta lista"}, 403
    
    try:
        db.session.delete(movie_list)
        db.session.commit()
        
        return {"message": "Lista eliminada exitosamente"}, 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al eliminar lista: {str(e)}")
        return {"error": "Error al eliminar la lista"}, 500

# === RUTAS DE AMISTAD ===

@app.route('/amigos')
@login_required
def friends():
    """Página principal de amigos"""
    # Obtener amigos aceptados
    friends_query = db.session.query(Friendship).filter(
        ((Friendship.requester_id == current_user.id) | (Friendship.addressee_id == current_user.id)),
        Friendship.status == 'accepted'
    ).all()
    
    friends_list = []
    for friendship in friends_query:
        friend_id = friendship.addressee_id if friendship.requester_id == current_user.id else friendship.requester_id
        friend = UserModel.query.get(friend_id)
        if friend:
            friends_list.append({
                'id': friend.id,
                'username': friend.username,
                'friendship_since': friendship.responded_at or friendship.requested_at
            })
    
    # Obtener solicitudes pendientes recibidas
    pending_requests = db.session.query(Friendship).filter(
        Friendship.addressee_id == current_user.id,
        Friendship.status == 'pending'
    ).all()
    
    pending_list = []
    for request in pending_requests:
        requester = UserModel.query.get(request.requester_id)
        if requester:
            pending_list.append({
                'id': request.id,
                'username': requester.username,
                'requested_at': request.requested_at
            })
    
    return render_template('friends.html', friends=friends_list, pending_requests=pending_list)

@app.route('/buscar-usuarios')
@login_required
def search_users():
    """Buscar usuarios para agregar como amigos"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    # Buscar usuarios (excluyendo al usuario actual)
    users = UserModel.query.filter(
        UserModel.username.like(f'%{query}%'),
        UserModel.id != current_user.id
    ).limit(10).all()
    
    results = []
    for user in users:
        # Verificar si ya son amigos o hay solicitud pendiente
        existing = Friendship.query.filter(
            ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user.id)) |
            ((Friendship.requester_id == user.id) & (Friendship.addressee_id == current_user.id))
        ).first()
        
        status = 'none'
        if existing:
            if existing.status == 'accepted':
                status = 'friends'
            elif existing.status == 'pending':
                if existing.requester_id == current_user.id:
                    status = 'sent'
                else:
                    status = 'received'
            elif existing.status == 'blocked':
                status = 'blocked'
        
        results.append({
            'id': user.id,
            'username': user.username,
            'status': status
        })
    
    return jsonify(results)

@app.route('/solicitud-amistad', methods=['POST'])
@login_required
def send_friend_request():
    """Enviar solicitud de amistad"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id or user_id == current_user.id:
        return {"error": "Usuario inválido"}, 400
    
    # Verificar que el usuario existe
    target_user = UserModel.query.get(user_id)
    if not target_user:
        return {"error": "Usuario no encontrado"}, 404
    
    # Verificar si ya existe una relación
    existing = Friendship.query.filter(
        ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user_id)) |
        ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current_user.id))
    ).first()
    
    if existing:
        if existing.status == 'accepted':
            return {"error": "Ya son amigos"}, 400
        elif existing.status == 'pending':
            return {"error": "Ya hay una solicitud pendiente"}, 400
        elif existing.status == 'blocked':
            return {"error": "No se puede enviar solicitud"}, 400
    
    try:
        # Crear nueva solicitud
        friendship = Friendship(
            requester_id=current_user.id,
            addressee_id=user_id,
            status='pending'
        )
        db.session.add(friendship)
        db.session.commit()
        
        return {"message": "Solicitud de amistad enviada"}, 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error enviando solicitud: {str(e)}")
        return {"error": "Error al enviar solicitud"}, 500

@app.route('/responder-amistad/<int:request_id>', methods=['POST'])
@login_required
def respond_friend_request(request_id):
    """Responder a solicitud de amistad"""
    data = request.get_json()
    action = data.get('action')  # 'accept' o 'reject'
    
    if action not in ['accept', 'reject']:
        return {"error": "Acción inválida"}, 400
    
    # Obtener la solicitud
    friendship = Friendship.query.filter(
        Friendship.id == request_id,
        Friendship.addressee_id == current_user.id,
        Friendship.status == 'pending'
    ).first()
    
    if not friendship:
        return {"error": "Solicitud no encontrada"}, 404
    
    try:
        friendship.status = 'accepted' if action == 'accept' else 'rejected'
        friendship.responded_at = datetime.utcnow()
        db.session.commit()
        
        message = "Solicitud aceptada" if action == 'accept' else "Solicitud rechazada"
        return {"message": message}, 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error respondiendo solicitud: {str(e)}")
        return {"error": "Error al responder solicitud"}, 500

@app.route('/eliminar-amigo/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    """Eliminar amistad"""
    friendship = Friendship.query.filter(
        ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user_id)) |
        ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current_user.id)),
        Friendship.status == 'accepted'
    ).first()
    
    if not friendship:
        return {"error": "Amistad no encontrada"}, 404
    
    try:
        db.session.delete(friendship)
        db.session.commit()
        
        return {"message": "Amistad eliminada"}, 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error eliminando amistad: {str(e)}")
        return {"error": "Error al eliminar amistad"}, 500

@app.route('/amigo/<int:friend_id>/descargas')
@login_required
def friend_downloads(friend_id):
    """Ver descargas de un amigo"""
    # Verificar que son amigos
    friendship = Friendship.query.filter(
        ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == friend_id)) |
        ((Friendship.requester_id == friend_id) & (Friendship.addressee_id == current_user.id)),
        Friendship.status == 'accepted'
    ).first()
    
    if not friendship:
        return {"error": "No son amigos"}, 403
    
    friend = UserModel.query.get_or_404(friend_id)
    downloads = Download.query.filter_by(user_id=friend_id).order_by(Download.download_date.desc()).all()
    
    return render_template('friend_downloads.html', friend=friend, downloads=downloads)

@app.route('/amigo/<int:friend_id>/listas')
@login_required
def friend_lists(friend_id):
    """Ver listas públicas de un amigo"""
    # Verificar que son amigos
    friendship = Friendship.query.filter(
        ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == friend_id)) |
        ((Friendship.requester_id == friend_id) & (Friendship.addressee_id == current_user.id)),
        Friendship.status == 'accepted'
    ).first()
    
    if not friendship:
        return {"error": "No son amigos"}, 403
    
    friend = UserModel.query.get_or_404(friend_id)
    # Solo mostrar listas públicas
    friend_lists = MovieList.query.filter_by(creator_id=friend_id, is_public=True).order_by(MovieList.updated_at.desc()).all()
    
    return render_template('friend_lists.html', friend=friend, lists=friend_lists)

# === RUTAS DE PERFIL ===

def ensure_profile_fields(user):
    """Asegurar que el usuario tenga todos los campos del perfil"""
    try:
        needs_save = False
        
        if not user.full_name:
            user.full_name = user.username.title()
            needs_save = True
            
        if not user.email:
            user.email = f'{user.username}@example.com'
            needs_save = True
            
        if not user.bio:
            if user.created_at:
                try:
                    month_year = user.created_at.strftime('%B %Y')
                    user.bio = f'Usuario registrado desde {month_year}'
                except:
                    user.bio = 'Usuario de la plataforma YTS Downloader'
            else:
                user.bio = 'Usuario de la plataforma YTS Downloader'
            needs_save = True
            
        if user.is_public is None:
            user.is_public = True
            needs_save = True
            
        if user.show_stats is None:
            user.show_stats = True
            needs_save = True
            
        if user.email_notifications is None:
            user.email_notifications = True
            needs_save = True
        
        if needs_save:
            try:
                db.session.commit()
            except Exception as e:
                print(f"Error saving profile fields: {e}")
                db.session.rollback()
        
        return user
        
    except Exception as e:
        print(f"Error in ensure_profile_fields: {e}")
        return user

@app.route('/perfil')
@login_required
def profile():
    """Ver perfil del usuario actual"""
    try:
        # Asegurar que el usuario tenga todos los campos del perfil
        ensure_profile_fields(current_user)
        
        # Calcular estadísticas básicas
        stats = {
            'downloads': 0,
            'lists': 0,
            'friends': 0
        }
        
        try:
            stats['downloads'] = Download.query.filter_by(user_id=current_user.id).count()
        except Exception as e:
            print(f"Error calculando downloads: {e}")
        
        try:
            stats['lists'] = MovieList.query.filter_by(creator_id=current_user.id).count()
        except Exception as e:
            print(f"Error calculando lists: {e}")
        
        try:
            stats['friends'] = db.session.query(Friendship).filter(
                ((Friendship.requester_id == current_user.id) | (Friendship.addressee_id == current_user.id)),
                Friendship.status == 'accepted'
            ).count()
        except Exception as e:
            print(f"Error calculando friends: {e}")
        
        # Obtener listas y descargas del usuario de manera segura
        lists = []
        downloads = []
        
        try:
            # Obtener listas sin cargar relaciones problemáticas
            lists_query = MovieList.query.filter_by(creator_id=current_user.id).limit(10)
            lists = lists_query.all()
            print(f"Lists encontradas: {len(lists)}")
        except Exception as e:
            print(f"Error obteniendo listas: {e}")
            lists = []
        
        try:
            downloads = Download.query.filter_by(user_id=current_user.id).order_by(Download.download_date.desc()).limit(10).all()
            print(f"Downloads encontradas: {len(downloads)}")
        except Exception as e:
            print(f"Error obteniendo descargas: {e}")
            downloads = []
        
        return render_template('profile_enhanced.html', user=current_user, stats=stats, lists=lists, downloads=downloads)
        
    except Exception as e:
        print(f"Error general en profile(): {e}")
        import traceback
        traceback.print_exc()
        return f"Error en perfil: {str(e)}", 500

@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Editar perfil del usuario"""
    # Asegurar que el usuario tenga todos los campos del perfil
    ensure_profile_fields(current_user)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Actualizar campos del perfil
            current_user.full_name = data.get('full_name', '').strip()
            current_user.email = data.get('email', '').strip()
            current_user.bio = data.get('bio', '').strip()
            current_user.location = data.get('location', '').strip()
            current_user.avatar_url = data.get('avatar_url', '').strip()
            
            # Configuraciones
            current_user.is_public = data.get('is_public', True)
            current_user.show_stats = data.get('show_stats', True)
            current_user.email_notifications = data.get('email_notifications', True)
            
            # Validar email si se proporcionó
            if current_user.email:
                existing_user = UserModel.query.filter(
                    UserModel.email == current_user.email,
                    UserModel.id != current_user.id
                ).first()
                
                if existing_user:
                    return {"error": "Este email ya está en uso"}, 400
            
            db.session.commit()
            return {"message": "Perfil actualizado exitosamente"}
            
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/perfil/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Subir imagen de avatar"""
    try:
        if 'avatar_file' not in request.files:
            return {"error": "No se ha seleccionado ningún archivo"}, 400
        
        file = request.files['avatar_file']
        if file.filename == '':
            return {"error": "No se ha seleccionado ningún archivo"}, 400
        
        # Validar tipo de archivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return {"error": "Tipo de archivo no permitido. Usa: PNG, JPG, JPEG, GIF, WEBP"}, 400
        
        # Validar tamaño (5MB)
        file.seek(0, 2)  # Ir al final del archivo
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return {"error": "El archivo es demasiado grande. Máximo 5MB"}, 400
        
        # Generar nombre único para el archivo
        unique_filename = f"{uuid.uuid4().hex}_{current_user.id}.{file_extension}"
        
        # Crear directorio de avatares si no existe
        avatar_dir = os.path.join('static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(avatar_dir, unique_filename)
        file.save(file_path)
        
        # Generar URL para acceder al archivo
        avatar_url = f"/static/avatars/{unique_filename}"
        
        return {"url": avatar_url, "message": "Avatar subido exitosamente"}
        
    except Exception as e:
        print(f"Error subiendo avatar: {e}")
        return {"error": "Error interno del servidor"}, 500

@app.route('/perfil/<int:user_id>')
@login_required
def view_profile(user_id):
    """Ver perfil de otro usuario"""
    user = UserModel.query.get_or_404(user_id)
    
    # Asegurar que el usuario tenga todos los campos del perfil
    ensure_profile_fields(user)
    
    # Verificar si el perfil es público o si son amigos
    is_friend = False
    if user_id != current_user.id:
        friendship = Friendship.query.filter(
            ((Friendship.requester_id == current_user.id) & (Friendship.addressee_id == user_id)) |
            ((Friendship.requester_id == user_id) & (Friendship.addressee_id == current_user.id)),
            Friendship.status == 'accepted'
        ).first()
        is_friend = bool(friendship)
        
        if not user.is_public and not is_friend:
            return {"error": "Este perfil es privado"}, 403
    
    # Calcular estadísticas si están habilitadas
    stats = None
    if user.show_stats or user_id == current_user.id or is_friend:
        total_downloads = Download.query.filter_by(user_id=user_id).count()
        total_lists = MovieList.query.filter_by(creator_id=user_id).count()
        total_friends = db.session.query(Friendship).filter(
            ((Friendship.requester_id == user_id) | (Friendship.addressee_id == user_id)),
            Friendship.status == 'accepted'
        ).count()
        
        stats = {
            'downloads': total_downloads,
            'lists': total_lists,
            'friends': total_friends
        }
    
    return render_template('profile.html', user=user, stats=stats, is_friend=is_friend)

@app.route('/test-modals')
def test_modals():
    """Página de prueba para modales"""
    return render_template('test_modals.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


