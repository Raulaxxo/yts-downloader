FROM python:3.11-slim

WORKDIR /app

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Puerto
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["flask", "run", "--host=0.0.0.0"]
