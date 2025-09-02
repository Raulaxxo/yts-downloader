#!/usr/bin/env python3
"""
Script para configurar Plex y forzar reconocimiento de películas
"""
import requests
import time
import subprocess
import os

def setup_plex_library():
    """Configura la biblioteca de Plex"""
    print("🎭 **Configurando Plex para reconocer películas...**\n")
    
    # Información sobre Plex
    plex_url = "http://localhost:32401"
    
    print("📋 **Pasos para configurar Plex manualmente:**\n")
    
    print("1. **Acceder a Plex Web:**")
    print(f"   Abrir: {plex_url}/web")
    print("   (o http://localhost:32401/web)")
    print()
    
    print("2. **Crear biblioteca de películas:**")
    print("   - Ir a 'Configuración' > 'Bibliotecas'")
    print("   - Hacer clic en '+ Agregar biblioteca'")
    print("   - Seleccionar 'Películas'")
    print("   - Nombre: 'Películas' o 'Movies'")
    print("   - Añadir carpeta: `/movies`")
    print("   - Agente: 'Plex Movie' (recomendado)")
    print("   - Idioma de metadatos: 'Español' o 'English'")
    print()
    
    print("3. **Configuración avanzada (opcional):**")
    print("   - Activar 'Escanear automáticamente'")
    print("   - Activar 'Ejecutar analizador parcial cuando sea posible'")
    print("   - Activar 'Incluir archivos de música en contenido mixto'")
    print()
    
    print("4. **Forzar escaneo desde el contenedor:**")
    print("   Ejecutar este comando para escanear manualmente:")
    
    # Comando para escanear desde dentro del contenedor
    scan_command = """docker exec plex /usr/lib/plexmediaserver/Plex\\ Media\\ Scanner --scan --refresh --section 1"""
    print(f"   ```")
    print(f"   {scan_command}")
    print(f"   ```")
    print()
    
    # Intentar escaneo automático
    print("5. **Intentando escaneo automático...**")
    try:
        result = subprocess.run([
            "docker", "exec", "plex", 
            "/usr/lib/plexmediaserver/Plex Media Scanner",
            "--scan", "--refresh"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ Escaneo iniciado correctamente")
        else:
            print(f"   ⚠️ Escaneo con advertencias: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Error en escaneo automático: {e}")
        print("   💡 Usar el comando manual arriba")
    
    print()
    print("📊 **Información de archivos disponibles:**")
    
    movies_dir = "/home/raulaxxo/yts-downloader/downloads/movies"
    if os.path.exists(movies_dir):
        files = [f for f in os.listdir(movies_dir) if f.endswith('.mp4')]
        print(f"   📁 Total de películas: {len(files)}")
        print("   📽️ Películas disponibles:")
        for i, file in enumerate(files, 1):
            size_mb = os.path.getsize(os.path.join(movies_dir, file)) / (1024*1024)
            print(f"      {i:2d}. {file} ({size_mb:.0f} MB)")
    
    print()
    print("🎯 **Problemas comunes y soluciones:**")
    print()
    print("   **❓ Plex no encuentra películas:**")
    print("   - Verificar permisos: archivos deben ser legibles por uid:gid 1000:1000")
    print("   - Verificar rutas: `/movies` debe mapear a `./downloads/movies`")
    print("   - Verificar naming: usar formato 'Película (Año).ext'")
    print()
    print("   **❓ Metadatos incorrectos:**")
    print("   - Ir a la película > 'Más opciones' > 'Arreglar coincidencia'")
    print("   - Asegurar que el año esté en el nombre del archivo")
    print("   - Usar 'Actualizar metadatos' si es necesario")
    print()
    print("   **❓ Plex no actualiza automáticamente:**")
    print("   - Activar 'Escanear automáticamente' en configuración de biblioteca")
    print("   - Verificar que los webhooks estén funcionando")
    print("   - Usar escaneo manual desde interfaz web")
    
    return True

def check_plex_access():
    """Verifica acceso a Plex"""
    try:
        response = requests.get("http://localhost:32401/", timeout=5)
        if response.status_code in [200, 401]:  # 401 es normal sin auth
            print("✅ Plex está corriendo y accesible")
            return True
        else:
            print(f"❌ Plex responde con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar a Plex: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🎭 **CONFIGURACIÓN DE PLEX PARA PELÍCULAS**")
    print("=" * 60)
    print()
    
    if check_plex_access():
        setup_plex_library()
    else:
        print("⚠️ Verifica que Plex esté ejecutándose:")
        print("   docker-compose logs plex")
    
    print()
    print("🎬 **¡Configuración lista!**")
    print("   Accede a Plex Web y sigue los pasos arriba para completar la configuración.")
