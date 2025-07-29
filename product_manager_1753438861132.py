"""
Product management for MOON FIT Telegram Bot
"""
import logging
from typing import List, Dict, Optional, Tuple
from database import db
from config import CURRENCY

logger = logging.getLogger(__name__)

class ProductManager:
    # Product type mappings
    PRODUCT_TYPES = {
        'tshirt': '👕 T-Shirt',
        'hoodie': '👔 Hoodie', 
        'hat': '🧢 Hat'
    }
    
    @staticmethod
    def add_product(name: str, product_type: str, price: float, description: str = None,
                   image_url: str = None, stock_quantity: int = 0, admin_id: int = None) -> Tuple[bool, str, int]:
        """Add a new product"""
        try:
            # Validate input
            if not name or len(name.strip()) < 2:
                return False, "Product name must be at least 2 characters", 0
            
            if product_type not in ProductManager.PRODUCT_TYPES:
                return False, f"Invalid product type. Must be one of: {', '.join(ProductManager.PRODUCT_TYPES.keys())}", 0
            
            if price <= 0:
                return False, "Price must be greater than 0", 0
            
            if stock_quantity < 0:
                return False, "Stock quantity cannot be negative", 0
            
            # Add product to database
            product_id = db.add_product(
                name=name.strip(),
                product_type=product_type,
                price=price,
                description=description.strip() if description else None,
                image_url=image_url.strip() if image_url else None,
                stock_quantity=stock_quantity
            )
            
            # Log admin action
            if admin_id:
                db.log_admin_action(
                    admin_id, 
                    "ADD_PRODUCT", 
                    f"Added product: {name} (ID: {product_id}, Type: {product_type}, Price: {price})"
                )
            
            logger.info(f"Added new product: {name} (ID: {product_id})")
            return True, f"Product '{name}' added successfully!", product_id
            
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return False, "Failed to add product", 0
    
    @staticmethod
    def update_product(product_id: int, admin_id: int = None, **kwargs) -> Tuple[bool, str]:
        """Update product information"""
        try:
            # Get current product
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            # Validate updates
            valid_fields = ['name', 'price', 'description', 'image_url', 'stock_quantity', 'active']
            update_data = {}
            
            for key, value in kwargs.items():
                if key in valid_fields and value is not None:
                    if key == 'name' and (not value or len(value.strip()) < 2):
                        return False, "Product name must be at least 2 characters"
                    elif key == 'price' and value <= 0:
                        return False, "Price must be greater than 0"
                    elif key == 'stock_quantity' and value < 0:
                        return False, "Stock quantity cannot be negative"
                    
                    update_data[key] = value.strip() if isinstance(value, str) else value
            
            if not update_data:
                return False, "No valid fields to update"
            
            # Update product
            db.update_product(product_id, **update_data)
            
            # Log admin action
            if admin_id:
                changes = ', '.join([f"{k}: {v}" for k, v in update_data.items()])
                db.log_admin_action(
                    admin_id,
                    "UPDATE_PRODUCT",
                    f"Updated product ID {product_id}: {changes}"
                )
            
            logger.info(f"Updated product {product_id}: {update_data}")
            return True, "Product updated successfully!"
            
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False, "Failed to update product"
    
    @staticmethod
    def delete_product(product_id: int, admin_id: int = None) -> Tuple[bool, str]:
        """Soft delete a product"""
        try:
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            db.delete_product(product_id)
            
            # Log admin action
            if admin_id:
                db.log_admin_action(
                    admin_id,
                    "DELETE_PRODUCT",
                    f"Deleted product: {product['name']} (ID: {product_id})"
                )
            
            logger.info(f"Deleted product {product_id}: {product['name']}")
            return True, f"Product '{product['name']}' deleted successfully!"
            
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False, "Failed to delete product"
    
    @staticmethod
    def get_product_details(product_id: int, include_reviews: bool = False) -> Optional[Dict]:
        """Get detailed product information"""
        try:
            product = db.get_product(product_id)
            if not product:
                return None
            
            # Add formatted information
            product['type_display'] = ProductManager.PRODUCT_TYPES.get(product['type'], product['type'])
            product['price_display'] = f"{product['price']:.3f} {CURRENCY}"
            
            # Add stock status
            if product['stock_quantity'] == 0:
                product['stock_status'] = "❌ Out of Stock"
                product['stock_color'] = "🔴"
            elif product['stock_quantity'] < 10:
                product['stock_status'] = f"⚠️ Low Stock ({product['stock_quantity']} left)"
                product['stock_color'] = "🟡"
            else:
                product['stock_status'] = f"✅ In Stock ({product['stock_quantity']} available)"
                product['stock_color'] = "🟢"
            
            if include_reviews:
                from review_manager import review_manager
                product['rating_summary'] = review_manager.get_product_rating_summary(product_id)
            
            return product
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return None
    
    @staticmethod
    def get_products_by_category(category: str, active_only: bool = True) -> List[Dict]:
        """Get products by category with additional information"""
        try:
            products = db.get_products_by_type(category) if active_only else db.get_all_products()
            
            # Filter by category if getting all products
            if not active_only:
                products = [p for p in products if p['type'] == category]
            
            # Add display information
            for product in products:
                product['type_display'] = ProductManager.PRODUCT_TYPES.get(product['type'], product['type'])
                product['price_display'] = f"{product['price']:.3f} {CURRENCY}"
                
                # Add stock status
                if product['stock_quantity'] == 0:
                    product['stock_status'] = "❌ Out of Stock"
                elif product['stock_quantity'] < 10:
                    product['stock_status'] = f"⚠️ Low Stock"
                else:
                    product['stock_status'] = "✅ In Stock"
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []
    
    @staticmethod
    def get_all_products(admin_view: bool = False) -> List[Dict]:
        """Get all products with display information"""
        try:
            products = db.get_all_products(include_inactive=admin_view)
            
            for product in products:
                product['type_display'] = ProductManager.PRODUCT_TYPES.get(product['type'], product['type'])
                product['price_display'] = f"{product['price']:.3f} {CURRENCY}"
                product['status_display'] = "✅ Active" if product['active'] else "❌ Inactive"
                
                # Add stock status
                if product['stock_quantity'] == 0:
                    product['stock_status'] = "❌ Out of Stock"
                elif product['stock_quantity'] < 10:
                    product['stock_status'] = f"⚠️ Low Stock ({product['stock_quantity']})"
                else:
                    product['stock_status'] = f"✅ In Stock ({product['stock_quantity']})"
            
            return products
            
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return []
    
    @staticmethod
    def format_product_text(product: Dict, detailed: bool = True) -> str:
        """Format product information for display"""
        try:
            if not product:
                return "Product not found"
            
            text = f"**{product['name']}**\n\n"
            text += f"**Type:** {product.get('type_display', product['type'])}\n"
            text += f"**Price:** {product['price']:.3f} {CURRENCY}\n"
            
            if detailed:
                if product.get('description'):
                    text += f"**Description:** {product['description']}\n"
                
                stock_qty = product['stock_quantity']
                text += f"**Stock:** {product.get('stock_status', f'{stock_qty} available')}\n"
                
                # Add rating if available
                if product.get('rating_summary'):
                    rating = product['rating_summary']
                    if rating['total_reviews'] > 0:
                        from review_manager import ReviewManager
                        text += f"**Rating:** {ReviewManager.format_rating(rating['average_rating'])} ({rating['total_reviews']} reviews)\n"
                    else:
                        text += f"**Rating:** No reviews yet\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error formatting product text: {e}")
            return "Error displaying product information"
    
    @staticmethod
    def format_product_list(products: List[Dict], category: str = None) -> str:
        """Format product list for display"""
        try:
            if not products:
                category_text = f" in {ProductManager.PRODUCT_TYPES.get(category, category)}" if category else ""
                return f"No products found{category_text}."
            
            category_text = f" - {ProductManager.PRODUCT_TYPES.get(category, category)}" if category else ""
            text = f"🛍️ **Products{category_text}**\n\n"
            
            for product in products:
                status_emoji = "✅" if product['active'] else "❌"
                stock_emoji = "🟢" if product['stock_quantity'] > 10 else "🟡" if product['stock_quantity'] > 0 else "🔴"
                
                text += f"{status_emoji} **{product['name']}**\n"
                text += f"   Price: {product['price']:.3f} {CURRENCY}\n"
                text += f"   Stock: {stock_emoji} {product['stock_quantity']} available\n\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error formatting product list: {e}")
            return "Error displaying products"
    
    @staticmethod
    def update_stock(product_id: int, quantity_change: int, admin_id: int = None) -> Tuple[bool, str]:
        """Update product stock quantity"""
        try:
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            new_quantity = product['stock_quantity'] + quantity_change
            if new_quantity < 0:
                return False, "Stock quantity cannot be negative"
            
            db.update_stock(product_id, quantity_change)
            
            # Log admin action
            if admin_id:
                action_type = "INCREASE_STOCK" if quantity_change > 0 else "DECREASE_STOCK"
                db.log_admin_action(
                    admin_id,
                    action_type,
                    f"Product {product['name']} (ID: {product_id}): {product['stock_quantity']} → {new_quantity}"
                )
            
            logger.info(f"Updated stock for product {product_id}: {quantity_change} (new total: {new_quantity})")
            return True, f"Stock updated successfully. New quantity: {new_quantity}"
            
        except Exception as e:
            logger.error(f"Error updating stock: {e}")
            return False, "Failed to update stock"
    
    @staticmethod
    def get_low_stock_products(threshold: int = 10) -> List[Dict]:
        """Get products with low stock"""
        try:
            products = db.get_all_products(include_inactive=False)
            low_stock = [p for p in products if p['stock_quantity'] <= threshold]
            
            for product in low_stock:
                product['type_display'] = ProductManager.PRODUCT_TYPES.get(product['type'], product['type'])
                product['price_display'] = f"{product['price']:.3f} {CURRENCY}"
            
            return low_stock
            
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []
    
    @staticmethod
    def search_products(query: str, active_only: bool = True) -> List[Dict]:
        """Search products by name or description"""
        try:
            products = db.get_all_products(include_inactive=not active_only)
            query_lower = query.lower()
            
            matching_products = []
            for product in products:
                if (query_lower in product['name'].lower() or 
                    (product['description'] and query_lower in product['description'].lower())):
                    
                    product['type_display'] = ProductManager.PRODUCT_TYPES.get(product['type'], product['type'])
                    product['price_display'] = f"{product['price']:.3f} {CURRENCY}"
                    matching_products.append(product)
            
            return matching_products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    @staticmethod
    def validate_product_data(name: str, product_type: str, price: float, 
                            description: str = None, stock_quantity: int = 0) -> Tuple[bool, str]:
        """Validate product data before adding/updating"""
        if not name or len(name.strip()) < 2:
            return False, "Product name must be at least 2 characters"
        
        if product_type not in ProductManager.PRODUCT_TYPES:
            return False, f"Invalid product type. Must be one of: {', '.join(ProductManager.PRODUCT_TYPES.keys())}"
        
        if price <= 0:
            return False, "Price must be greater than 0"
        
        if price > 10000:  # Reasonable upper limit
            return False, "Price is too high"
        
        if stock_quantity < 0:
            return False, "Stock quantity cannot be negative"
        
        if description and len(description) > 1000:
            return False, "Description is too long (max 1000 characters)"
        
        return True, "Valid product data"

# Global product manager instance
product_manager = ProductManager()
