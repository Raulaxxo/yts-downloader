#!/usr/bin/env python3
"""
Webhook script que se ejecuta cuando se completa una descarga en Transmission
"""
import sys
import os
import sqlite3
import logging
import requests
import subprocess
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/transmission_webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# URLs de servicios
FLASK_URL = "http://localhost:5000"
PLEX_URL = "http://plex:32400"
PLEX_TOKEN = os.getenv('PLEX_TOKEN', '')

def update_movie_status_in_db(torrent_name):
    """Actualiza el estado de la película en la base de datos"""
    try:
        # Buscar la película por nombre y marcarla como completada
        response = requests.post(f"{FLASK_URL}/api/webhook/complete", 
                               json={"torrent_name": torrent_name},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Estado actualizado: {data.get('message', 'OK')}")
            return data.get('movie_found', False)
        else:
            logger.error(f"Error al actualizar estado: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error conectando con Flask: {e}")
        return False

def organize_files(torrent_name, torrent_dir):
    """Organiza y limpia los archivos descargados"""
    try:
        logger.info(f"🗂️  Organizando archivos para: {torrent_name}")
        
        # Configurar variables de entorno para el organizador
        env = os.environ.copy()
        env['TR_TORRENT_NAME'] = torrent_name
        env['TR_TORRENT_DIR'] = torrent_dir
        
        # Ejecutar el organizador de archivos
        result = subprocess.run([
            'python3', '/app/file_organizer.py'
        ], env=env, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Archivos organizados correctamente")
            return True
        else:
            logger.error(f"❌ Error organizando archivos: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("⏰ Timeout organizando archivos")
        return False
    except Exception as e:
        logger.error(f"❌ Error ejecutando organizador: {e}")
        return False

def refresh_plex_library():
    """Actualiza la biblioteca de Plex después de organizar archivos"""
    try:
        # URL de tu servidor Plex
        plex_url = "http://plex:32400"
        
        # Token de acceso de Plex (puedes obtenerlo desde Plex Web)
        # Por ahora, intentaremos sin token para un escaneo básico
        scan_url = f"{plex_url}/library/sections/all/refresh"
        
        # Hacer petición a Plex
        response = requests.post(scan_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Plex notificado para actualizar biblioteca")
            return True
        else:
            logger.warning(f"⚠️  Respuesta inesperada de Plex: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error conectando con Plex: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error notificando Plex: {e}")
        return False

def main():
    """Función principal del webhook"""
    logger.info("🎬 Webhook de Transmission ejecutado")
    
    # Obtener información del torrent desde variables de entorno
    # Transmission pasa estas variables automáticamente
    torrent_name = os.getenv('TR_TORRENT_NAME', '')
    torrent_dir = os.getenv('TR_TORRENT_DIR', '')
    torrent_hash = os.getenv('TR_TORRENT_HASH', '')
    
    if not torrent_name:
        logger.error("❌ No se recibió nombre del torrent")
        sys.exit(1)
    
    logger.info(f"📁 Torrent completado: {torrent_name}")
    logger.info(f"📂 Directorio: {torrent_dir}")
    logger.info(f"🔢 Hash: {torrent_hash}")
    
    # 1. Organizar y limpiar archivos
    logger.info("🗂️  Organizando archivos...")
    files_organized = organize_files(torrent_name, torrent_dir)
    
    # 2. Actualizar estado en la base de datos
    logger.info("📊 Actualizando estado en base de datos...")
    movie_found = update_movie_status_in_db(torrent_name)
    
    if movie_found:
        logger.info("✅ Película encontrada y estado actualizado")
    else:
        logger.warning("⚠️ Película no encontrada en base de datos")
    
    # 3. Actualizar Plex
    logger.info("🎭 Actualizando biblioteca de Plex...")
    plex_updated = refresh_plex_library()
    
    # 4. Resumen final
    if files_organized and movie_found and plex_updated:
        logger.info("🎉 ¡Webhook completado exitosamente!")
        logger.info("   ✅ Archivos organizados")
        logger.info("   ✅ Base de datos actualizada")
        logger.info("   ✅ Plex notificado")
    else:
        logger.warning("⚠️ Webhook completado con advertencias:")
        logger.warning(f"   🗂️  Archivos organizados: {'✅' if files_organized else '❌'}")
        logger.warning(f"   📊 BD actualizada: {'✅' if movie_found else '❌'}")
        logger.warning(f"   🎭 Plex actualizado: {'✅' if plex_updated else '❌'}")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
