"""
Script para ejecutar todos los tests de la aplicación
"""
import os
import sys
import subprocess

def run_tests():
    """Ejecuta todos los tests con pytest"""
    
    # Cambiar al directorio backend
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    print("🧪 Ejecutando tests de YTS Downloader...")
    print("=" * 50)
    
    # Configurar variables de entorno para tests
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    try:
        # Ejecutar tests con pytest
        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-v',  # Verbose
            '--tb=short',  # Traceback corto
            '--color=yes',  # Colores
            '--durations=10',  # Mostrar 10 tests más lentos
            '--cov=app',  # Coverage del código
            '--cov-report=term-missing',  # Mostrar líneas faltantes
            '--cov-report=html:htmlcov',  # Report HTML
        ]
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ Todos los tests pasaron!")
            print("📊 Report de coverage generado en htmlcov/")
        else:
            print("\n❌ Algunos tests fallaron")
            return False
            
    except FileNotFoundError:
        print("❌ pytest no encontrado. Instalando...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 
                          'pytest', 'pytest-cov', 'pytest-flask'], 
                         check=True)
            print("✅ pytest instalado. Ejecutando tests...")
            return run_tests()  # Reintentar
        except subprocess.CalledProcessError:
            print("❌ Error instalando pytest")
            return False
    
    return result.returncode == 0

def run_specific_test(test_file=None, test_function=None):
    """Ejecuta un test específico"""
    
    cmd = [sys.executable, '-m', 'pytest', '-v']
    
    if test_file:
        if test_function:
            cmd.append(f"tests/{test_file}::{test_function}")
        else:
            cmd.append(f"tests/{test_file}")
    
    subprocess.run(cmd)

def show_coverage():
    """Abre el report de coverage en el navegador"""
    import webbrowser
    coverage_file = os.path.join(os.path.dirname(__file__), 'htmlcov', 'index.html')
    if os.path.exists(coverage_file):
        webbrowser.open(f'file://{coverage_file}')
        print("🌐 Report de coverage abierto en el navegador")
    else:
        print("❌ Report de coverage no encontrado. Ejecuta los tests primero.")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecutar tests de YTS Downloader')
    parser.add_argument('--file', '-f', help='Ejecutar tests de un archivo específico')
    parser.add_argument('--test', '-t', help='Ejecutar una función de test específica')
    parser.add_argument('--coverage', '-c', action='store_true', 
                       help='Abrir report de coverage')
    
    args = parser.parse_args()
    
    if args.coverage:
        show_coverage()
    elif args.file or args.test:
        run_specific_test(args.file, args.test)
    else:
        success = run_tests()
        sys.exit(0 if success else 1)
