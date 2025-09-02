#!/usr/bin/env python3
"""
Script para organizar y limpiar nombres de archivos completados
Se ejecuta cuando termina una descarga
"""
import os
import re
import shutil
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FileOrganizer:
    def __init__(self):
        self.download_dir = "/downloads/complete"
        self.incomplete_dir = "/downloads/incomplete"
        self.organized_dir = "/downloads/movies"  # Nueva carpeta organizada
        
        # Crear directorio organizado si no existe
        os.makedirs(self.organized_dir, exist_ok=True)
    
    def clean_movie_name(self, filename):
        """Limpia el nombre del archivo para que sea más legible"""
        # Remover extensión
        name_without_ext = os.path.splitext(filename)[0]
        
        # Patrones a remover (común en torrents)
        patterns_to_remove = [
            r'\[.*?\]',  # [YTS.MX], [RARBG], etc.
            r'\(.*?\)',  # (2023), (1080p), etc. - los mantendremos algunos
            r'www\..*?\.',  # URLs
            r'YTS\..*',  # YTS tags
            r'RARBG',
            r'x264.*',
            r'BluRay.*',
            r'WEBRip.*',
            r'HDTV.*',
            r'DVDRip.*',
            r'BRRip.*',
            r'\..*',  # Puntos adicionales
            r'-.*Team',  # Release teams
            r'PROPER',
            r'REPACK',
            r'INTERNAL',
            r'LIMITED',
            r'FESTIVAL',
            r'UNRATED',
            r'EXTENDED',
            r'DIRECTORS\.CUT',
        ]
        
        cleaned_name = name_without_ext
        
        # Aplicar limpieza de patrones
        for pattern in patterns_to_remove:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Limpiar espacios y caracteres especiales
        cleaned_name = re.sub(r'[\.\-_]+', ' ', cleaned_name)  # Reemplazar . - _ con espacios
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)  # Múltiples espacios a uno
        cleaned_name = cleaned_name.strip()
        
        # Intentar extraer año si está presente
        year_match = re.search(r'\b(19|20)\d{2}\b', cleaned_name)
        year = ""
        if year_match:
            year = year_match.group()
            # Remover el año del nombre principal
            cleaned_name = re.sub(r'\b(19|20)\d{2}\b', '', cleaned_name).strip()
        
        # Intentar extraer calidad
        quality_match = re.search(r'\b(720p|1080p|2160p|4K)\b', name_without_ext, re.IGNORECASE)
        quality = ""
        if quality_match:
            quality = quality_match.group()
        
        # Formato final: "Nombre Película (Año) [Calidad]"
        final_name = cleaned_name
        if year:
            final_name += f" ({year})"
        if quality:
            final_name += f" [{quality}]"
        
        return final_name.strip()
    
    def get_file_extension(self, filepath):
        """Obtiene la extensión del archivo de video principal"""
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        
        if os.path.isfile(filepath):
            _, ext = os.path.splitext(filepath)
            return ext if ext.lower() in video_extensions else '.mp4'
        
        # Si es un directorio, buscar el archivo de video más grande
        if os.path.isdir(filepath):
            largest_file = None
            largest_size = 0
            
            for root, dirs, files in os.walk(filepath):
                for file in files:
                    file_path = os.path.join(root, file)
                    _, ext = os.path.splitext(file)
                    
                    if ext.lower() in video_extensions:
                        file_size = os.path.getsize(file_path)
                        if file_size > largest_size:
                            largest_size = file_size
                            largest_file = file_path
            
            if largest_file:
                _, ext = os.path.splitext(largest_file)
                return ext
        
        return '.mp4'  # Default
    
    def organize_completed_download(self, torrent_name, torrent_dir):
        """Organiza el archivo/directorio completado"""
        try:
            source_path = os.path.join(torrent_dir, torrent_name)
            
            if not os.path.exists(source_path):
                logger.error(f"❌ Archivo fuente no encontrado: {source_path}")
                return False
            
            # Limpiar nombre
            clean_name = self.clean_movie_name(torrent_name)
            extension = self.get_file_extension(source_path)
            
            # Nombre final del archivo
            final_filename = f"{clean_name}{extension}"
            destination_path = os.path.join(self.organized_dir, final_filename)
            
            logger.info(f"📁 Organizando: {torrent_name}")
            logger.info(f"➡️  Nuevo nombre: {final_filename}")
            
            # Si es un archivo único, simplemente moverlo y renombrarlo
            if os.path.isfile(source_path):
                shutil.move(source_path, destination_path)
                logger.info(f"✅ Archivo movido a: {destination_path}")
                
            # Si es un directorio con múltiples archivos
            elif os.path.isdir(source_path):
                # Buscar el archivo de video principal
                main_video_file = self.find_main_video_file(source_path)
                
                if main_video_file:
                    # Mover solo el archivo principal
                    shutil.move(main_video_file, destination_path)
                    logger.info(f"✅ Archivo principal movido a: {destination_path}")
                    
                    # Opcional: mover subtítulos si existen
                    self.move_subtitles(source_path, clean_name)
                    
                    # Eliminar directorio vacío o con archivos no necesarios
                    try:
                        shutil.rmtree(source_path)
                        logger.info(f"🗑️  Directorio temporal eliminado: {source_path}")
                    except:
                        logger.warning(f"⚠️  No se pudo eliminar directorio: {source_path}")
                else:
                    logger.error(f"❌ No se encontró archivo de video en: {source_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error organizando descarga: {e}")
            return False
    
    def find_main_video_file(self, directory):
        """Encuentra el archivo de video principal en un directorio"""
        video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        largest_file = None
        largest_size = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                _, ext = os.path.splitext(file)
                
                if ext.lower() in video_extensions:
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > largest_size:
                            largest_size = file_size
                            largest_file = file_path
                    except:
                        continue
        
        return largest_file
    
    def move_subtitles(self, source_dir, clean_name):
        """Mueve archivos de subtítulos si existen"""
        subtitle_extensions = ['.srt', '.sub', '.ass', '.ssa', '.vtt']
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in subtitle_extensions:
                    source_sub = os.path.join(root, file)
                    dest_sub = os.path.join(self.organized_dir, f"{clean_name}{ext}")
                    
                    try:
                        shutil.copy2(source_sub, dest_sub)
                        logger.info(f"📝 Subtítulos copiados: {dest_sub}")
                    except Exception as e:
                        logger.warning(f"⚠️  Error copiando subtítulos: {e}")

def main():
    """Función principal"""
    # Obtener información del torrent desde variables de entorno
    torrent_name = os.getenv('TR_TORRENT_NAME', '')
    torrent_dir = os.getenv('TR_TORRENT_DIR', '/downloads/complete')
    
    if not torrent_name:
        logger.error("❌ No se recibió nombre del torrent")
        return False
    
    logger.info(f"🎬 Iniciando organización de: {torrent_name}")
    
    organizer = FileOrganizer()
    success = organizer.organize_completed_download(torrent_name, torrent_dir)
    
    if success:
        logger.info("🎉 ¡Organización completada exitosamente!")
    else:
        logger.error("❌ Error en la organización")
    
    return success

if __name__ == "__main__":
    main()
