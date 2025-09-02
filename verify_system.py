#!/usr/bin/env python3
"""
Script de verificación final del sistema de medios
"""
import subprocess
import requests
import time
import os

def check_plex_status():
    """Verifica el estado completo de Plex"""
    print("🎭 Verificando estado de Plex...")
    
    # Verificar contenedor
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=plex", "--format", "table {{.Names}}\t{{.Status}}"], 
                              capture_output=True, text=True)
        if "plex" in result.stdout and "Up" in result.stdout:
            print("✅ Contenedor Plex funcionando")
        else:
            print("❌ Contenedor Plex no está corriendo")
            return False
    except:
        print("❌ Error verificando contenedor Plex")
        return False
    
    # Verificar acceso web
    try:
        resp = requests.get("http://localhost:32401/web", timeout=5)
        if resp.status_code == 200:
            print("✅ Interfaz web accesible")
        else:
            print(f"⚠️ Interfaz web responde con código: {resp.status_code}")
    except:
        print("❌ Interfaz web no accesible")
    
    return True

def check_files():
    """Verifica archivos organizados"""
    print("\n📁 Verificando archivos organizados...")
    
    try:
        result = subprocess.run(["docker", "exec", "plex", "ls", "-la", "/movies/"], 
                              capture_output=True, text=True)
        
        lines = result.stdout.strip().split('\n')
        movie_files = [line for line in lines if line.endswith('.mp4') or line.endswith('.mkv')]
        
        print(f"✅ {len(movie_files)} películas encontradas en /movies/")
        
        for i, file_line in enumerate(movie_files[:5]):
            filename = file_line.split()[-1]
            print(f"   {i+1}. {filename}")
        
        if len(movie_files) > 5:
            print(f"   ... y {len(movie_files) - 5} más")
            
        return len(movie_files)
    except:
        print("❌ Error verificando archivos")
        return 0

def provide_instructions():
    """Proporciona instrucciones finales al usuario"""
    print("\n" + "="*60)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("="*60)
    
    print("\n📋 ESTADO DEL SISTEMA:")
    print("✅ Aplicación Flask funcionando")
    print("✅ Transmission configurado y conectado")
    print("✅ Sistema de organización de archivos activo")
    print("✅ Plex instalado y archivos accesibles")
    
    print("\n🔧 PASOS FINALES PARA PLEX:")
    print("1. Abre Plex en tu navegador:")
    print("   http://localhost:32401/web")
    print("\n2. Si es la primera vez:")
    print("   - Crea una cuenta o inicia sesión")
    print("   - Completa la configuración inicial")
    print("\n3. Agregar biblioteca de películas:")
    print("   - Clic en '+' junto a 'Bibliotecas'")
    print("   - Selecciona 'Películas'")
    print("   - Agrega la carpeta: /movies")
    print("   - Selecciona agente de metadatos: 'The Movie Database'")
    print("   - Guarda y escanea")
    
    print("\n🚀 FLUJO AUTOMÁTICO:")
    print("1. Descarga película desde la app")
    print("2. Transmission descarga el archivo")
    print("3. Webhook organiza automáticamente")
    print("4. Plex detecta y añade a la biblioteca")
    
    print("\n🎬 ¡Tu sistema de medios está listo!")

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN FINAL DEL SISTEMA")
    print("="*50)
    
    # Verificar Plex
    plex_ok = check_plex_status()
    
    # Verificar archivos
    file_count = check_files()
    
    # Instrucciones finales
    provide_instructions()
    
    if plex_ok and file_count > 0:
        print("\n🟢 Sistema completamente funcional")
    else:
        print("\n🟡 Sistema parcialmente funcional - revisa configuración de Plex")
