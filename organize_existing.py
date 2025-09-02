#!/usr/bin/env python3
"""
Script para organizar archivos existentes en /downloads/complete/
"""
import os
import shutil
import re

def clean_movie_name(filename):
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

def organize_existing_files():
    """Organiza todos los archivos existentes"""
    complete_dir = "/home/raulaxxo/yts-downloader/downloads/complete"
    movies_dir = "/home/raulaxxo/yts-downloader/downloads/movies"
    
    # Crear directorio de películas si no existe
    os.makedirs(movies_dir, exist_ok=True)
    
    processed = 0
    
    print("🗂️  **Organizando archivos existentes...**\n")
    
    for item in os.listdir(complete_dir):
        item_path = os.path.join(complete_dir, item)
        
        if os.path.isfile(item_path) and item.endswith('.mp4'):
            # Es un archivo de video directo
            print(f"📁 Procesando archivo: {item}")
            
            # Limpiar nombre
            clean_name = clean_movie_name(item)
            if not clean_name.endswith('.mp4'):
                clean_name += '.mp4'
            
            # Mover archivo
            dest_path = os.path.join(movies_dir, clean_name)
            try:
                shutil.move(item_path, dest_path)
                print(f"✅ Movido a: {clean_name}\n")
                processed += 1
            except Exception as e:
                print(f"❌ Error moviendo {item}: {e}\n")
                
        elif os.path.isdir(item_path):
            # Es un directorio, buscar el archivo principal
            print(f"📂 Procesando directorio: {item}")
            
            # Buscar archivo de video más grande
            video_file = None
            max_size = 0
            
            for root, dirs, files in os.walk(item_path):
                for file in files:
                    if file.endswith(('.mp4', '.mkv', '.avi')):
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        if size > max_size:
                            max_size = size
                            video_file = file_path
            
            if video_file:
                # Usar el nombre del directorio para limpiar
                clean_name = clean_movie_name(item)
                extension = os.path.splitext(video_file)[1] or '.mp4'
                if not clean_name.endswith(extension):
                    clean_name += extension
                
                # Mover archivo principal
                dest_path = os.path.join(movies_dir, clean_name)
                try:
                    shutil.move(video_file, dest_path)
                    print(f"✅ Movido a: {clean_name}")
                    
                    # Intentar eliminar directorio vacío
                    try:
                        shutil.rmtree(item_path)
                        print(f"🗑️  Directorio eliminado: {item}")
                    except:
                        print(f"⚠️  No se pudo eliminar directorio: {item}")
                    
                    print()
                    processed += 1
                except Exception as e:
                    print(f"❌ Error moviendo {video_file}: {e}\n")
            else:
                print(f"⚠️  No se encontró archivo de video en {item}\n")
    
    print(f"🎉 **Organización completada!**")
    print(f"📊 **Archivos procesados:** {processed}")
    
    return processed

if __name__ == "__main__":
    organize_existing_files()
