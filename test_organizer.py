#!/usr/bin/env python3
"""
Script de prueba para verificar el organizador de archivos
"""
import os
import re
import urllib.parse

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
    
    # Remover año para no duplicarlo
    if year:
        cleaned_name = re.sub(r'\b' + year + r'\b', '', cleaned_name)
    
    # Limpiar espacios y caracteres especiales
    cleaned_name = re.sub(r'[\.\-_]+', ' ', cleaned_name)
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)
    cleaned_name = cleaned_name.strip()
    
    # Si el nombre queda muy corto o vacío, usar estrategia conservadora
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

def test_clean_movie_name():
    """Prueba la función de limpieza de nombres"""    
    test_cases = [
        "The.Matrix.1999.1080p.BluRay.x264-YTS.MX",
        "Inception[2010]DvDrip[Eng]-FXG",
        "Avatar.The.Way.of.Water.2022.2160p.WEBRip.x265-RARBG",
        "Joker (2019) [1080p] [YTS] [YIFY]",
        "Spider-Man.No.Way.Home.2021.720p.HDTV.x264",
        "The.Batman.2022.1080p.WEBRip.x264-RARBG",
        "Top.Gun.Maverick.2022.2160p.4K.BluRay.x265-YTS",
        "Dune.Part.One.2021.IMAX.1080p.BluRay.x264-YTS.MX",
        "Fast.X.2023.1080p.BluRay.x264-YIFY",
        "John.Wick.Chapter.4.2023.2160p.WEBRip.x265-PSA",
        "Scream.VI.2023.720p.HDTV.x264-KILLERS",
        "Everything.Everywhere.All.at.Once.2022.1080p.BluRay.H264-AAC-RARBG"
    ]
    
    print("🧪 **Pruebas de limpieza de nombres:**\n")
    
    for i, test_name in enumerate(test_cases, 1):
        clean_name = clean_movie_name(test_name)
        print(f"{i}. **Original:** `{test_name}`")
        print(f"   **Limpio:**  `{clean_name}.mp4`\n")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🎬 **PRUEBA DEL ORGANIZADOR DE ARCHIVOS**")
    print("=" * 60)
    
    test_clean_movie_name()
    
    print("✅ **Pruebas completadas!**")
    print("🗂️  **Los archivos se organizarán automáticamente cuando termine una descarga**")
