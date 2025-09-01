#!/bin/bash

# Crear directorio para la interfaz web
mkdir -p transmission_config/web

# Descargar la última versión de transmission-web-control
echo "Descargando transmission-web-control..."
wget https://github.com/ronggang/transmission-web-control/archive/refs/heads/master.zip -O twc.zip

# Descomprimir
echo "Descomprimiendo..."
unzip -o twc.zip

# Mover los archivos necesarios
echo "Instalando..."
cp -r transmission-web-control-master/src/* transmission_config/web/

# Limpiar archivos temporales
echo "Limpiando..."
rm -rf transmission-web-control-master twc.zip

echo "Instalación completada!"
