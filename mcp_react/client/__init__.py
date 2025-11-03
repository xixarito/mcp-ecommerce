"""
Cliente simple para interactuar con el MCP Hybris.
"""

import requests
import json
from typing import Dict, Any

class HybrisEcommerceMCPClient:
    """Cliente para interactuar con el MCP de e-commerce Hybris."""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
    
    def query_products(self, question: str) -> Dict[str, Any]:
        """
        Envía una consulta al servidor MCP.
        """
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con el servidor.
        """
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False

class InteractiveMCPClient:
    """Cliente interactivo de línea de comandos."""
    
    def __init__(self):
        self.client = HybrisEcommerceMCPClient()
    
    def run(self):
        """
        Ejecuta el cliente interactivo.
        """
        print("🛒 Cliente MCP Hybris E-commerce")
        print("=" * 50)
        
        # Verificar conexión
        if not self.client.test_connection():
            print("❌ No se puede conectar al servidor. ¿Está ejecutándose en localhost:5001?")
            return
        
        print("✅ Conectado al servidor MCP")
        print("\nEjemplos de consultas:")
        print("- ¿Qué laptops están disponibles?")
        print("- ¿Cuál es el precio del iPhone 15 Pro?")
        print("- ¿Hay stock del MacBook Air M2?")
        print("- Muéstrame productos de electrónicos")
        print("\nEscribe 'quit' para salir\n")
        
        while True:
            try:
                question = input("💬 Tu consulta: ").strip()
                
                if question.lower() in ['quit', 'salir', 'exit']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if not question:
                    continue
                
                print("🔄 Procesando...")
                result = self.client.query_products(question)
                
                if result.get("success"):
                    data = result["data"]
                    print(f"\n✅ Respuesta: {data.get('final_answer', 'Sin respuesta')}")
                    print(f"📊 Pasos realizados: {data.get('steps', 0)}")
                else:
                    print(f"❌ Error: {result.get('error', 'Error desconocido')}")
                
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    client = InteractiveMCPClient()
    client.run()