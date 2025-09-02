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
        """Limpia el nombre del archivo: Nombre (Año) [Calidad]"""
        # Remover extensión
        name_without_ext = os.path.splitext(filename)[0]
        original_name = name_without_ext
        
        # Extraer año y calidad ANTES de limpiar
        year_match = re.search(r'\b(19|20)\d{2}\b', original_name)
        year = year_match.group() if year_match else ""
        
        quality_match = re.search(r'\b(720p|1080p|2160p|4K)\b', original_name, re.IGNORECASE)
        quality = quality_match.group() if quality_match else ""
        
        # Estrategia más inteligente: dividir por patrones conocidos
        cleaned_name = original_name
        
        # Encontrar donde termina el título real (antes de calidad, codec, etc.)
        cutoff_patterns = [
            r'\b(720p|1080p|2160p|4K)\b',
            r'\b(BluRay|WEBRip|HDTV|DVDRip|BRRip)\b',
            r'\b(x264|x265|H264)\b',
            r'\b(YTS|RARBG|YIFY)\b',
            r'-[A-Z]{2,}$',  # Release groups al final
        ]
        
        # Encontrar el primer patrón que aparece
        cut_position = len(cleaned_name)
        for pattern in cutoff_patterns:
            match = re.search(pattern, cleaned_name, re.IGNORECASE)
            if match:
                cut_position = min(cut_position, match.start())
        
    def clean_movie_name(self, filename):
        """Limpia el nombre del archivo: Nombre (Año) [Calidad]"""
        # Remover extensión
        name_without_ext = os.path.splitext(filename)[0]
        original_name = name_without_ext
        
        # Extraer año y calidad ANTES de limpiar
        year_match = re.search(r'\b(19|20)\d{2}\b', original_name)
        year = year_match.group() if year_match else ""
        
        quality_match = re.search(r'\b(720p|1080p|2160p|4K)\b', original_name, re.IGNORECASE)
        quality = quality_match.group() if quality_match else ""
        
        # Estrategia más inteligente: dividir por patrones conocidos
        cleaned_name = original_name
        
        # Encontrar donde termina el título real (antes de calidad, codec, etc.)
        cutoff_patterns = [
            r'\[(720p|1080p|2160p|4K)\]',  # Calidad entre corchetes
            r'\.(720p|1080p|2160p|4K)\.',   # Calidad con puntos
            r'\b(BluRay|WEBRip|HDTV|DVDRip|BRRip)\b',
            r'\b(x264|x265|H264)\b',
            r'\[?(YTS|RARBG|YIFY)\]?',      # Release groups específicos
            r'-(RARBG|YTS|YIFY|KILLERS|PSA|FXG)$',  # Release groups específicos al final
        ]
        
        # Encontrar el primer patrón que aparece
        cut_position = len(cleaned_name)
        for pattern in cutoff_patterns:
            match = re.search(pattern, cleaned_name, re.IGNORECASE)
            if match:
                cut_position = min(cut_position, match.start())
        
        # Cortar el nombre en esa posición, pero limpiar espacios al final
        cleaned_name = cleaned_name[:cut_position].strip()
        
        # Limpiar patrones restantes
        cleaned_name = re.sub(r'\[.*?\]', '', cleaned_name)  # Remover corchetes
        
        # Remover paréntesis con año específicamente
        if year:
            cleaned_name = re.sub(r'\(' + year + r'\)', '', cleaned_name)
        
        # Remover paréntesis restantes
        cleaned_name = re.sub(r'\(.*?\)', '', cleaned_name)
        
        # Limpiar espacios y caracteres especiales
        cleaned_name = re.sub(r'[\.\-_]+', ' ', cleaned_name)
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
        cleaned_name = cleaned_name.strip()
        
        # Si el nombre queda muy corto, usar estrategia conservadora
        if len(cleaned_name) < 3:
            # Usar las primeras palabras del nombre original
            words = original_name.replace('.', ' ').replace('-', ' ').replace('_', ' ').split()
            # Filtrar palabras que no sean parte del título
            title_words = []
            for word in words:
                if not re.match(r'\b(19|20)\d{2}\b', word) and \
                   not re.match(r'\b(720p|1080p|2160p|4K)\b', word, re.IGNORECASE) and \
                   not re.match(r'\b(BluRay|WEBRip|HDTV)\b', word, re.IGNORECASE):
                    title_words.append(word)
                if len(title_words) >= 5:  # Máximo 5 palabras
                    break
            cleaned_name = ' '.join(title_words)
        
        # Capitalizar correctamente
        final_name = cleaned_name.title()
        
        # Agregar año y calidad
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
