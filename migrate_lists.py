#!/usr/bin/env python3
"""
Script para migrar la base de datos y agregar las tablas de listas de películas
"""
import sqlite3
import os

def migrate_database():
    """Migra la base de datos para agregar soporte a listas de películas"""
    
    # Ruta de la base de datos dentro del contenedor
    db_path = "/app/yts.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Iniciando migración de base de datos...")
        
        # Crear tabla movie_list
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                share_code VARCHAR(32) UNIQUE NOT NULL,
                is_public BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                creator_id INTEGER NOT NULL,
                FOREIGN KEY (creator_id) REFERENCES user (id)
            )
        """)
        
        print("✅ Tabla movie_list creada")
        
        # Crear tabla movie_list_item
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movie_list_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movie_title VARCHAR(200) NOT NULL,
                year VARCHAR(4),
                rating VARCHAR(10),
                imdb_code VARCHAR(20),
                poster_url VARCHAR(500),
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                watched BOOLEAN DEFAULT 0,
                list_id INTEGER NOT NULL,
                FOREIGN KEY (list_id) REFERENCES movie_list (id) ON DELETE CASCADE
            )
        """)
        
        print("✅ Tabla movie_list_item creada")
        
        # Crear índices para mejorar el rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_list_creator ON movie_list(creator_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_list_share_code ON movie_list(share_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_list_item_list ON movie_list_item(list_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_list_item_imdb ON movie_list_item(imdb_code)")
        
        print("✅ Índices creados")
        
        # Verificar que las tablas se crearon correctamente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'movie_list%'")
        tables = cursor.fetchall()
        
        print(f"📋 Tablas encontradas: {[table[0] for table in tables]}")
        
        conn.commit()
        conn.close()
        
        print("🎉 Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = migrate_database()
    exit(0 if success else 1)
