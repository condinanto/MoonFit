"""
Inline keyboard layouts for MOON FIT Telegram Bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional

class Keyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("👕 T-Shirts", callback_data="category_tshirt"),
                InlineKeyboardButton("👔 Hoodies", callback_data="category_hoodie")
            ],
            [
                InlineKeyboardButton("🧢 Hats", callback_data="category_hat")
            ],
            [
                InlineKeyboardButton("🛒 My Cart", callback_data="view_cart"),
                InlineKeyboardButton("📦 My Orders", callback_data="my_orders")
            ],
            [
                InlineKeyboardButton("⭐ Reviews", callback_data="reviews_menu"),
                InlineKeyboardButton("💬 Support", callback_data="support")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Admin panel main menu"""
        keyboard = [
            [
                InlineKeyboardButton("📦 Manage Products", callback_data="admin_products"),
                InlineKeyboardButton("📊 Orders", callback_data="admin_orders")
            ],
            [
                InlineKeyboardButton("🎫 Discount Codes", callback_data="admin_discounts"),
                InlineKeyboardButton("⭐ Reviews", callback_data="admin_reviews")
            ],
            [
                InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics"),
                InlineKeyboardButton("📝 Logs", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton("🏠 Back to Store", callback_data="back_to_home")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def category_menu(products: List[Dict], category: str) -> InlineKeyboardMarkup:
        """Product category listing"""
        keyboard = []
        
        for product in products:
            keyboard.append([
                InlineKeyboardButton(
                    f"{product['name']} - {product['price']:.2f} TON",
                    callback_data=f"product_{product['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🏠 Home", callback_data="back_to_home")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def product_detail(product_id: int, in_cart: bool = False) -> InlineKeyboardMarkup:
        """Product detail page keyboard"""
        keyboard = []
        
        if not in_cart:
            keyboard.append([
                InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_cart_{product_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ In Cart", callback_data="noop"),
                InlineKeyboardButton("➖ Remove", callback_data=f"remove_cart_{product_id}")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("⭐ Reviews", callback_data=f"product_reviews_{product_id}"),
                InlineKeyboardButton("✍️ Write Review", callback_data=f"write_review_{product_id}")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="back"),
                InlineKeyboardButton("🏠 Home", callback_data="back_to_home")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cart_menu(cart_items: List[Dict], total: float) -> InlineKeyboardMarkup:
        """Shopping cart keyboard"""
        keyboard = []
        
        if cart_items:
            for item in cart_items:
                keyboard.append([
                    InlineKeyboardButton(
                        f"➖ {item['name']} (x{item['quantity']})",
                        callback_data=f"remove_cart_{item['product_id']}"
                    ),
                    InlineKeyboardButton(
                        f"➕",
                        callback_data=f"add_cart_{item['product_id']}"
                    )
                ])
            
            keyboard.extend([
                [InlineKeyboardButton("🗑️ Clear Cart", callback_data="clear_cart")],
                [InlineKeyboardButton("💳 Checkout", callback_data="checkout")]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🛍️ Start Shopping", callback_data="back_to_home")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🏠 Home", callback_data="back_to_home")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def checkout_menu(has_discount: bool = False) -> InlineKeyboardMarkup:
        """Checkout process keyboard"""
        keyboard = []
        
        if not has_discount:
            keyboard.append([
                InlineKeyboardButton("🎫 Apply Discount Code", callback_data="apply_discount")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("❌ Remove Discount", callback_data="remove_discount")
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("💰 Pay with TON", callback_data="pay_ton")],
            [
                InlineKeyboardButton("🔙 Back to Cart", callback_data="view_cart"),
                InlineKeyboardButton("🏠 Home", callback_data="back_to_home")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def payment_verification() -> InlineKeyboardMarkup:
        """Payment verification keyboard"""
        keyboard = [
            [InlineKeyboardButton("🔄 Check Payment", callback_data="check_payment")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data="cancel_order")],
            [InlineKeyboardButton("💬 Support", callback_data="support")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def order_management(order_id: int, status: str) -> InlineKeyboardMarkup:
        """Order management for admin"""
        keyboard = []
        
        if status == 'paid':
            keyboard.append([
                InlineKeyboardButton("📦 Mark as Shipped", callback_data=f"ship_order_{order_id}")
            ])
        elif status == 'shipped':
            keyboard.append([
                InlineKeyboardButton("✅ Mark as Delivered", callback_data=f"deliver_order_{order_id}")
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_orders")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_products_menu() -> InlineKeyboardMarkup:
        """Admin products management menu"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product"),
                InlineKeyboardButton("📝 Edit Product", callback_data="admin_edit_product")
            ],
            [
                InlineKeyboardButton("📋 List Products", callback_data="admin_list_products"),
                InlineKeyboardButton("🗑️ Delete Product", callback_data="admin_delete_product")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_product_list(products: List[Dict], action: str = "view") -> InlineKeyboardMarkup:
        """Admin product listing with actions"""
        keyboard = []
        
        for product in products:
            status = "✅" if product['active'] else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {product['name']} - {product['price']:.2f} TON",
                    callback_data=f"admin_product_{action}_{product['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="admin_products")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_discount_menu() -> InlineKeyboardMarkup:
        """Admin discount codes menu"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Create Code", callback_data="admin_create_discount"),
                InlineKeyboardButton("📋 List Codes", callback_data="admin_list_discounts")
            ],
            [
                InlineKeyboardButton("📊 Usage Stats", callback_data="admin_discount_stats"),
                InlineKeyboardButton("🗑️ Manage Codes", callback_data="admin_manage_discounts")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_discount_list(discounts: List[Dict]) -> InlineKeyboardMarkup:
        """Admin discount codes listing"""
        keyboard = []
        
        for discount in discounts:
            status = "✅" if discount['active'] else "❌"
            expiry = "∞" if not discount['expiry_date'] else discount['expiry_date'][:10]
            usage = f"{discount['used_count']}/{discount['usage_limit'] or '∞'}"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {discount['code']} ({usage}) - Expires: {expiry}",
                    callback_data=f"admin_discount_manage_{discount['id']}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Back", callback_data="admin_discounts")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_discount_actions(discount_id: int, is_active: bool) -> InlineKeyboardMarkup:
        """Admin discount code actions"""
        keyboard = []
        
        if is_active:
            keyboard.append([
                InlineKeyboardButton("❌ Deactivate", callback_data=f"admin_discount_toggle_{discount_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("✅ Activate", callback_data=f"admin_discount_toggle_{discount_id}")
            ])
        
        keyboard.extend([
            [InlineKeyboardButton("📊 View Usage", callback_data=f"admin_discount_usage_{discount_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_list_discounts")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_review_actions(review_id: int) -> InlineKeyboardMarkup:
        """Admin review moderation actions"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_review_{review_id}"),
                InlineKeyboardButton("❌ Delete", callback_data=f"admin_delete_review_{review_id}")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="admin_reviews")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def rating_keyboard(product_id: int) -> InlineKeyboardMarkup:
        """Rating selection keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("⭐", callback_data=f"rate_{product_id}_1"),
                InlineKeyboardButton("⭐⭐", callback_data=f"rate_{product_id}_2"),
                InlineKeyboardButton("⭐⭐⭐", callback_data=f"rate_{product_id}_3")
            ],
            [
                InlineKeyboardButton("⭐⭐⭐⭐", callback_data=f"rate_{product_id}_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data=f"rate_{product_id}_5")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="back")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def yes_no_keyboard(action: str) -> InlineKeyboardMarkup:
        """Yes/No confirmation keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ No", callback_data="cancel")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_home_keyboard() -> InlineKeyboardMarkup:
        """Simple back to home keyboard"""
        keyboard = [
            [InlineKeyboardButton("🏠 Home", callback_data="back_to_home")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def product_type_keyboard() -> InlineKeyboardMarkup:
        """Product type selection for admin"""
        keyboard = [
            [
                InlineKeyboardButton("👕 T-Shirt", callback_data="type_tshirt"),
                InlineKeyboardButton("👔 Hoodie", callback_data="type_hoodie")
            ],
            [
                InlineKeyboardButton("🧢 Hat", callback_data="type_hat")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="admin_products")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def discount_type_keyboard() -> InlineKeyboardMarkup:
        """Discount type selection for admin"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Fixed Amount", callback_data="discount_type_fixed"),
                InlineKeyboardButton("📊 Percentage", callback_data="discount_type_percentage")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="admin_discounts")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

# Helper function to create navigation keyboard
def create_navigation_keyboard(back_action: str = "back", home: bool = True) -> InlineKeyboardMarkup:
    """Create a navigation keyboard with back and home buttons"""
    keyboard = []
    
    if back_action != "back":
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_action)])
    
    if home:
        keyboard.append([InlineKeyboardButton("🏠 Home", callback_data="back_to_home")])
    
    return InlineKeyboardMarkup(keyboard)
