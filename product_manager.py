"""
Product management for MOON FIT Telegram Bot
"""
import logging
from typing import List, Dict, Optional, Tuple
from database import db
from config import DEFAULT_PRODUCT_IMAGE, PRODUCT_CATEGORIES

logger = logging.getLogger(__name__)

class ProductManager:
    @staticmethod
    def add_product(name: str, product_type: str, price: float, 
                   stock_quantity: int, description: str = None,
                   image_url: str = None) -> Tuple[bool, str]:
        """Add a new product to the store"""
        try:
            # Validate input
            if not name or not name.strip():
                return False, "Product name cannot be empty"
            
            if product_type not in PRODUCT_CATEGORIES:
                return False, f"Invalid product type. Must be one of: {', '.join(PRODUCT_CATEGORIES.keys())}"
            
            if price <= 0:
                return False, "Price must be greater than 0"
            
            if stock_quantity < 0:
                return False, "Stock quantity cannot be negative"
            
            # Use default image if none provided
            if not image_url:
                image_url = DEFAULT_PRODUCT_IMAGE
            
            # Add product to database
            product_id = db.add_product(
                name=name.strip(),
                product_type=product_type,
                price=price,
                stock_quantity=stock_quantity,
                description=description.strip() if description else None,
                image_url=image_url
            )
            
            if product_id:
                logger.info(f"Product added successfully: {name} (ID: {product_id})")
                return True, f"Product '{name}' added successfully!"
            else:
                return False, "Failed to add product to database"
                
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False, "An error occurred while adding the product"
    
    @staticmethod
    def get_product_details(product_id: int) -> Optional[Dict]:
        """Get detailed product information"""
        try:
            return db.get_product(product_id)
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
    
    @staticmethod
    def get_all_products() -> List[Dict]:
        """Get all products"""
        try:
            return db.get_all_products()
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []
    
    @staticmethod
    def get_products_by_type(product_type: str) -> List[Dict]:
        """Get products by type"""
        try:
            return db.get_products_by_type(product_type)
        except Exception as e:
            logger.error(f"Error getting products by type: {e}")
            return []
    
    @staticmethod
    def update_stock(product_id: int, quantity_change: int) -> Tuple[bool, str]:
        """Update product stock (add or subtract)"""
        try:
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            new_stock = product['stock_quantity'] + quantity_change
            
            if new_stock < 0:
                return False, "Insufficient stock"
            
            success = db.update_product_stock(product_id, new_stock)
            
            if success:
                logger.info(f"Stock updated for product {product_id}: {product['stock_quantity']} -> {new_stock}")
                return True, f"Stock updated to {new_stock}"
            else:
                return False, "Failed to update stock"
                
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return False, "An error occurred while updating stock"
    
    @staticmethod
    def check_stock_availability(product_id: int, required_quantity: int) -> Tuple[bool, str]:
        """Check if required quantity is available in stock"""
        try:
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            if product['stock_quantity'] >= required_quantity:
                return True, "Stock available"
            else:
                return False, f"Only {product['stock_quantity']} items available"
                
        except Exception as e:
            logger.error(f"Error checking stock availability: {e}")
            return False, "Error checking stock"
    
    @staticmethod
    def delete_product(product_id: int) -> Tuple[bool, str]:
        """Delete a product from the store"""
        try:
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            success = db.delete_product(product_id)
            
            if success:
                logger.info(f"Product deleted: {product['name']} (ID: {product_id})")
                return True, f"Product '{product['name']}' deleted successfully"
            else:
                return False, "Failed to delete product"
                
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False, "An error occurred while deleting the product"
    
    @staticmethod
    def get_low_stock_products(threshold: int = 5) -> List[Dict]:
        """Get products with low stock"""
        try:
            return db.get_low_stock_products(threshold)
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []
    
    @staticmethod
    def search_products(query: str) -> List[Dict]:
        """Search products by name"""
        try:
            all_products = db.get_all_products()
            query_lower = query.lower()
            
            matching_products = []
            for product in all_products:
                if (query_lower in product['name'].lower() or 
                    (product['description'] and query_lower in product['description'].lower())):
                    matching_products.append(product)
            
            return matching_products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def get_product_statistics() -> Dict:
        """Get product-related statistics"""
        try:
            all_products = db.get_all_products()
            low_stock = db.get_low_stock_products()
            
            # Count by category
            category_counts = {}
            total_value = 0
            
            for product in all_products:
                category = product['type']
                category_counts[category] = category_counts.get(category, 0) + 1
                total_value += product['price'] * product['stock_quantity']
            
            return {
                'total_products': len(all_products),
                'low_stock_count': len(low_stock),
                'category_counts': category_counts,
                'total_inventory_value': total_value
            }
            
        except Exception as e:
            logger.error(f"Error getting product statistics: {e}")
            return {
                'total_products': 0,
                'low_stock_count': 0,
                'category_counts': {},
                'total_inventory_value': 0.0
            }
    
    @staticmethod
    def add_sample_products():
        """Add sample products to the store for testing"""
        try:
            logger.info("Adding sample products...")
            
            sample_products = [
                {
                    'name': 'Classic Moon Tee',
                    'type': 'tshirt',
                    'price': 25.99,
                    'stock_quantity': 15,
                    'description': 'Premium cotton t-shirt with moon logo. Comfortable and stylish for everyday wear.'
                },
                {
                    'name': 'Lunar Polo Shirt',
                    'type': 'tshirt',
                    'price': 35.99,
                    'stock_quantity': 12,
                    'description': 'Elegant polo shirt with embroidered moon design. Perfect for casual and semi-formal occasions.'
                },
                {
                    'name': 'Galaxy Hoodie',
                    'type': 'hoodie',
                    'price': 49.99,
                    'stock_quantity': 8,
                    'description': 'Warm and cozy hoodie featuring a beautiful galaxy print. Ideal for cool weather.'
                },
                {
                    'name': 'Constellation Pullover',
                    'type': 'hoodie',
                    'price': 45.99,
                    'stock_quantity': 10,
                    'description': 'Stylish pullover hoodie with constellation pattern. Made from premium fleece material.'
                },
                {
                    'name': 'Moon Phase Cap',
                    'type': 'hat',
                    'price': 19.99,
                    'stock_quantity': 20,
                    'description': 'Adjustable baseball cap with moon phase embroidery. One size fits all.'
                },
                {
                    'name': 'Lunar Beanie',
                    'type': 'hat',
                    'price': 16.99,
                    'stock_quantity': 18,
                    'description': 'Soft knit beanie with moon logo. Perfect for cold weather and casual outfits.'
                },
                {
                    'name': 'Eclipse Snapback',
                    'type': 'hat',
                    'price': 22.99,
                    'stock_quantity': 14,
                    'description': 'Trendy snapback hat with eclipse design. Flat brim and adjustable fit.'
                },
                {
                    'name': 'Midnight Oversized Tee',
                    'type': 'tshirt',
                    'price': 28.99,
                    'stock_quantity': 6,
                    'description': 'Relaxed fit oversized t-shirt in midnight black. Features glow-in-the-dark moon print.'
                }
            ]
            
            added_count = 0
            for product_data in sample_products:
                success, message = ProductManager.add_product(**product_data)
                if success:
                    added_count += 1
                else:
                    logger.warning(f"Failed to add sample product {product_data['name']}: {message}")
            
            logger.info(f"Added {added_count} sample products successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding sample products: {e}")
            return False
    
    @staticmethod
    def validate_product_data(name: str, product_type: str, price: float, 
                             stock_quantity: int, description: str = None) -> Tuple[bool, str]:
        """Validate product data before adding/updating"""
        try:
            # Name validation
            if not name or not name.strip():
                return False, "Product name is required"
            
            if len(name.strip()) > 100:
                return False, "Product name is too long (max 100 characters)"
            
            # Type validation
            if product_type not in PRODUCT_CATEGORIES:
                return False, f"Invalid product type. Must be one of: {', '.join(PRODUCT_CATEGORIES.keys())}"
            
            # Price validation
            if not isinstance(price, (int, float)):
                return False, "Price must be a number"
            
            if price <= 0:
                return False, "Price must be greater than 0"
            
            if price > 10000:
                return False, "Price is too high (max $10,000)"
            
            # Stock validation
            if not isinstance(stock_quantity, int):
                return False, "Stock quantity must be a whole number"
            
            if stock_quantity < 0:
                return False, "Stock quantity cannot be negative"
            
            if stock_quantity > 10000:
                return False, "Stock quantity is too high (max 10,000)"
            
            # Description validation
            if description and len(description) > 1000:
                return False, "Description is too long (max 1000 characters)"
            
            return True, "Valid product data"
            
        except Exception as e:
            logger.error(f"Error validating product data: {e}")
            return False, "Error validating product data"
