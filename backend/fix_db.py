#!/usr/bin/env python3
"""
Script para arreglar completamente la base de datos
"""
import sqlite3
import os

def fix_database():
    """Arregla la base de datos principal"""
    db_path = '/app/instance/yts.db'
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar columnas actuales
        cursor.execute("PRAGMA table_info(download)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Columnas actuales: {columns}")
        
        # Agregar columnas faltantes
        missing_columns = {
            'magnet': 'TEXT',
            'status': 'VARCHAR(20) DEFAULT "pendiente"'
        }
        
        for col_name, col_type in missing_columns.items():
            if col_name not in columns:
                print(f"Agregando columna {col_name}...")
                cursor.execute(f"ALTER TABLE download ADD COLUMN {col_name} {col_type}")
        
        conn.commit()
        
        # Verificar las columnas finales
        cursor.execute("PRAGMA table_info(download)")
        columns_final = [column[1] for column in cursor.fetchall()]
        print(f"Columnas finales: {columns_final}")
        print("Base de datos arreglada exitosamente!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_database()
