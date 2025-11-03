#!/usr/bin/env python3
"""
🔍 Verificador de estado del MCP Hybris E-commerce
Verifica que todos los componentes estén funcionando correctamente.
"""

import sys
import os
import subprocess
from datetime import datetime

def print_header(title):
    """Imprime un encabezado estilizado."""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def check_python_version():
    """Verifica la versión de Python."""
    print(f"🐍 Python {sys.version}")
    return sys.version_info >= (3, 8)

def check_dependencies():
    """Verifica las dependencias requeridas."""
    dependencies = {
        "flask": "Servidor web",
        "pydantic": "Modelos de datos", 
        "datetime": "Manejo de fechas",
        "typing": "Tipado estático"
    }
    
    results = {}
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            results[dep] = "✅"
            print(f"✅ {dep}: {description}")
        except ImportError:
            results[dep] = "❌"
            print(f"❌ {dep}: {description} - NO DISPONIBLE")
    
    return all(status == "✅" for status in results.values())

def check_files():
    """Verifica que los archivos principales existan."""
    required_files = {
        "server_simple.py": "Servidor principal",
        "start_server.sh": "Script de inicio",
        "README.md": "Documentación",
        "reflexion/seo_schemas.py": "Esquemas SEO",
        "reflexion/seo_nodes.py": "Nodos SEO",
        "reflexion/seo_graph.py": "Grafo SEO"
    }
    
    optional_files = {
        "verify_setup.py": "Verificador de sistema (este archivo)"
    }
    
    results = {}
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            results[file_path] = "✅"
            print(f"✅ {file_path}: {description}")
        else:
            results[file_path] = "❌"
            print(f"❌ {file_path}: {description} - NO ENCONTRADO")
    
    # Verificar archivos opcionales
    for file_path, description in optional_files.items():
        if os.path.exists(file_path):
            print(f"✅ {file_path}: {description} (opcional)")
    
    return all(status == "✅" for status in results.values())

def check_imports():
    """Verifica que las importaciones funcionen correctamente."""
    print("\n🔗 Verificando importaciones internas...")
    
    try:
        # Test importación de esquemas
        sys.path.insert(0, '.')
        from reflexion.seo_schemas import SEOReflexionState, ProductDescriptionTask
        print("✅ reflexion.seo_schemas: Importación exitosa")
        
        # Test creación de estado
        task = ProductDescriptionTask(
            product_id="TEST001",
            original_description="Test description",
            target_keywords=["test", "keyword"],
            product_category="Test",
            target_audience="Test",
            price_range="Test"
        )
        print("✅ ProductDescriptionTask: Creación exitosa")
        
        initial_state = SEOReflexionState.create_initial(task, max_attempts=3)
        print("✅ SEOReflexionState: Estado inicial creado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {str(e)}")
        return False

def check_server_syntax():
    """Verifica que el servidor tenga sintaxis correcta."""
    print("\n🌐 Verificando sintaxis del servidor...")
    
    try:
        # Verificar sintaxis compilando
        with open('server_simple.py', 'r') as f:
            content = f.read()
        
        compile(content, 'server_simple.py', 'exec')
        print("✅ server_simple.py: Sintaxis correcta")
        return True
        
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en servidor: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error verificando servidor: {str(e)}")
        return False

def main():
    """Función principal de verificación."""
    print_header("VERIFICADOR DE ESTADO MCP HYBRIS E-COMMERCE")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # Ejecutar verificaciones
    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Archivos del proyecto", check_files),
        ("Importaciones internas", check_imports),
        ("Sintaxis del servidor", check_server_syntax)
    ]
    
    results = []
    for check_name, check_func in checks:
        print_header(f"VERIFICANDO: {check_name}")
        result = check_func()
        results.append((check_name, result))
    
    # Resumen final
    print_header("RESUMEN DE VERIFICACIÓN")
    all_passed = True
    
    for check_name, passed in results:
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ El proyecto está listo para usar")
        print("\n🚀 Para iniciar el servidor ejecuta:")
        print("   ./start_server.sh")
        print("\n🌐 Para acceder a las interfaces:")
        print("   http://localhost:5001/demo      - ReAct E-commerce")
        print("   http://localhost:5001/seo-demo  - Reflexión SEO")
    else:
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print("🔧 Revisa los errores arriba antes de usar el sistema")
    
    print("="*60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)