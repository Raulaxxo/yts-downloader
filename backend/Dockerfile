FROM python:3.11-slim

WORKDIR /app

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip

# Instalar supervisor para manejar múltiples procesos
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Copiar configuración de supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Puerto
EXPOSE 5000

# Comando para ejecutar supervisor
CMD ["/usr/bin/supervisord"]
