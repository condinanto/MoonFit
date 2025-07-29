"""
MOON FIT Telegram Bot - Main Application
E-commerce bot for fashion store with TON payments
"""
import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ConversationHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

# Import custom modules
from config import *
from database import db
from product_manager import ProductManager
from cart_manager import CartManager
from discount_manager import DiscountManager
from admin_panel import AdminPanel
from review_manager import ReviewManager
from ton_payments import ton_processor
from utils import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(WAITING_PRODUCT_NAME, WAITING_PRODUCT_TYPE, WAITING_PRODUCT_PRICE, 
 WAITING_PRODUCT_STOCK, WAITING_PRODUCT_DESCRIPTION, WAITING_PRODUCT_IMAGE,
 WAITING_DISCOUNT_CODE, WAITING_DISCOUNT_TYPE, WAITING_DISCOUNT_VALUE,
 WAITING_DISCOUNT_LIMIT, WAITING_DISCOUNT_EXPIRY, WAITING_REVIEW_RATING, 
 WAITING_REVIEW_COMMENT) = range(13)

class MoonFitBot:
    def __init__(self):
        self.admin_panel = AdminPanel()
        self.product_manager = ProductManager()
        self.cart_manager = CartManager()
        self.discount_manager = DiscountManager()
        self.review_manager = ReviewManager()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        
        # Register user in database
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Welcome message
        welcome_text = f"""
🌙 **Welcome to MOON FIT Store!** 

Hello {user.first_name}! 👋

We specialize in premium fashion:
👕 T-shirts
👔 Hoodies  
🧢 Hats

💰 **Pay with TON cryptocurrency**
⭐ **Customer reviews**
🎁 **Discount codes**
🛒 **Shopping cart**

What would you like to do?
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")],
            [InlineKeyboardButton("🎁 Apply Discount", callback_data="apply_discount")],
            [InlineKeyboardButton("📝 My Reviews", callback_data="my_reviews")],
        ]
        
        # Add admin button if user is admin
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button clicks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        try:
            # Main menu buttons
            if data == "browse_products":
                await self.show_products(query, context)
            elif data == "view_cart":
                await self.show_cart(query, context)
            elif data == "apply_discount":
                await self.show_discount_input(query, context)
            elif data == "my_reviews":
                await self.show_user_reviews(query, context)
            elif data == "admin_panel" and user_id == ADMIN_ID:
                await self.show_admin_panel(query, context)
            elif data == "back_to_main" or data == "back_to_store":
                await self.show_main_menu(query, context)
            
            # Product browsing
            elif data.startswith("category_"):
                category = data.split("_")[1]
                await self.show_category_products(query, context, category)
            elif data.startswith("product_"):
                product_id = int(data.split("_")[1])
                await self.show_product_details(query, context, product_id)
            elif data.startswith("reviews_"):
                product_id = int(data.split("_")[1])
                await self.show_product_reviews(query, context, product_id)
            elif data.startswith("add_review_"):
                product_id = int(data.split("_")[2])
                await self.start_review_process(query, context, product_id)
            elif data.startswith("review_rating_"):
                rating = int(data.split("_")[2])
                await self.handle_review_rating(query, context, rating)
            
            # Cart operations
            elif data.startswith("add_to_cart_"):
                product_id = int(data.split("_")[3])
                await self.add_to_cart(query, context, product_id)
            elif data.startswith("remove_from_cart_"):
                product_id = int(data.split("_")[3])
                await self.remove_from_cart(query, context, product_id)
            elif data == "checkout":
                await self.start_checkout(query, context)
            elif data == "clear_cart":
                await self.clear_cart(query, context)
            
            # Admin panel
            elif data.startswith("admin_"):
                await self.handle_admin_action(query, context, data)
            
            # Discount code generation
            elif data.startswith("discount_type_"):
                discount_type = data.split("_")[2]
                context.user_data['discount_type'] = discount_type
                await self.ask_discount_value(query, context)
            
            # Back navigation
            elif data == "back_to_products":
                await self.show_products(query, context)
            elif data == "back_to_admin":
                await self.show_admin_panel(query, context)
                
        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            await query.edit_message_text(
                "❌ An error occurred. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")
                ]])
            )
    
    async def show_main_menu(self, query, context):
        """Show main menu"""
        user = query.from_user
        
        welcome_text = f"""
🌙 **MOON FIT Store** 

Hello {user.first_name}! 👋

What would you like to do?
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")],
            [InlineKeyboardButton("🎁 Apply Discount", callback_data="apply_discount")],
            [InlineKeyboardButton("📝 My Reviews", callback_data="my_reviews")],
        ]
        
        if user.id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_products(self, query, context):
        """Show product categories"""
        text = """
🛍️ **Browse Products**

Choose a category:
        """
        
        keyboard = [
            [InlineKeyboardButton("👕 T-shirts", callback_data="category_tshirt")],
            [InlineKeyboardButton("👔 Hoodies", callback_data="category_hoodie")],
            [InlineKeyboardButton("🧢 Hats", callback_data="category_hat")],
            [InlineKeyboardButton("📦 All Products", callback_data="category_all")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_category_products(self, query, context, category):
        """Show products in category"""
        if category == "all":
            products = self.product_manager.get_all_products()
            category_name = "All Products"
        else:
            products = self.product_manager.get_products_by_type(category)
            category_name = {
                'tshirt': 'T-shirts',
                'hoodie': 'Hoodies', 
                'hat': 'Hats'
            }.get(category, category.title())
        
        if not products:
            text = f"📦 **{category_name}**\n\nNo products available in this category."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="browse_products")]]
        else:
            text = f"📦 **{category_name}**\n\nSelect a product:\n\n"
            
            keyboard = []
            for product in products:
                stock_emoji, stock_text = format_stock_status(product['stock_quantity'])
                product_text = f"{format_product_name(product['name'], product['type'])} - {format_currency(product['price'])}"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{stock_emoji} {product_text}",
                        callback_data=f"product_{product['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="browse_products")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_product_details(self, query, context, product_id):
        """Show detailed product information"""
        product = self.product_manager.get_product_details(product_id)
        
        if not product:
            await query.edit_message_text(
                "❌ Product not found.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data="browse_products")
                ]])
            )
            return
        
        # Get product reviews summary
        rating_summary = self.review_manager.get_product_rating_summary(product_id)
        
        stock_emoji, stock_text = format_stock_status(product['stock_quantity'])
        rating_text = format_rating_stars(rating_summary['average_rating'])
        
        text = f"""
{format_product_name(product['name'], product['type'])}

**Price:** {format_currency(product['price'])}
**Stock:** {stock_emoji} {stock_text}
**Rating:** {rating_text} ({rating_summary['total_reviews']} reviews)

**Description:**
{product.get('description', 'No description available.')}
        """
        
        keyboard = []
        
        # Add to cart button (only if in stock)
        if product['stock_quantity'] > 0:
            keyboard.append([
                InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_to_cart_{product_id}")
            ])
        
        # Reviews and navigation buttons
        keyboard.extend([
            [InlineKeyboardButton("⭐ View Reviews", callback_data=f"reviews_{product_id}")],
            [InlineKeyboardButton("📝 Write Review", callback_data=f"add_review_{product_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_products")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_product_reviews(self, query, context, product_id):
        """Show product reviews (public access)"""
        product = self.product_manager.get_product_details(product_id)
        
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        # Show ALL approved reviews (public access)
        reviews_text = self.review_manager.format_reviews_text(product_id)
        
        text = f"""
{format_product_name(product['name'], product['type'])}

{reviews_text}
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 Write Review", callback_data=f"add_review_{product_id}")],
            [InlineKeyboardButton("🔙 Back to Product", callback_data=f"product_{product_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_review_process(self, query, context, product_id):
        """Start review submission process"""
        user_id = query.from_user.id
        
        # Check if user can review this product
        can_review, message = self.review_manager.check_user_can_review(user_id, product_id)
        
        if not can_review:
            await query.answer(f"❌ {message}", show_alert=True)
            return
        
        product = self.product_manager.get_product_details(product_id)
        if not product:
            await query.answer("❌ Product not found", show_alert=True)
            return
        
        context.user_data['review_product_id'] = product_id
        
        text = f"""
📝 **Write a Review**

Product: {format_product_name(product['name'], product['type'])}

Please rate this product (1-5 stars):
        """
        
        keyboard = [
            [InlineKeyboardButton("⭐", callback_data="review_rating_1"),
             InlineKeyboardButton("⭐⭐", callback_data="review_rating_2"),
             InlineKeyboardButton("⭐⭐⭐", callback_data="review_rating_3")],
            [InlineKeyboardButton("⭐⭐⭐⭐", callback_data="review_rating_4"),
             InlineKeyboardButton("⭐⭐⭐⭐⭐", callback_data="review_rating_5")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"product_{product_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_review_rating(self, query, context, rating):
        """Handle review rating selection"""
        product_id = context.user_data.get('review_product_id')
        if not product_id:
            await query.answer("❌ Session expired", show_alert=True)
            return
        
        context.user_data['review_rating'] = rating
        
        product = self.product_manager.get_product_details(product_id)
        stars = "⭐" * rating
        
        text = f"""
📝 **Write a Review**

Product: {format_product_name(product['name'], product['type'])}
Rating: {stars}

Now write your review comment (optional):
Send a message with your review, or click "Submit" to submit without comment.
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Submit Review", callback_data="submit_review_no_comment")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"product_{product_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        context.user_data['waiting_for_review_comment'] = True
    
    async def show_user_reviews(self, query, context):
        """Show user's own reviews"""
        user_id = query.from_user.id
        reviews = self.review_manager.get_user_reviews(user_id)
        
        if not reviews:
            text = "📝 **Your Reviews**\n\nYou haven't written any reviews yet."
            keyboard = [
                [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ]
        else:
            text = f"📝 **Your Reviews** ({len(reviews)} reviews)\n\n"
            
            for review in reviews[:10]:  # Show last 10 reviews
                status = "✅ Approved" if review['approved'] else "⏳ Pending"
                stars = "⭐" * review['rating']
                date = format_datetime(review['created_at'], 'date')
                
                text += f"**{review['product_name']}** {stars}\n"
                text += f"Status: {status} | Date: {date}\n"
                
                if review['comment']:
                    comment = truncate_text(review['comment'], 100)
                    text += f"_{comment}_\n"
                
                text += "\n"
            
            keyboard = [
                [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_discount_input(self, query, context):
        """Show discount code input"""
        text = """
🎁 **Apply Discount Code**

Enter your discount code to get savings on your order!

Please send me your discount code:
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        context.user_data['waiting_for_discount'] = True
    
    async def show_cart(self, query, context):
        """Show shopping cart"""
        user_id = query.from_user.id
        cart_items = self.cart_manager.get_cart_items(user_id)
        
        if not cart_items:
            text = "🛒 **Your Cart is Empty**\n\nStart shopping to add items!"
            keyboard = [
                [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ]
        else:
            total_amount = self.cart_manager.get_cart_total(user_id)
            
            text = "🛒 **Your Shopping Cart**\n\n"
            
            for item in cart_items:
                text += f"• {item['name']} x{item['quantity']}\n"
                text += f"  {format_currency(item['price'])} each = {format_currency(item['total_price'])}\n\n"
            
            text += f"**Total: {format_currency(total_amount)}**"
            
            keyboard = []
            
            # Item removal buttons
            for item in cart_items:
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ Remove {item['name']}",
                        callback_data=f"remove_from_cart_{item['product_id']}"
                    )
                ])
            
            # Action buttons
            keyboard.extend([
                [InlineKeyboardButton("💰 Checkout", callback_data="checkout")],
                [InlineKeyboardButton("🗑️ Clear Cart", callback_data="clear_cart")],
                [InlineKeyboardButton("🛍️ Continue Shopping", callback_data="browse_products")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def add_to_cart(self, query, context, product_id):
        """Add product to cart"""
        user_id = query.from_user.id
        success, message = self.cart_manager.add_to_cart(user_id, product_id, 1)
        
        if success:
            await query.answer("✅ Added to cart!")
            # Refresh product details to show updated stock
            await self.show_product_details(query, context, product_id)
        else:
            await query.answer(f"❌ {message}", show_alert=True)
    
    async def remove_from_cart(self, query, context, product_id):
        """Remove product from cart"""
        user_id = query.from_user.id
        success, message = self.cart_manager.remove_from_cart(user_id, product_id)
        
        if success:
            await query.answer("✅ Removed from cart!")
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        # Refresh cart view
        await self.show_cart(query, context)
    
    async def clear_cart(self, query, context):
        """Clear entire cart"""
        user_id = query.from_user.id
        success, message = self.cart_manager.clear_cart(user_id)
        
        if success:
            await query.answer("✅ Cart cleared!")
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        await self.show_cart(query, context)
    
    async def start_checkout(self, query, context):
        """Start checkout process"""
        user_id = query.from_user.id
        cart_items = self.cart_manager.get_cart_items(user_id)
        
        if not cart_items:
            await query.answer("❌ Cart is empty!", show_alert=True)
            return
        
        total_amount = self.cart_manager.get_cart_total(user_id)
        
        # Create order
        order_id = db.create_order(user_id, cart_items, total_amount)
        
        if not order_id:
            await query.answer("❌ Failed to create order!", show_alert=True)
            return
        
        # Convert to TON amount (simplified conversion rate)
        ton_amount = total_amount * TON_CONVERSION_RATE
        
        # Generate payment instructions
        payment_message = ton_processor.format_payment_message(ton_amount, order_id, user_id)
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Sent Payment", callback_data=f"verify_payment_{order_id}")],
            [InlineKeyboardButton("❌ Cancel Order", callback_data=f"cancel_order_{order_id}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            payment_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        # Clear cart after creating order
        self.cart_manager.clear_cart(user_id)
    
    async def show_admin_panel(self, query, context):
        """Show admin panel"""
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ Access denied!", show_alert=True)
            return
        
        stats = self.admin_panel.get_dashboard_stats()
        
        text = f"""
⚙️ **Admin Panel**

📊 **Dashboard Stats:**
• Total Products: {stats['total_products']}
• Total Orders: {stats['total_orders']}
• Total Users: {stats['total_users']}
• Total Revenue: {format_currency(stats['total_revenue'])}
• Pending Reviews: {stats['pending_reviews']}

**Management Options:**
        """
        
        keyboard = [
            [InlineKeyboardButton("📦 Manage Products", callback_data="admin_products")],
            [InlineKeyboardButton("🎁 Manage Discounts", callback_data="admin_discounts")],
            [InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics")],
            [InlineKeyboardButton("⭐ Manage Reviews", callback_data="admin_reviews")],
            [InlineKeyboardButton("📋 Admin Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("🏠 Back to Store", callback_data="back_to_store")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_admin_action(self, query, context, data):
        """Handle admin panel actions"""
        if query.from_user.id != ADMIN_ID:
            await query.answer("❌ Access denied!", show_alert=True)
            return
        
        parts = data.split("_")
        action = parts[1]
        
        if action == "products":
            await self.show_admin_products(query, context)
        elif action == "discounts":
            await self.show_admin_discounts(query, context)
        elif action == "analytics":
            await self.show_admin_analytics(query, context)
        elif action == "reviews":
            await self.show_admin_reviews(query, context)
        elif action == "logs":
            await self.show_admin_logs(query, context)
        elif action == "add" and parts[2] == "product":
            context.user_data['admin_adding_product'] = True
            await self.start_add_product_conversation(query, context)
        elif action == "delete" and parts[2] == "product":
            product_id = int(parts[3])
            await self.delete_product(query, context, product_id)
        elif action == "generate" and parts[2] == "discount":
            await self.start_generate_discount(query, context)
        elif action == "approve" and parts[2] == "review":
            review_id = int(parts[3])
            await self.approve_review(query, context, review_id)
        elif action == "delete" and parts[2] == "review":
            review_id = int(parts[3])
            await self.delete_review(query, context, review_id)
    
    async def show_admin_products(self, query, context):
        """Show admin product management"""
        products = self.product_manager.get_all_products()
        
        text = "📦 **Product Management**\n\n"
        
        if products:
            text += "**Current Products:**\n"
            for product in products[:10]:  # Show first 10
                stock_emoji, _ = format_stock_status(product['stock_quantity'])
                text += f"• {stock_emoji} {product['name']} - {format_currency(product['price'])}\n"
            
            if len(products) > 10:
                text += f"\n_... and {len(products) - 10} more products_"
        else:
            text += "No products available."
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Product", callback_data="admin_add_product")],
        ]
        
        # Add delete buttons for existing products
        if products:
            for product in products[:5]:  # Show delete buttons for first 5
                keyboard.append([
                    InlineKeyboardButton(
                        f"🗑️ Delete {product['name'][:20]}...",
                        callback_data=f"admin_delete_product_{product['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def delete_product(self, query, context, product_id):
        """Delete a product"""
        success, message = self.product_manager.delete_product(product_id)
        
        if success:
            # Log admin action
            db.log_admin_action(
                query.from_user.id,
                "DELETE_PRODUCT",
                f"Deleted product ID: {product_id}"
            )
            await query.answer("✅ Product deleted!")
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        # Refresh product list
        await self.show_admin_products(query, context)
    
    async def show_admin_discounts(self, query, context):
        """Show admin discount management"""
        discounts = self.discount_manager.get_all_discounts()
        
        text = "🎁 **Discount Management**\n\n"
        
        if discounts:
            text += "**Active Discount Codes:**\n"
            for discount in discounts:
                status = "✅ Active" if discount['active'] else "❌ Inactive"
                expiry = format_datetime(discount['expires_at'], "date") if discount['expires_at'] else "No expiry"
                
                if discount['discount_type'] == 'percentage':
                    value_text = f"{discount['discount_value']}%"
                else:
                    value_text = format_currency(discount['discount_value'])
                
                text += f"• **{discount['code']}** - {value_text} ({status})\n"
                text += f"  Used: {discount['used_count']}/{discount['usage_limit'] or '∞'} | Expires: {expiry}\n\n"
        else:
            text += "No discount codes available."
        
        keyboard = [
            [InlineKeyboardButton("➕ Generate New Code", callback_data="admin_generate_discount")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def start_generate_discount(self, query, context):
        """Start discount code generation process"""
        text = """
🎁 **Generate Discount Code**

Choose discount type:
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Percentage Off", callback_data="discount_type_percentage")],
            [InlineKeyboardButton("💰 Fixed Amount Off", callback_data="discount_type_fixed")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_discounts")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def ask_discount_value(self, query, context):
        """Ask for discount value"""
        discount_type = context.user_data.get('discount_type')
        
        if discount_type == 'percentage':
            text = "📊 **Percentage Discount**\n\nEnter the percentage (e.g., 10 for 10% off):"
        else:
            text = f"💰 **Fixed Amount Discount**\n\nEnter the discount amount in {CURRENCY} (e.g., 5.00):"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_discounts")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        context.user_data['waiting_for_discount_value'] = True
    
    async def show_admin_analytics(self, query, context):
        """Show admin analytics dashboard"""
        try:
            analytics = self.admin_panel.get_analytics_data()
            
            text = f"""
📊 **Analytics Dashboard**

**Sales Overview:**
• Total Revenue: {format_currency(analytics['total_revenue'])}
• Total Orders: {analytics['total_orders']}
• Average Order Value: {format_currency(analytics['avg_order_value'])}

**Product Performance:**
• Total Products: {analytics['total_products']}
• Most Popular: {analytics['most_popular_product']}
• Low Stock Items: {analytics['low_stock_count']}

**User Statistics:**
• Total Users: {analytics['total_users']}
• New Users Today: {analytics['new_users_today']}

**Review Statistics:**
• Total Reviews: {analytics['total_reviews']}
• Average Rating: {analytics['avg_rating']}/5.0
• Pending Reviews: {analytics['pending_reviews']}

**Recent Activity:**
{analytics['recent_activity']}
            """
            
        except Exception as e:
            logger.error(f"Error in analytics: {e}")
            text = "❌ **Analytics Error**\n\nThere was an error loading analytics data. Please try again later."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_analytics")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_admin_reviews(self, query, context):
        """Show admin review management"""
        pending_reviews = self.review_manager.get_pending_reviews()
        
        text = self.review_manager.format_pending_reviews_text(pending_reviews)
        
        keyboard = []
        
        # Add approve/delete buttons for pending reviews
        for review in pending_reviews[:3]:  # Show first 3
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ Approve #{review['id']}",
                    callback_data=f"admin_approve_review_{review['id']}"
                ),
                InlineKeyboardButton(
                    f"❌ Delete #{review['id']}",
                    callback_data=f"admin_delete_review_{review['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def approve_review(self, query, context, review_id):
        """Approve a review"""
        success, message = self.review_manager.approve_review(review_id, query.from_user.id)
        
        if success:
            await query.answer("✅ Review approved!")
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        # Refresh review list
        await self.show_admin_reviews(query, context)
    
    async def delete_review(self, query, context, review_id):
        """Delete a review"""
        success, message = self.review_manager.delete_review(review_id, query.from_user.id)
        
        if success:
            await query.answer("✅ Review deleted!")
        else:
            await query.answer(f"❌ {message}", show_alert=True)
        
        # Refresh review list
        await self.show_admin_reviews(query, context)
    
    async def show_admin_logs(self, query, context):
        """Show admin activity logs"""
        try:
            logs = self.admin_panel.get_admin_logs()
            
            text = "📋 **Admin Activity Logs**\n\n"
            
            if logs:
                for log in logs[:15]:  # Show last 15 logs
                    timestamp = format_datetime(log['timestamp'], "short")
                    text += f"**{timestamp}** - {log['action']}\n"
                    if log['details']:
                        text += f"_{log['details']}_\n"
                    text += "\n"
            else:
                text += "No admin activity logs found."
                
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            text = "📋 **Admin Activity Logs**\n\n❌ Error loading logs. Please try again later."
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    # Message handlers
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Handle review comment input
        if context.user_data.get('waiting_for_review_comment'):
            await self.handle_review_comment(update, context, text)
            return
        
        # Handle product addition steps
        if context.user_data.get('admin_adding_product'):
            await self.handle_product_input(update, context, text)
            return
        
        # Handle discount value input
        if context.user_data.get('waiting_for_discount_value'):
            await self.handle_discount_value_input(update, context, text)
            return
        
        # Handle discount code input
        if context.user_data.get('waiting_for_discount'):
            context.user_data['waiting_for_discount'] = False
            
            cart_total = self.cart_manager.get_cart_total(user_id)
            if cart_total == 0:
                await update.message.reply_text(
                    "❌ Your cart is empty. Add items to your cart before applying discount codes.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products")
                    ]])
                )
                return
            
            is_valid, message, discount_amount = self.discount_manager.validate_discount_code(text, cart_total)
            
            if is_valid:
                context.user_data['applied_discount'] = {
                    'code': text.upper(),
                    'amount': discount_amount
                }
                
                new_total = cart_total - discount_amount
                await update.message.reply_text(
                    f"✅ {message}\n\n"
                    f"**Original Total:** {format_currency(cart_total)}\n"
                    f"**Discount:** -{format_currency(discount_amount)}\n"
                    f"**New Total:** {format_currency(new_total)}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🛒 View Cart", callback_data="view_cart")],
                        [InlineKeyboardButton("💰 Checkout", callback_data="checkout")]
                    ])
                )
            else:
                await update.message.reply_text(
                    f"❌ {message}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🎁 Try Again", callback_data="apply_discount")
                    ]])
                )
    
    async def handle_review_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle review comment input"""
        user_id = update.effective_user.id
        comment = update.message.text.strip()
        rating = context.user_data.get('review_rating')
        product_id = context.user_data.get('review_product_id')
        
        if not rating or not product_id:
            await update.message.reply_text("❌ Session expired. Please start again.")
            return
        
        # Submit review
        success, message = self.review_manager.add_review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=comment if comment else None
        )
        
        if success:
            keyboard = [[InlineKeyboardButton("✅ Back to Product", callback_data=f"product_{product_id}")]]
            await update.message.reply_text(
                f"✅ {message}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(f"❌ {message}")
        
        # Clear review data
        context.user_data.pop('review_rating', None)
        context.user_data.pop('review_product_id', None)
        context.user_data.pop('waiting_for_review_comment', None)
    
    async def handle_product_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product creation input"""
        text = update.message.text.strip()
        step = context.user_data.get('product_step', 'name')
        
        if step == 'name':
            if not text:
                await update.message.reply_text("❌ Product name cannot be empty. Please try again:")
                return
            
            context.user_data['product_name'] = text
            context.user_data['product_step'] = 'type'
            
            keyboard = [
                [InlineKeyboardButton("👕 T-shirt", callback_data="product_type_tshirt")],
                [InlineKeyboardButton("👔 Hoodie", callback_data="product_type_hoodie")],
                [InlineKeyboardButton("🧢 Hat", callback_data="product_type_hat")],
                [InlineKeyboardButton("❌ Cancel", callback_data="admin_products")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Product name: **{text}**\n\nSelect product type:",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        
        elif step == 'price':
            try:
                price = float(text)
                if price <= 0:
                    await update.message.reply_text("❌ Price must be greater than 0. Please try again:")
                    return
                
                context.user_data['product_price'] = price
                context.user_data['product_step'] = 'stock'
                
                await update.message.reply_text(
                    f"Product: **{context.user_data['product_name']}**\n"
                    f"Type: **{context.user_data['product_type']}**\n"
                    f"Price: **{format_currency(price)}**\n\n"
                    f"Enter the stock quantity:",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except ValueError:
                await update.message.reply_text("❌ Invalid price format. Please enter a number:")
        
        elif step == 'stock':
            try:
                stock = int(text)
                if stock < 0:
                    await update.message.reply_text("❌ Stock cannot be negative. Please try again:")
                    return
                
                context.user_data['product_stock'] = stock
                context.user_data['product_step'] = 'description'
                
                await update.message.reply_text(
                    f"Product: **{context.user_data['product_name']}**\n"
                    f"Type: **{context.user_data['product_type']}**\n"
                    f"Price: **{format_currency(context.user_data['product_price'])}**\n"
                    f"Stock: **{stock}**\n\n"
                    f"Enter a product description (or send 'skip' to skip):",
                    parse_mode=ParseMode.MARKDOWN
                )
                
            except ValueError:
                await update.message.reply_text("❌ Invalid stock quantity. Please enter a number:")
        
        elif step == 'description':
            description = text if text.lower() != 'skip' else None
            
            # Create the product
            success, message = self.product_manager.add_product(
                name=context.user_data['product_name'],
                product_type=context.user_data['product_type'],
                price=context.user_data['product_price'],
                stock_quantity=context.user_data['product_stock'],
                description=description
            )
            
            if success:
                # Log admin action
                db.log_admin_action(
                    update.effective_user.id,
                    "ADD_PRODUCT",
                    f"Added product: {context.user_data['product_name']}"
                )
                
                keyboard = [[InlineKeyboardButton("✅ Back to Products", callback_data="admin_products")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **Product Added Successfully!**\n\n"
                    f"**{context.user_data['product_name']}** has been added to the store.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(f"❌ {message}")
            
            # Clear product data
            for key in ['admin_adding_product', 'product_step', 'product_name', 'product_type', 'product_price', 'product_stock']:
                context.user_data.pop(key, None)
    
    async def handle_discount_value_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle discount value input"""
        try:
            value = float(update.message.text.strip())
            discount_type = context.user_data.get('discount_type')
            
            if value <= 0:
                await update.message.reply_text("❌ Discount value must be greater than 0. Please try again:")
                return
            
            if discount_type == 'percentage' and value > 100:
                await update.message.reply_text("❌ Percentage cannot exceed 100%. Please try again:")
                return
            
            # Generate the discount code
            success, message = self.discount_manager.generate_discount_code(
                discount_type=discount_type,
                discount_value=value,
                usage_limit=10,  # Default limit
                expires_in_days=30  # Default expiry
            )
            
            if success:
                # Log admin action
                db.log_admin_action(
                    update.effective_user.id,
                    "GENERATE_DISCOUNT",
                    f"Generated discount code: {discount_type} {value}"
                )
                
                keyboard = [[InlineKeyboardButton("✅ Back to Discounts", callback_data="admin_discounts")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ **{message}**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(f"❌ {message}")
            
            # Clear user data
            context.user_data.pop('discount_type', None)
            context.user_data.pop('waiting_for_discount_value', None)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid format. Please enter a number:")
    
    async def start_add_product_conversation(self, query, context):
        """Start add product conversation"""
        text = "➕ **Add New Product**\n\nEnter the product name:"
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_products")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        context.user_data['admin_adding_product'] = True
        context.user_data['product_step'] = 'name'
    
    async def handle_callback_query_product_type(self, query, context):
        """Handle product type selection"""
        if query.data.startswith("product_type_"):
            product_type = query.data.split("_")[2]
            context.user_data['product_type'] = product_type
            context.user_data['product_step'] = 'price'
            
            type_name = {
                'tshirt': 'T-shirt',
                'hoodie': 'Hoodie',
                'hat': 'Hat'
            }.get(product_type, product_type)
            
            await query.edit_message_text(
                f"Product: **{context.user_data['product_name']}**\n"
                f"Type: **{type_name}**\n\n"
                f"Enter the product price (in {CURRENCY}):",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_submit_review_no_comment(self, query, context):
        """Handle submitting review without comment"""
        user_id = query.from_user.id
        rating = context.user_data.get('review_rating')
        product_id = context.user_data.get('review_product_id')
        
        if not rating or not product_id:
            await query.answer("❌ Session expired", show_alert=True)
            return
        
        # Submit review without comment
        success, message = self.review_manager.add_review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=None
        )
        
        if success:
            keyboard = [[InlineKeyboardButton("✅ Back to Product", callback_data=f"product_{product_id}")]]
            await query.edit_message_text(
                f"✅ {message}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(f"❌ {message}")
        
        # Clear review data
        context.user_data.pop('review_rating', None)
        context.user_data.pop('review_product_id', None)
        context.user_data.pop('waiting_for_review_comment', None)

def main():
    """Main function to run the bot"""
    # Initialize database and create sample products
    db.init_database()
    
    # Add sample products if none exist
    if not ProductManager().get_all_products():
        logger.info("No products found, adding sample products...")
        ProductManager.add_sample_products()
        logger.info("Sample products added successfully")
    
    # Create bot instance
    bot = MoonFitBot()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(
        bot.handle_callback_query_product_type, 
        pattern="^product_type_"
    ))
    application.add_handler(CallbackQueryHandler(
        bot.handle_submit_review_no_comment, 
        pattern="^submit_review_no_comment$"
    ))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    
    # Run the bot
    logger.info("Starting MOON FIT Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
