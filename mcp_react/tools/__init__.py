"""
Herramientas de e-commerce para simular sistema Hybris.
Reemplaza las herramientas de Wikipedia del notebook por herramientas de productos.
"""

from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
import random
from ..schemas import ProductModel, SearchResultModel, StockInfo, PriceHistory

# === DATOS SIMULADOS DE PRODUCTOS ===

SAMPLE_PRODUCTS = [
    {
        "id": "LAPTOP001",
        "name": "Laptop HP Pavilion 15",
        "description": "Laptop HP Pavilion 15 con procesador Intel Core i5, 8GB RAM, 256GB SSD",
        "price": 15999.99,
        "currency": "MXN",
        "category": "Electrónicos",
        "brand": "HP",
        "stock": 25,
        "rating": 4.5,
        "specifications": {
            "processor": "Intel Core i5-11400H",
            "ram": "8GB DDR4",
            "storage": "256GB SSD",
            "screen": "15.6 pulgadas Full HD"
        }
    },
    {
        "id": "LAPTOP002", 
        "name": "MacBook Air M2",
        "description": "MacBook Air con chip M2, 8GB RAM unificada, 256GB SSD",
        "price": 28999.99,
        "currency": "MXN",
        "category": "Electrónicos",
        "brand": "Apple",
        "stock": 12,
        "rating": 4.8,
        "specifications": {
            "processor": "Apple M2",
            "ram": "8GB unificada",
            "storage": "256GB SSD",
            "screen": "13.6 pulgadas Liquid Retina"
        }
    },
    {
        "id": "PHONE001",
        "name": "iPhone 15 Pro",
        "description": "iPhone 15 Pro con chip A17 Pro, cámara triple, 128GB",
        "price": 26999.99,
        "currency": "MXN",
        "category": "Electrónicos",
        "brand": "Apple",
        "stock": 8,
        "rating": 4.9,
        "specifications": {
            "processor": "A17 Pro",
            "storage": "128GB",
            "camera": "Triple cámara 48MP",
            "screen": "6.1 pulgadas Super Retina XDR"
        }
    },
    {
        "id": "MOUSE001",
        "name": "Mouse Logitech MX Master 3",
        "description": "Mouse inalámbrico Logitech MX Master 3 para productividad",
        "price": 2299.99,
        "currency": "MXN",
        "category": "Accesorios",
        "brand": "Logitech",
        "stock": 45,
        "rating": 4.7,
        "specifications": {
            "connectivity": "Bluetooth + USB-C",
            "battery": "70 días",
            "dpi": "4000 DPI",
            "buttons": "7 botones"
        }
    },
    {
        "id": "TABLET001",
        "name": "iPad Air",
        "description": "iPad Air con chip M1, pantalla de 10.9 pulgadas, 64GB WiFi",
        "price": 14999.99,
        "currency": "MXN",
        "category": "Electrónicos",
        "brand": "Apple",
        "stock": 18,
        "rating": 4.6,
        "specifications": {
            "processor": "Apple M1",
            "storage": "64GB",
            "screen": "10.9 pulgadas Liquid Retina",
            "connectivity": "WiFi 6"
        }
    }
]

# === HERRAMIENTAS DE E-COMMERCE ===

def search_products(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Busca productos en el catálogo simulado de Hybris.
    Equivalente a search_wikipedia_simple del notebook.
    """
    try:
        query_lower = query.lower()
        matching_products = []
        
        for product_data in SAMPLE_PRODUCTS:
            product = ProductModel(**product_data)
            
            # Buscar en nombre, descripción, categoría y marca
            searchable_text = f"{product.name} {product.description} {product.category} {product.brand}".lower()
            
            if query_lower in searchable_text:
                matching_products.append(product)
        
        # Limitar resultados
        matching_products = matching_products[:limit]
        
        result = SearchResultModel(
            products=matching_products,
            total_results=len(matching_products),
            query=query,
            per_page=limit
        )
        
        return {
            "success": True,
            "content": f"Encontrados {len(matching_products)} productos para '{query}': " + 
                      ", ".join([f"{p.name} (${p.price})" for p in matching_products]),
            "data": result.model_dump(),
            "products_found": [p.model_dump() for p in matching_products]
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": f"Error en búsqueda de productos: {str(e)}",
            "data": None
        }

def get_product_details(product_id: str) -> Dict[str, Any]:
    """
    Obtiene detalles específicos de un producto.
    Equivalente a lookup_in_page del notebook pero para productos.
    """
    try:
        # Buscar producto por ID
        for product_data in SAMPLE_PRODUCTS:
            if product_data["id"] == product_id:
                product = ProductModel(**product_data)
                
                details = f"Producto: {product.name}\n"
                details += f"Precio: ${product.price} {product.currency}\n"
                details += f"Marca: {product.brand}\n"
                details += f"Categoría: {product.category}\n"
                details += f"Stock disponible: {product.stock} unidades\n"
                details += f"Rating: {product.rating}/5 estrellas\n"
                details += f"Descripción: {product.description}\n"
                
                if product.specifications:
                    details += "Especificaciones:\n"
                    for key, value in product.specifications.items():
                        details += f"- {key}: {value}\n"
                
                return {
                    "success": True,
                    "content": details,
                    "data": product.model_dump()
                }
        
        return {
            "success": False,
            "content": f"Producto con ID '{product_id}' no encontrado",
            "data": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": f"Error obteniendo detalles del producto: {str(e)}",
            "data": None
        }

def check_stock(product_id: str) -> Dict[str, Any]:
    """
    Verifica disponibilidad de stock de un producto.
    """
    try:
        for product_data in SAMPLE_PRODUCTS:
            if product_data["id"] == product_id:
                stock_info = StockInfo(
                    product_id=product_id,
                    available=product_data["stock"] > 0,
                    quantity=product_data["stock"],
                    warehouse="main"
                )
                
                status = "Disponible" if stock_info.available else "Agotado"
                content = f"Stock del producto {product_id}: {status} ({stock_info.quantity} unidades)"
                
                return {
                    "success": True,
                    "content": content,
                    "data": stock_info.model_dump()
                }
        
        return {
            "success": False,
            "content": f"Producto {product_id} no encontrado para verificar stock",
            "data": None
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": f"Error verificando stock: {str(e)}",
            "data": None
        }

def get_price_history(product_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Obtiene historial de precios de un producto.
    """
    try:
        # Buscar producto
        product_price = None
        for product_data in SAMPLE_PRODUCTS:
            if product_data["id"] == product_id:
                product_price = product_data["price"]
                break
        
        if product_price is None:
            return {
                "success": False,
                "content": f"Producto {product_id} no encontrado",
                "data": None
            }
        
        # Generar historial simulado
        prices = []
        current_date = datetime.now()
        base_price = product_price
        
        for i in range(days):
            date = current_date - timedelta(days=i)
            # Simular variación de precios ±10%
            variation = random.uniform(-0.1, 0.1)
            price = base_price * (1 + variation)
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 2)
            })
        
        prices.reverse()  # Ordenar cronológicamente
        
        price_history = PriceHistory(
            product_id=product_id,
            prices=prices,
            current_price=product_price,
            lowest_price=min(p["price"] for p in prices),
            highest_price=max(p["price"] for p in prices)
        )
        
        content = f"Historial de precios para {product_id}:\n"
        content += f"Precio actual: ${price_history.current_price}\n"
        content += f"Precio más bajo (últimos {days} días): ${price_history.lowest_price}\n"
        content += f"Precio más alto (últimos {days} días): ${price_history.highest_price}\n"
        
        return {
            "success": True,
            "content": content,
            "data": price_history.model_dump()
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": f"Error obteniendo historial de precios: {str(e)}",
            "data": None
        }

def get_category_products(category: str, limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene productos de una categoría específica.
    """
    try:
        category_lower = category.lower()
        matching_products = []
        
        for product_data in SAMPLE_PRODUCTS:
            if category_lower in product_data["category"].lower():
                product = ProductModel(**product_data)
                matching_products.append(product)
        
        matching_products = matching_products[:limit]
        
        content = f"Productos en categoría '{category}' ({len(matching_products)} encontrados):\n"
        for product in matching_products:
            content += f"- {product.name}: ${product.price} (Stock: {product.stock})\n"
        
        return {
            "success": True,
            "content": content,
            "data": [p.model_dump() for p in matching_products]
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": f"Error obteniendo productos de categoría: {str(e)}",
            "data": None
        }