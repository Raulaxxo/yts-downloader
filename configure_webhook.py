#!/usr/bin/env python3
"""
Script para configurar automáticamente el webhook en Transmission
"""
import requests
import time
import json

def configure_transmission_webhook():
    """Configura el webhook en Transmission usando su API"""
    
    # Configuración
    transmission_url = "http://localhost:19091/transmission/rpc"
    username = "admin"
    password = "1234"
    
    print("🔧 Configurando webhook en Transmission...")
    
    # Esperar a que Transmission esté disponible
    for attempt in range(30):
        try:
            session = requests.Session()
            session.auth = (username, password)
            
            # Obtener token de sesión
            resp = session.post(transmission_url)
            if resp.status_code == 409:
                token = resp.headers.get('X-Transmission-Session-Id')
                session.headers.update({'X-Transmission-Session-Id': token})
                break
            else:
                print(f"Intento {attempt + 1}/30: Esperando a Transmission...")
                time.sleep(2)
        except Exception as e:
            print(f"Intento {attempt + 1}/30: Esperando a Transmission... ({e})")
            time.sleep(2)
    else:
        print("❌ No se pudo conectar con Transmission")
        return False
    
    try:
        # Configurar el script de torrent completado
        payload = {
            "method": "session-set",
            "arguments": {
                "script-torrent-done-enabled": True,
                "script-torrent-done-filename": "/usr/local/bin/transmission-webhook"
            }
        }
        
        resp = session.post(transmission_url, json=payload)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('result') == 'success':
                print("✅ Webhook configurado correctamente en Transmission")
                return True
            else:
                print(f"❌ Error en respuesta: {result}")
                return False
        else:
            print(f"❌ Error HTTP: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando webhook: {e}")
        return False

if __name__ == "__main__":
    configure_transmission_webhook()
