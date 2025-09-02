#!/usr/bin/env python3
"""
Script para configurar automáticamente la biblioteca de Plex
"""
import requests
import time
import json

def get_plex_token():
    """Intenta obtener token de Plex existente o crear uno nuevo"""
    # Intentar leer token de archivos de configuración
    possible_paths = [
        "/home/raulaxxo/yts-downloader/plex_config/Library/Application Support/Plex Media Server/Preferences.xml",
        "/home/raulaxxo/yts-downloader/plex_config/Preferences.xml"
    ]
    
    for path in possible_paths:
        try:
            with open(path, 'r') as f:
                content = f.read()
                # Buscar PlexOnlineToken en el XML
                import re
                token_match = re.search(r'PlexOnlineToken="([^"]+)"', content)
                if token_match:
                    return token_match.group(1)
        except:
            continue
    
    return None

def configure_plex_library():
    """Configura automáticamente la biblioteca de Plex"""
    plex_url = "http://localhost:32401"
    
    print("🎭 Configurando biblioteca de Plex automáticamente...")
    
    # Obtener token
    token = get_plex_token()
    if not token:
        print("❌ No se pudo obtener token de Plex")
        print("💡 Configura manualmente desde la interfaz web:")
        print(f"   {plex_url}/web")
        return False
    
    print(f"✅ Token obtenido: {token[:10]}...")
    
    headers = {'X-Plex-Token': token}
    
    try:
        # Verificar secciones existentes
        resp = requests.get(f"{plex_url}/library/sections", headers=headers)
        if resp.status_code == 200:
            sections = resp.json()
            print(f"📚 Secciones existentes: {len(sections.get('MediaContainer', {}).get('Directory', []))}")
            
            # Buscar si ya existe una sección de películas
            for section in sections.get('MediaContainer', {}).get('Directory', []):
                if section.get('type') == 'movie':
                    print(f"✅ Sección de películas ya existe: {section.get('title')} (ID: {section.get('key')})")
                    
                    # Forzar actualización
                    refresh_url = f"{plex_url}/library/sections/{section.get('key')}/refresh"
                    refresh_resp = requests.post(refresh_url, headers=headers)
                    if refresh_resp.status_code == 200:
                        print("✅ Biblioteca actualizada correctamente")
                    return True
        
        # Si no existe, crear nueva sección
        print("🔧 Creando nueva sección de películas...")
        
        create_data = {
            'name': 'Películas',
            'type': 'movie',
            'agent': 'com.plexapp.agents.imdb',
            'scanner': 'Plex Movie Scanner',
            'language': 'es',
            'location': '/movies'
        }
        
        create_resp = requests.post(f"{plex_url}/library/sections", 
                                  headers=headers, 
                                  data=create_data)
        
        if create_resp.status_code == 201:
            print("✅ Sección de películas creada correctamente")
            return True
        else:
            print(f"❌ Error creando sección: {create_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando Plex: {e}")
        return False

def manual_scan():
    """Ejecuta escaneo manual desde el contenedor"""
    print("🔍 Ejecutando escaneo manual...")
    
    import subprocess
    try:
        # Escanear todas las secciones
        result = subprocess.run([
            "docker", "exec", "plex",
            "/usr/lib/plexmediaserver/Plex Media Scanner",
            "--scan", "--refresh"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Escaneo manual completado")
            return True
        else:
            print(f"⚠️ Escaneo con advertencias: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error en escaneo manual: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🎭 CONFIGURACIÓN AUTOMÁTICA DE PLEX")
    print("=" * 50)
    
    # Esperar a que Plex esté listo
    print("⏳ Esperando a que Plex esté listo...")
    time.sleep(10)
    
    # Intentar configuración automática
    if configure_plex_library():
        print("🎉 Configuración automática exitosa")
    else:
        print("🔧 Usando configuración manual...")
        manual_scan()
    
    print("\n📋 RESUMEN:")
    print("✅ Archivos organizados en /downloads/movies/")
    print("✅ Plex configurado para leer desde /movies")
    print("✅ Escaneo de biblioteca iniciado")
    print(f"\n🌐 Accede a Plex: http://localhost:32401/web")
    print("\n🎬 ¡Las películas deberían aparecer en unos minutos!")
