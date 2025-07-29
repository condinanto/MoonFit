"""
Shopping cart management for MOON FIT Telegram Bot
"""
import logging
from typing import List, Dict, Optional, Tuple
from database import db
from product_manager import ProductManager
from config import MAX_CART_ITEMS
from utils import format_currency

logger = logging.getLogger(__name__)

class CartManager:
    @staticmethod
    def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str]:
        """Add product to user's cart"""
        try:
            # Check if product exists and has stock
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            if product['stock_quantity'] < quantity:
                return False, f"Only {product['stock_quantity']} items available"
            
            # Get current cart
            cart = db.get_cart(user_id)
            
            # Check cart size limit
            if len(cart) >= MAX_CART_ITEMS:
                return False, f"Cart is full (max {MAX_CART_ITEMS} different items)"
            
            product_key = str(product_id)
            
            # Add or update quantity
            if product_key in cart:
                new_quantity = cart[product_key]['quantity'] + quantity
                if new_quantity > product['stock_quantity']:
                    return False, f"Cannot add {quantity} more. Only {product['stock_quantity']} total available"
                cart[product_key]['quantity'] = new_quantity
            else:
                cart[product_key] = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'added_at': "2024-01-01T00:00:00"  # Simple timestamp
                }
            
            # Update cart in database
            success = db.update_cart(user_id, cart)
            
            if success:
                logger.info(f"Added to cart: User {user_id}, Product {product_id}, Quantity {quantity}")
                return True, f"Added {quantity} x {product['name']} to cart"
            else:
                return False, "Failed to update cart"
                
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False, "An error occurred while adding to cart"
    
    @staticmethod
    def remove_from_cart(user_id: int, product_id: int, quantity: int = None) -> Tuple[bool, str]:
        """Remove product from cart (or reduce quantity)"""
        try:
            cart = db.get_cart(user_id)
            product_key = str(product_id)
            
            if product_key not in cart:
                return False, "Product not in cart"
            
            product = db.get_product(product_id)
            product_name = product['name'] if product else "Unknown Product"
            
            if quantity is None or quantity >= cart[product_key]['quantity']:
                # Remove completely
                removed_quantity = cart[product_key]['quantity']
                del cart[product_key]
                message = f"Removed {product_name} from cart"
            else:
                # Reduce quantity
                cart[product_key]['quantity'] -= quantity
                removed_quantity = quantity
                message = f"Reduced {product_name} quantity by {quantity}"
            
            # Update cart in database
            success = db.update_cart(user_id, cart)
            
            if success:
                logger.info(f"Removed from cart: User {user_id}, Product {product_id}, Quantity {removed_quantity}")
                return True, message
            else:
                return False, "Failed to update cart"
                
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            return False, "An error occurred while removing from cart"
    
    @staticmethod
    def get_cart_items(user_id: int) -> List[Dict]:
        """Get cart items with product details"""
        try:
            cart = db.get_cart(user_id)
            items = []
            
            for product_key, cart_item in cart.items():
                product_id = cart_item['product_id']
                product = db.get_product(product_id)
                
                if product:
                    # Check if still in stock
                    available_quantity = min(cart_item['quantity'], product['stock_quantity'])
                    
                    items.append({
                        'product_id': product_id,
                        'name': product['name'],
                        'type': product['type'],
                        'price': product['price'],
                        'quantity': cart_item['quantity'],
                        'available_quantity': available_quantity,
                        'total_price': product['price'] * cart_item['quantity'],
                        'in_stock': available_quantity == cart_item['quantity'],
                        'stock_available': product['stock_quantity']
                    })
                else:
                    # Product no longer exists, should be removed
                    logger.warning(f"Product {product_id} in cart but not found in database")
            
            return items
            
        except Exception as e:
            logger.error(f"Error getting cart items: {e}")
            return []
    
    @staticmethod
    def get_cart_total(user_id: int) -> float:
        """Calculate total cart value"""
        try:
            items = CartManager.get_cart_items(user_id)
            return sum(item['total_price'] for item in items if item['in_stock'])
        except Exception as e:
            logger.error(f"Error calculating cart total: {e}")
            return 0.0
    
    @staticmethod
    def get_cart_count(user_id: int) -> int:
        """Get total number of items in cart"""
        try:
            cart = db.get_cart(user_id)
            return sum(item['quantity'] for item in cart.values())
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0
    
    @staticmethod
    def clear_cart(user_id: int) -> Tuple[bool, str]:
        """Clear all items from cart"""
        try:
            success = db.clear_cart(user_id)
            
            if success:
                logger.info(f"Cart cleared for user {user_id}")
                return True, "Cart cleared successfully"
            else:
                return False, "Failed to clear cart"
                
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False, "An error occurred while clearing cart"
    
    @staticmethod
    def validate_cart(user_id: int) -> Tuple[bool, List[str]]:
        """Validate cart items (check stock, existence, etc.)"""
        try:
            cart = db.get_cart(user_id)
            issues = []
            updated_cart = {}
            cart_modified = False
            
            for product_key, cart_item in cart.items():
                product_id = cart_item['product_id']
                product = db.get_product(product_id)
                
                if not product:
                    issues.append(f"Product (ID: {product_id}) no longer available")
                    cart_modified = True
                    continue
                
                if product['stock_quantity'] == 0:
                    issues.append(f"{product['name']} is out of stock")
                    cart_modified = True
                    continue
                
                if product['stock_quantity'] < cart_item['quantity']:
                    # Reduce quantity to available stock
                    cart_item['quantity'] = product['stock_quantity']
                    issues.append(f"{product['name']} quantity reduced to {product['stock_quantity']} (available stock)")
                    cart_modified = True
                
                updated_cart[product_key] = cart_item
            
            # Update cart if modifications were made
            if cart_modified:
                db.update_cart(user_id, updated_cart)
            
            return len(issues) == 0, issues
            
        except Exception as e:
            logger.error(f"Error validating cart: {e}")
            return False, ["Error validating cart"]
    
    @staticmethod
    def update_quantity(user_id: int, product_id: int, new_quantity: int) -> Tuple[bool, str]:
        """Update quantity of specific item in cart"""
        try:
            if new_quantity <= 0:
                return CartManager.remove_from_cart(user_id, product_id)
            
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            if product['stock_quantity'] < new_quantity:
                return False, f"Only {product['stock_quantity']} items available"
            
            cart = db.get_cart(user_id)
            product_key = str(product_id)
            
            if product_key not in cart:
                return False, "Product not in cart"
            
            cart[product_key]['quantity'] = new_quantity
            
            success = db.update_cart(user_id, cart)
            
            if success:
                logger.info(f"Updated cart quantity: User {user_id}, Product {product_id}, New quantity {new_quantity}")
                return True, f"Updated {product['name']} quantity to {new_quantity}"
            else:
                return False, "Failed to update quantity"
                
        except Exception as e:
            logger.error(f"Error updating cart quantity: {e}")
            return False, "An error occurred while updating quantity"
    
    @staticmethod
    def get_cart_summary(user_id: int) -> Dict:
        """Get comprehensive cart summary"""
        try:
            items = CartManager.get_cart_items(user_id)
            total = CartManager.get_cart_total(user_id)
            count = CartManager.get_cart_count(user_id)
            
            # Check for issues
            is_valid, issues = CartManager.validate_cart(user_id)
            
            return {
                'items': items,
                'total_amount': total,
                'item_count': count,
                'is_valid': is_valid,
                'issues': issues,
                'is_empty': count == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {
                'items': [],
                'total_amount': 0.0,
                'item_count': 0,
                'is_valid': False,
                'issues': ["Error loading cart"],
                'is_empty': True
            }
    
    @staticmethod
    def reserve_stock(user_id: int) -> Tuple[bool, str]:
        """Reserve stock for items in cart (for checkout process)"""
        try:
            items = CartManager.get_cart_items(user_id)
            
            if not items:
                return False, "Cart is empty"
            
            # Check stock availability for all items
            for item in items:
                if not item['in_stock']:
                    return False, f"Insufficient stock for {item['name']}"
            
            # Reserve stock by reducing quantities
            reserved_items = []
            for item in items:
                success, message = ProductManager.update_stock(item['product_id'], -item['quantity'])
                if success:
                    reserved_items.append(item)
                else:
                    # Rollback previous reservations
                    for reserved_item in reserved_items:
                        ProductManager.update_stock(reserved_item['product_id'], reserved_item['quantity'])
                    return False, f"Failed to reserve stock for {item['name']}: {message}"
            
            logger.info(f"Stock reserved for user {user_id}: {len(reserved_items)} items")
            return True, f"Stock reserved for {len(reserved_items)} items"
            
        except Exception as e:
            logger.error(f"Error reserving stock: {e}")
            return False, "An error occurred while reserving stock"
    
    @staticmethod
    def release_stock(user_id: int, items: List[Dict]) -> bool:
        """Release reserved stock back to inventory"""
        try:
            for item in items:
                ProductManager.update_stock(item['product_id'], item['quantity'])
            
            logger.info(f"Stock released for user {user_id}: {len(items)} items")
            return True
            
        except Exception as e:
            logger.error(f"Error releasing stock: {e}")
            return False
