#!/usr/bin/env python3
"""
Script de monitoreo automático simplificado
Solo verifica el estado sin hacer login
"""
import time
import logging
import sys

# Configuración
CHECK_INTERVAL = 300  # 5 minutos en segundos

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    """Monitor simplificado"""
    logger = logging.getLogger(__name__)
    logger.info("Monitor automático iniciado (modo simplificado)")
    logger.info("Por ahora solo mantiene el proceso vivo")
    
    try:
        while True:
            logger.info("Monitor activo - esperando...")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Monitor detenido")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
