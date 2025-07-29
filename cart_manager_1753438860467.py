"""
Shopping cart management for MOON FIT Telegram Bot
"""
import logging
from typing import List, Dict, Tuple, Optional
from database import db
from config import CURRENCY

logger = logging.getLogger(__name__)

class CartManager:
    @staticmethod
    def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str]:
        """Add product to user's cart"""
        try:
            # Get product details
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            # Check stock availability
            if product['stock_quantity'] < quantity:
                return False, f"Only {product['stock_quantity']} items available in stock"
            
            # Get current cart
            cart = db.get_user_cart(user_id)
            
            # Check if product already in cart
            for item in cart:
                if item['product_id'] == product_id:
                    new_quantity = item['quantity'] + quantity
                    if new_quantity > product['stock_quantity']:
                        return False, f"Cannot add more items. Stock limit: {product['stock_quantity']}"
                    item['quantity'] = new_quantity
                    item['total_price'] = item['quantity'] * item['price']
                    break
            else:
                # Add new item to cart
                cart_item = {
                    'product_id': product_id,
                    'name': product['name'],
                    'type': product['type'],
                    'price': product['price'],
                    'quantity': quantity,
                    'total_price': product['price'] * quantity,
                    'image_url': product.get('image_url')
                }
                cart.append(cart_item)
            
            # Update cart in database
            db.update_user_cart(user_id, cart)
            logger.info(f"Added {quantity}x {product['name']} to user {user_id}'s cart")
            return True, f"Added {product['name']} to cart"
            
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            return False, "Failed to add item to cart"
    
    @staticmethod
    def remove_from_cart(user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str]:
        """Remove product from user's cart"""
        try:
            cart = db.get_user_cart(user_id)
            
            for i, item in enumerate(cart):
                if item['product_id'] == product_id:
                    if item['quantity'] <= quantity:
                        # Remove item completely
                        removed_item = cart.pop(i)
                        db.update_user_cart(user_id, cart)
                        return True, f"Removed {removed_item['name']} from cart"
                    else:
                        # Reduce quantity
                        item['quantity'] -= quantity
                        item['total_price'] = item['quantity'] * item['price']
                        db.update_user_cart(user_id, cart)
                        return True, f"Reduced {item['name']} quantity by {quantity}"
            
            return False, "Item not found in cart"
            
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            return False, "Failed to remove item from cart"
    
    @staticmethod
    def get_cart_summary(user_id: int) -> Dict:
        """Get cart summary with totals"""
        try:
            cart = db.get_user_cart(user_id)
            
            if not cart:
                return {
                    'items': [],
                    'total_items': 0,
                    'total_price': 0.0,
                    'is_empty': True
                }
            
            total_items = sum(item['quantity'] for item in cart)
            total_price = sum(item['total_price'] for item in cart)
            
            return {
                'items': cart,
                'total_items': total_items,
                'total_price': total_price,
                'is_empty': False
            }
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {
                'items': [],
                'total_items': 0,
                'total_price': 0.0,
                'is_empty': True
            }
    
    @staticmethod
    def clear_cart(user_id: int) -> bool:
        """Clear user's cart"""
        try:
            db.clear_user_cart(user_id)
            logger.info(f"Cleared cart for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return False
    
    @staticmethod
    def validate_cart(user_id: int) -> Tuple[bool, List[str]]:
        """Validate cart items against current stock and availability"""
        try:
            cart = db.get_user_cart(user_id)
            errors = []
            updated_cart = []
            cart_modified = False
            
            for item in cart:
                product = db.get_product(item['product_id'])
                
                if not product:
                    errors.append(f"❌ {item['name']} is no longer available")
                    cart_modified = True
                    continue
                
                if not product['active']:
                    errors.append(f"❌ {item['name']} has been discontinued")
                    cart_modified = True
                    continue
                
                if product['stock_quantity'] < item['quantity']:
                    if product['stock_quantity'] > 0:
                        # Reduce quantity to available stock
                        item['quantity'] = product['stock_quantity']
                        item['total_price'] = item['quantity'] * item['price']
                        errors.append(f"⚠️ {item['name']} quantity reduced to {product['stock_quantity']} (stock limit)")
                        cart_modified = True
                    else:
                        errors.append(f"❌ {item['name']} is out of stock")
                        cart_modified = True
                        continue
                
                # Check if price has changed
                if abs(product['price'] - item['price']) > 0.001:
                    item['price'] = product['price']
                    item['total_price'] = item['quantity'] * item['price']
                    errors.append(f"💰 {item['name']} price updated to {product['price']:.3f} {CURRENCY}")
                    cart_modified = True
                
                updated_cart.append(item)
            
            if cart_modified:
                db.update_user_cart(user_id, updated_cart)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Error validating cart: {e}")
            return False, ["Error validating cart items"]
    
    @staticmethod
    def get_cart_text(user_id: int) -> str:
        """Get formatted cart text for display"""
        cart_summary = CartManager.get_cart_summary(user_id)
        
        if cart_summary['is_empty']:
            return "🛒 Your cart is empty\n\nStart shopping to add items to your cart!"
        
        text = "🛒 **Your Shopping Cart**\n\n"
        
        for item in cart_summary['items']:
            text += f"**{item['name']}**\n"
            text += f"   Type: {item['type'].title()}\n"
            text += f"   Price: {item['price']:.3f} {CURRENCY} each\n"
            text += f"   Quantity: {item['quantity']}\n"
            text += f"   Subtotal: {item['total_price']:.3f} {CURRENCY}\n\n"
        
        text += f"**Total Items:** {cart_summary['total_items']}\n"
        text += f"**Total Price:** {cart_summary['total_price']:.3f} {CURRENCY}"
        
        return text
    
    @staticmethod
    def is_product_in_cart(user_id: int, product_id: int) -> bool:
        """Check if product is already in cart"""
        try:
            cart = db.get_user_cart(user_id)
            return any(item['product_id'] == product_id for item in cart)
        except Exception as e:
            logger.error(f"Error checking if product in cart: {e}")
            return False
    
    @staticmethod
    def get_cart_item_quantity(user_id: int, product_id: int) -> int:
        """Get quantity of specific product in cart"""
        try:
            cart = db.get_user_cart(user_id)
            for item in cart:
                if item['product_id'] == product_id:
                    return item['quantity']
            return 0
        except Exception as e:
            logger.error(f"Error getting cart item quantity: {e}")
            return 0
    
    @staticmethod
    def update_item_quantity(user_id: int, product_id: int, new_quantity: int) -> Tuple[bool, str]:
        """Update specific item quantity in cart"""
        try:
            if new_quantity <= 0:
                return CartManager.remove_from_cart(user_id, product_id, 999)  # Remove all
            
            # Get product to check stock
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            if new_quantity > product['stock_quantity']:
                return False, f"Only {product['stock_quantity']} items available in stock"
            
            cart = db.get_user_cart(user_id)
            
            for item in cart:
                if item['product_id'] == product_id:
                    item['quantity'] = new_quantity
                    item['total_price'] = item['quantity'] * item['price']
                    db.update_user_cart(user_id, cart)
                    return True, f"Updated {item['name']} quantity to {new_quantity}"
            
            return False, "Item not found in cart"
            
        except Exception as e:
            logger.error(f"Error updating item quantity: {e}")
            return False, "Failed to update item quantity"
    
    @staticmethod
    def prepare_order_data(user_id: int) -> Optional[Dict]:
        """Prepare cart data for order creation"""
        try:
            cart_summary = CartManager.get_cart_summary(user_id)
            
            if cart_summary['is_empty']:
                return None
            
            # Validate cart before creating order
            is_valid, errors = CartManager.validate_cart(user_id)
            if not is_valid:
                return None
            
            order_data = {
                'user_id': user_id,
                'products': cart_summary['items'],
                'total_amount': cart_summary['total_price'],
                'total_items': cart_summary['total_items']
            }
            
            return order_data
            
        except Exception as e:
            logger.error(f"Error preparing order data: {e}")
            return None

# Global cart manager instance
cart_manager = CartManager()
