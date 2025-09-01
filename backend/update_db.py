#!/usr/bin/env python3
"""
Script para actualizar la base de datos con las nuevas columnas
"""
import sqlite3
import os

# Rutas a las bases de datos
db_paths = ['/app/yts.db', '/app/instance/yts.db']

def update_database():
    """Actualiza la base de datos agregando las columnas faltantes"""
    for db_path in db_paths:
        print(f"\nActualizando base de datos: {db_path}")
        conn = None
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si la tabla download existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='download'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("La tabla 'download' no existe. Creando tabla...")
                cursor.execute("""
                    CREATE TABLE download (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        movie_id VARCHAR(120) NOT NULL,
                        movie_title VARCHAR(200) NOT NULL,
                        year VARCHAR(4),
                        rating VARCHAR(10),
                        magnet TEXT NOT NULL,
                        imdb_code VARCHAR(20),
                        download_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status VARCHAR(20) DEFAULT 'pendiente',
                        user_id INTEGER NOT NULL
                    )
                """)
                print("Tabla 'download' creada exitosamente!")
            else:
                print("La tabla 'download' ya existe. Verificando columnas...")
                
                # Verificar si las columnas ya existen
                cursor.execute("PRAGMA table_info(download)")
                columns = [column[1] for column in cursor.fetchall()]
                
                print(f"Columnas actuales en la tabla download: {columns}")
                
                # Agregar columna year si no existe
                if 'year' not in columns:
                    print("Agregando columna 'year'...")
                    cursor.execute("ALTER TABLE download ADD COLUMN year VARCHAR(4)")
                    
                # Agregar columna rating si no existe  
                if 'rating' not in columns:
                    print("Agregando columna 'rating'...")
                    cursor.execute("ALTER TABLE download ADD COLUMN rating VARCHAR(10)")
                    
                # Agregar columna imdb_code si no existe
                if 'imdb_code' not in columns:
                    print("Agregando columna 'imdb_code'...")
                    cursor.execute("ALTER TABLE download ADD COLUMN imdb_code VARCHAR(20)")
            
            # Verificar si la tabla user existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            user_table_exists = cursor.fetchone()
            
            if not user_table_exists:
                print("La tabla 'user' no existe. Creando tabla...")
                cursor.execute("""
                    CREATE TABLE user (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password VARCHAR(120) NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Tabla 'user' creada exitosamente!")
            
            conn.commit()
            print(f"Base de datos {db_path} actualizada exitosamente!")
            
            # Verificar las columnas después de la actualización
            cursor.execute("PRAGMA table_info(download)")
            columns_after = [column[1] for column in cursor.fetchall()]
            print(f"Columnas después de la actualización: {columns_after}")
            
        except Exception as e:
            print(f"Error al actualizar la base de datos {db_path}: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    update_database()
