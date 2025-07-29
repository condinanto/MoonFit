"""
MOON FIT Telegram Bot - Main Application
A comprehensive fashion store bot with TON payments, admin management, and discount system
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.error import TelegramError

# Import our modules
from config import (
    BOT_TOKEN, ADMIN_ID, WELCOME_MESSAGE, ADMIN_WELCOME, 
    ERROR_MESSAGES, SUCCESS_MESSAGES, HOST, PORT
)
from database import db
from keyboards import Keyboards
from cart_manager import cart_manager
from discount_manager import discount_manager
from review_manager import review_manager
from product_manager import product_manager
from admin_panel import admin_panel
from ton_payments import ton_processor
from utils import format_currency, validate_input, send_admin_notification

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(ADDING_PRODUCT_NAME, ADDING_PRODUCT_TYPE, ADDING_PRODUCT_PRICE, 
 ADDING_PRODUCT_DESCRIPTION, ADDING_PRODUCT_IMAGE, ADDING_PRODUCT_STOCK,
 CREATING_DISCOUNT_CODE, CREATING_DISCOUNT_TYPE, CREATING_DISCOUNT_VALUE,
 CREATING_DISCOUNT_LIMIT, CREATING_DISCOUNT_EXPIRY,
 WRITING_REVIEW_RATING, WRITING_REVIEW_COMMENT,
 APPLYING_DISCOUNT_CODE, WAITING_PAYMENT) = range(15)

class MoonFitBot:
    def __init__(self):
        self.application = None
        self.pending_payments = {}  # Track pending payments
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            
            # Create or update user in database
            db.create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Clear any existing conversation state
            db.clear_user_state(user.id)
            
            # Check if user is admin
            if admin_panel.is_admin(user.id):
                welcome_text = ADMIN_WELCOME
                keyboard = Keyboards.admin_menu()
            else:
                welcome_text = WELCOME_MESSAGE
                keyboard = Keyboards.main_menu()
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(ERROR_MESSAGES['database_error'])
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            data = query.data
            
            logger.info(f"Button callback: {data} from user {user_id}")
            
            # Route callback data to appropriate handlers
            if data == "back_to_home":
                await self.show_main_menu(query, user_id)
            elif data == "admin_panel":
                await self.show_admin_panel(query, user_id)
            elif data.startswith("category_"):
                await self.show_category(query, data.split("_")[1])
            elif data.startswith("product_"):
                await self.show_product_detail(query, int(data.split("_")[1]))
            elif data.startswith("add_cart_"):
                await self.add_to_cart(query, int(data.split("_")[2]))
            elif data.startswith("remove_cart_"):
                await self.remove_from_cart(query, int(data.split("_")[2]))
            elif data == "view_cart":
                await self.show_cart(query, user_id)
            elif data == "clear_cart":
                await self.clear_cart(query, user_id)
            elif data == "checkout":
                await self.show_checkout(query, user_id)
            elif data == "apply_discount":
                await self.apply_discount_start(query, user_id)
            elif data == "remove_discount":
                await self.remove_discount(query, user_id)
            elif data == "pay_ton":
                await self.process_payment(query, user_id)
            elif data == "check_payment":
                await self.check_payment_status(query, user_id)
            elif data == "cancel_order":
                await self.cancel_current_order(query, user_id)
            elif data == "my_orders":
                await self.show_user_orders(query, user_id)
            elif data == "reviews_menu":
                await self.show_reviews_menu(query)
            elif data.startswith("product_reviews_"):
                await self.show_product_reviews(query, int(data.split("_")[2]))
            elif data.startswith("write_review_"):
                await self.start_write_review(query, int(data.split("_")[2]))
            elif data.startswith("rate_"):
                await self.handle_rating(query, data)
            elif data == "support":
                await self.show_support(query)
            
            # Admin callbacks
            elif admin_panel.is_admin(user_id):
                await self.handle_admin_callback(query, data, user_id)
            else:
                await query.edit_message_text(ERROR_MESSAGES['admin_only'])
                
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            try:
                await query.edit_message_text(ERROR_MESSAGES['database_error'])
            except:
                pass
    
    async def show_main_menu(self, query, user_id: int):
        """Show main menu"""
        db.clear_user_state(user_id)
        
        if admin_panel.is_admin(user_id):
            text = ADMIN_WELCOME
            keyboard = Keyboards.admin_menu()
        else:
            text = WELCOME_MESSAGE
            keyboard = Keyboards.main_menu()
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_admin_panel(self, query, user_id: int):
        """Show admin panel"""
        if not admin_panel.is_admin(user_id):
            await query.edit_message_text(ERROR_MESSAGES['admin_only'])
            return
        
        stats = admin_panel.get_dashboard_stats()
        text = admin_panel.format_dashboard_text(stats)
        keyboard = Keyboards.admin_menu()
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_category(self, query, category: str):
        """Show products in category"""
        products = product_manager.get_products_by_category(category)
        
        if not products:
            text = f"No products available in {product_manager.PRODUCT_TYPES.get(category, category)} category."
            keyboard = Keyboards.back_home_keyboard()
        else:
            text = f"🛍️ **{product_manager.PRODUCT_TYPES.get(category, category)}**\n\nChoose a product to view details:"
            keyboard = Keyboards.category_menu(products, category)
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_product_detail(self, query, product_id: int):
        """Show product details"""
        product = product_manager.get_product_details(product_id, include_reviews=True)
        
        if not product:
            await query.edit_message_text(
                ERROR_MESSAGES['product_not_found'],
                reply_markup=Keyboards.back_home_keyboard()
            )
            return
        
        user_id = query.from_user.id
        in_cart = cart_manager.is_product_in_cart(user_id, product_id)
        
        text = product_manager.format_product_text(product, detailed=True)
        keyboard = Keyboards.product_detail(product_id, in_cart)
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def add_to_cart(self, query, product_id: int):
        """Add product to cart"""
        user_id = query.from_user.id
        success, message = cart_manager.add_to_cart(user_id, product_id)
        
        if success:
            await query.answer(SUCCESS_MESSAGES['order_placed'].replace('Order placed', 'Added to cart'))
            # Refresh product detail view
            await self.show_product_detail(query, product_id)
        else:
            await query.answer(message, show_alert=True)
    
    async def remove_from_cart(self, query, product_id: int):
        """Remove product from cart"""
        user_id = query.from_user.id
        success, message = cart_manager.remove_from_cart(user_id, product_id)
        
        await query.answer(message)
        
        # Check if we're in cart view or product view
        if "cart" in query.message.text.lower():
            await self.show_cart(query, user_id)
        else:
            await self.show_product_detail(query, product_id)
    
    async def show_cart(self, query, user_id: int):
        """Show shopping cart"""
        cart_text = cart_manager.get_cart_text(user_id)
        cart_summary = cart_manager.get_cart_summary(user_id)
        keyboard = Keyboards.cart_menu(cart_summary['items'], cart_summary['total_price'])
        
        await query.edit_message_text(cart_text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def clear_cart(self, query, user_id: int):
        """Clear shopping cart"""
        cart_manager.clear_cart(user_id)
        await query.answer("Cart cleared!")
        await self.show_cart(query, user_id)
    
    async def show_checkout(self, query, user_id: int):
        """Show checkout page"""
        # Validate cart
        is_valid, errors = cart_manager.validate_cart(user_id)
        
        if not is_valid:
            error_text = "❌ **Cart Validation Errors:**\n\n" + "\n".join(errors)
            error_text += "\n\nPlease review your cart and try again."
            keyboard = Keyboards.cart_menu([], 0)
            await query.edit_message_text(error_text, reply_markup=keyboard, parse_mode='Markdown')
            return
        
        cart_summary = cart_manager.get_cart_summary(user_id)
        
        if cart_summary['is_empty']:
            await query.edit_message_text(
                "🛒 Your cart is empty!\n\nAdd some items before checkout.",
                reply_markup=Keyboards.main_menu()
            )
            return
        
        # Check for applied discount
        state, state_data = db.get_user_state(user_id)
        has_discount = state_data.get('discount_code') is not None
        
        text = "💳 **Checkout**\n\n"
        text += f"**Items:** {cart_summary['total_items']}\n"
        text += f"**Subtotal:** {format_currency(cart_summary['total_price'])}\n"
        
        if has_discount:
            discount_amount = state_data.get('discount_amount', 0)
            final_amount = cart_summary['total_price'] - discount_amount
            text += f"**Discount:** -{format_currency(discount_amount)} ({state_data.get('discount_code')})\n"
            text += f"**Final Total:** {format_currency(final_amount)}\n"
        else:
            text += f"**Total:** {format_currency(cart_summary['total_price'])}\n"
        
        keyboard = Keyboards.checkout_menu(has_discount)
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def apply_discount_start(self, query, user_id: int):
        """Start discount code application process"""
        db.set_user_state(user_id, 'APPLYING_DISCOUNT')
        
        text = "🎫 **Enter Discount Code**\n\nPlease type your discount code:"
        keyboard = Keyboards.back_home_keyboard()
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def remove_discount(self, query, user_id: int):
        """Remove applied discount"""
        state, state_data = db.get_user_state(user_id)
        if state_data.get('discount_code'):
            state_data.pop('discount_code', None)
            state_data.pop('discount_amount', None)
            db.set_user_state(user_id, state, state_data)
        
        await query.answer("Discount removed!")
        await self.show_checkout(query, user_id)
    
    async def process_payment(self, query, user_id: int):
        """Process TON payment"""
        try:
            # Prepare order data
            order_data = cart_manager.prepare_order_data(user_id)
            if not order_data:
                await query.edit_message_text(
                    "❌ Unable to process order. Please check your cart.",
                    reply_markup=Keyboards.back_home_keyboard()
                )
                return
            
            # Check for discount
            state, state_data = db.get_user_state(user_id)
            discount_code = state_data.get('discount_code')
            discount_amount = state_data.get('discount_amount', 0)
            final_amount = order_data['total_amount'] - discount_amount
            
            # Create order
            order_id = db.create_order(
                user_id=user_id,
                products=order_data['products'],
                total_amount=order_data['total_amount'],
                discount_code=discount_code,
                discount_amount=discount_amount,
                final_amount=final_amount
            )
            
            # Generate payment instructions
            payment_message = ton_processor.format_payment_message(final_amount, order_id, user_id)
            keyboard = Keyboards.payment_verification()
            
            # Store payment info in user state
            payment_data = {
                'order_id': order_id,
                'amount': final_amount,
                'comment': f"ORDER_{order_id}_{user_id}"
            }
            db.set_user_state(user_id, 'WAITING_PAYMENT', payment_data)
            
            await query.edit_message_text(payment_message, reply_markup=keyboard, parse_mode='Markdown')
            
            # Send notification to admin
            await send_admin_notification(
                self.application.bot,
                f"🔔 New Order #{order_id}\n"
                f"Customer: {query.from_user.first_name or 'Unknown'}\n"
                f"Amount: {format_currency(final_amount)}\n"
                f"Items: {order_data['total_items']}"
            )
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            await query.edit_message_text(
                ERROR_MESSAGES['database_error'],
                reply_markup=Keyboards.back_home_keyboard()
            )
    
    async def check_payment_status(self, query, user_id: int):
        """Check payment verification status"""
        state, state_data = db.get_user_state(user_id)
        
        if state != 'WAITING_PAYMENT' or not state_data.get('order_id'):
            await query.answer("No pending payment found")
            return
        
        order_id = state_data['order_id']
        expected_amount = state_data['amount']
        comment = state_data['comment']
        
        await query.answer("Checking payment status...")
        
        # Verify payment (short timeout for manual check)
        success, tx_hash = await ton_processor.verify_payment(expected_amount, comment, timeout=5)
        
        if success:
            # Payment confirmed
            db.update_order_status(order_id, 'paid', tx_hash)
            
            # Clear cart and user state
            cart_manager.clear_cart(user_id)
            db.clear_user_state(user_id)
            
            # Record discount usage if applicable
            if state_data.get('discount_code'):
                discount = discount_manager.get_discount_info(state_data['discount_code'])
                if discount:
                    db.use_discount_code(discount['id'], user_id, order_id)
            
            success_text = f"✅ **Payment Confirmed!**\n\n"
            success_text += f"Order #{order_id} has been paid successfully.\n"
            success_text += f"Amount: {format_currency(expected_amount)}\n"
            success_text += f"Transaction: `{tx_hash}`\n\n"
            success_text += "Your order is now being processed!"
            
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(success_text, reply_markup=keyboard, parse_mode='Markdown')
            
            # Notify admin
            await send_admin_notification(
                self.application.bot,
                f"💰 Payment Confirmed!\n"
                f"Order #{order_id}\n"
                f"Amount: {format_currency(expected_amount)}\n"
                f"Customer: {query.from_user.first_name or 'Unknown'}"
            )
            
        else:
            await query.answer("Payment not found yet. Please wait a few minutes after sending.")
    
    async def cancel_current_order(self, query, user_id: int):
        """Cancel current pending order"""
        state, state_data = db.get_user_state(user_id)
        
        if state == 'WAITING_PAYMENT' and state_data.get('order_id'):
            order_id = state_data['order_id']
            db.update_order_status(order_id, 'cancelled')
            db.clear_user_state(user_id)
            
            await query.answer("Order cancelled")
            await self.show_main_menu(query, user_id)
        else:
            await query.answer("No pending order to cancel")
    
    async def show_user_orders(self, query, user_id: int):
        """Show user's order history"""
        orders = db.get_user_orders(user_id)
        
        if not orders:
            text = "📦 **No orders found**\n\nYou haven't placed any orders yet."
        else:
            text = f"📦 **Your Orders** ({len(orders)})\n\n"
            
            for order in orders[:10]:  # Show last 10 orders
                status_emoji = {
                    'pending': '⏳',
                    'paid': '💰',
                    'shipped': '📦',
                    'delivered': '✅',
                    'cancelled': '❌'
                }.get(order['status'], '❓')
                
                order_date = order['created_at'][:10]  # YYYY-MM-DD
                text += f"**Order #{order['id']}** {status_emoji}\n"
                text += f"Date: {order_date}\n"
                text += f"Total: {format_currency(order['final_amount'])}\n"
                text += f"Status: {order['status'].title()}\n\n"
        
        keyboard = Keyboards.back_home_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_reviews_menu(self, query):
        """Show reviews menu"""
        text = "⭐ **Reviews**\n\nBrowse product reviews or share your experience!"
        
        keyboard = [
            [InlineKeyboardButton("👕 T-Shirt Reviews", callback_data="reviews_category_tshirt")],
            [InlineKeyboardButton("👔 Hoodie Reviews", callback_data="reviews_category_hoodie")],
            [InlineKeyboardButton("🧢 Hat Reviews", callback_data="reviews_category_hat")],
            [InlineKeyboardButton("🏠 Home", callback_data="back_to_home")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_product_reviews(self, query, product_id: int):
        """Show reviews for specific product"""
        text = review_manager.format_reviews_text(product_id)
        keyboard = Keyboards.back_home_keyboard()
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def start_write_review(self, query, product_id: int):
        """Start writing a review"""
        user_id = query.from_user.id
        
        # Check if user can review
        can_review, message = review_manager.check_user_can_review(user_id, product_id)
        
        if not can_review:
            await query.answer(message, show_alert=True)
            return
        
        # Start review process
        db.set_user_state(user_id, 'WRITING_REVIEW', {'product_id': product_id})
        
        text = "⭐ **Write a Review**\n\nPlease rate this product (1-5 stars):"
        keyboard = Keyboards.rating_keyboard(product_id)
        
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def handle_rating(self, query, data: str):
        """Handle rating selection"""
        parts = data.split('_')
        product_id = int(parts[1])
        rating = int(parts[2])
        user_id = query.from_user.id
        
        # Update state with rating
        state, state_data = db.get_user_state(user_id)
        state_data['rating'] = rating
        db.set_user_state(user_id, 'WRITING_REVIEW_COMMENT', state_data)
        
        text = f"⭐ **Review Rating: {rating}/5**\n\n"
        text += "Now write your review comment (or type 'skip' to submit rating only):"
        
        keyboard = Keyboards.back_home_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def show_support(self, query):
        """Show support information"""
        text = f"💬 **Customer Support**\n\n"
        text += f"Need help? Contact our support team:\n\n"
        text += f"📧 **Email:** support@moonfit.store\n"
        text += f"💬 **Telegram:** @moonfitsupport\n"
        text += f"🕐 **Hours:** 9 AM - 6 PM (UTC)\n\n"
        text += f"For order issues, please include your order number.\n"
        text += f"We'll respond within 24 hours!"
        
        keyboard = Keyboards.back_home_keyboard()
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def handle_admin_callback(self, query, data: str, admin_id: int):
        """Handle admin-specific callbacks"""
        if data == "admin_products":
            keyboard = Keyboards.admin_products_menu()
            text = "📦 **Product Management**\n\nChoose an action:"
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_add_product":
            db.set_user_state(admin_id, 'ADDING_PRODUCT_NAME')
            text = "➕ **Add New Product**\n\nPlease enter the product name:"
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_list_products":
            products = product_manager.get_all_products(admin_view=True)
            text = product_manager.format_product_list(products)
            keyboard = Keyboards.admin_products_menu()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_discounts":
            keyboard = Keyboards.admin_discount_menu()
            text = "🎫 **Discount Management**\n\nChoose an action:"
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_create_discount":
            db.set_user_state(admin_id, 'CREATING_DISCOUNT_CODE')
            text = "🎫 **Create Discount Code**\n\nEnter the discount code (3-20 characters, letters and numbers only):"
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_list_discounts":
            discounts = discount_manager.get_all_discount_codes()
            if discounts:
                keyboard = Keyboards.admin_discount_list(discounts)
                text = "🎫 **Discount Codes**\n\nClick on a code to manage it:"
            else:
                keyboard = Keyboards.admin_discount_menu()
                text = "🎫 **No discount codes found**\n\nCreate your first discount code!"
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_orders":
            orders = admin_panel.get_recent_orders()
            text = admin_panel.format_orders_text(orders)
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_reviews":
            pending_reviews = review_manager.get_pending_reviews()
            text = review_manager.format_pending_reviews_text(pending_reviews)
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        elif data == "admin_analytics":
            report = admin_panel.get_analytics_report()
            text = admin_panel.format_analytics_report(report)
            keyboard = Keyboards.back_home_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
        else:
            await query.answer("Feature coming soon!")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on user state"""
        try:
            user_id = update.effective_user.id
            text = update.message.text.strip()
            
            state, state_data = db.get_user_state(user_id)
            
            if state == 'APPLYING_DISCOUNT':
                await self.handle_discount_code_input(update, text)
            elif state == 'WRITING_REVIEW_COMMENT':
                await self.handle_review_comment_input(update, text)
            elif state == 'ADDING_PRODUCT_NAME':
                await self.handle_add_product_name(update, text)
            elif state == 'ADDING_PRODUCT_PRICE':
                await self.handle_add_product_price(update, text)
            elif state == 'ADDING_PRODUCT_DESCRIPTION':
                await self.handle_add_product_description(update, text)
            elif state == 'ADDING_PRODUCT_STOCK':
                await self.handle_add_product_stock(update, text)
            elif state == 'CREATING_DISCOUNT_CODE':
                await self.handle_create_discount_code(update, text)
            elif state == 'CREATING_DISCOUNT_VALUE':
                await self.handle_create_discount_value(update, text)
            else:
                # No active conversation, show main menu
                keyboard = Keyboards.main_menu()
                await update.message.reply_text(
                    "Please use the menu buttons below:",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text(ERROR_MESSAGES['database_error'])
    
    async def handle_discount_code_input(self, update: Update, code: str):
        """Handle discount code input"""
        user_id = update.effective_user.id
        cart_summary = cart_manager.get_cart_summary(user_id)
        
        success, message, discount_amount = discount_manager.apply_discount(
            code, user_id, cart_summary['total_price']
        )
        
        if success:
            # Store discount in user state
            state_data = {
                'discount_code': code.upper(),
                'discount_amount': discount_amount
            }
            db.set_user_state(user_id, 'CHECKOUT', state_data)
            
            await update.message.reply_text(f"✅ {message}")
            
            # Show updated checkout
            text = "💳 **Checkout - Discount Applied**\n\n"
            text += f"**Items:** {cart_summary['total_items']}\n"
            text += f"**Subtotal:** {format_currency(cart_summary['total_price'])}\n"
            text += f"**Discount:** -{format_currency(discount_amount)} ({code.upper()})\n"
            text += f"**Final Total:** {format_currency(cart_summary['total_price'] - discount_amount)}\n"
            
            keyboard = Keyboards.checkout_menu(has_discount=True)
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ {message}")
            
            # Show checkout without discount
            keyboard = Keyboards.checkout_menu(has_discount=False)
            text = "💳 **Checkout**\n\nTry a different discount code or proceed to payment."
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def handle_review_comment_input(self, update: Update, comment: str):
        """Handle review comment input"""
        user_id = update.effective_user.id
        state, state_data = db.get_user_state(user_id)
        
        product_id = state_data.get('product_id')
        rating = state_data.get('rating')
        
        if not product_id or not rating:
            await update.message.reply_text("❌ Review session expired. Please try again.")
            return
        
        # Handle skip
        review_comment = None if comment.lower() == 'skip' else comment
        
        # Add review
        success, message = review_manager.add_review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=review_comment
        )
        
        # Clear state
        db.clear_user_state(user_id)
        
        if success:
            await update.message.reply_text(f"✅ {message}")
        else:
            await update.message.reply_text(f"❌ {message}")
        
        # Show main menu
        keyboard = Keyboards.main_menu()
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=keyboard
        )
    
    async def handle_add_product_name(self, update: Update, name: str):
        """Handle product name input in admin flow"""
        user_id = update.effective_user.id
        
        if not admin_panel.is_admin(user_id):
            await update.message.reply_text(ERROR_MESSAGES['admin_only'])
            return
        
        if len(name) < 2:
            await update.message.reply_text("❌ Product name must be at least 2 characters. Please try again:")
            return
        
        # Store name and ask for type
        db.set_user_state(user_id, 'ADDING_PRODUCT_TYPE', {'name': name})
        
        text = f"✅ Product name: **{name}**\n\nNow select the product type:"
        keyboard = Keyboards.product_type_keyboard()
        
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def handle_add_product_price(self, update: Update, price_text: str):
        """Handle product price input"""
        user_id = update.effective_user.id
        
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError("Price must be positive")
            
            state, state_data = db.get_user_state(user_id)
            state_data['price'] = price
            db.set_user_state(user_id, 'ADDING_PRODUCT_DESCRIPTION', state_data)
            
            await update.message.reply_text(
                f"✅ Price: {format_currency(price)}\n\n"
                "Now enter a product description (or type 'skip'):"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid price. Please enter a valid number:")
    
    async def handle_add_product_description(self, update: Update, description: str):
        """Handle product description input"""
        user_id = update.effective_user.id
        state, state_data = db.get_user_state(user_id)
        
        if description.lower() != 'skip':
            state_data['description'] = description
        
        db.set_user_state(user_id, 'ADDING_PRODUCT_STOCK', state_data)
        
        await update.message.reply_text(
            "Now enter the initial stock quantity (number of items):"
        )
    
    async def handle_add_product_stock(self, update: Update, stock_text: str):
        """Handle product stock input and create product"""
        user_id = update.effective_user.id
        
        try:
            stock = int(stock_text)
            if stock < 0:
                raise ValueError("Stock cannot be negative")
            
            state, state_data = db.get_user_state(user_id)
            
            # Create product
            success, message, product_id = product_manager.add_product(
                name=state_data['name'],
                product_type=state_data['product_type'],
                price=state_data['price'],
                description=state_data.get('description'),
                stock_quantity=stock,
                admin_id=user_id
            )
            
            # Clear state
            db.clear_user_state(user_id)
            
            if success:
                await update.message.reply_text(f"✅ {message}\nProduct ID: {product_id}")
            else:
                await update.message.reply_text(f"❌ {message}")
            
            # Show admin menu
            keyboard = Keyboards.admin_menu()
            await update.message.reply_text(
                "Product creation completed. What would you like to do next?",
                reply_markup=keyboard
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid stock quantity. Please enter a valid number:")
    
    async def handle_create_discount_code(self, update: Update, code: str):
        """Handle discount code creation"""
        user_id = update.effective_user.id
        
        if not discount_manager.validate_code_format(code):
            await update.message.reply_text(
                "❌ Invalid code format. Use 3-20 characters, letters and numbers only. Please try again:"
            )
            return
        
        if not discount_manager.check_code_availability(code):
            await update.message.reply_text(
                "❌ This discount code already exists. Please choose a different code:"
            )
            return
        
        # Store code and ask for type
        db.set_user_state(user_id, 'CREATING_DISCOUNT_TYPE', {'code': code.upper()})
        
        text = f"✅ Discount code: **{code.upper()}**\n\nSelect discount type:"
        keyboard = Keyboards.discount_type_keyboard()
        
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')
    
    async def handle_create_discount_value(self, update: Update, value_text: str):
        """Handle discount value input and create discount"""
        user_id = update.effective_user.id
        
        try:
            value = float(value_text)
            state, state_data = db.get_user_state(user_id)
            
            discount_type = state_data['discount_type']
            
            # Validate value based on type
            if discount_type == 'percentage' and (value <= 0 or value > 100):
                raise ValueError("Percentage must be between 0-100")
            elif discount_type == 'fixed' and value <= 0:
                raise ValueError("Fixed amount must be positive")
            
            # Create discount code with default settings
            success, message = discount_manager.create_discount_code(
                code=state_data['code'],
                discount_type=discount_type,
                discount_value=value,
                created_by=user_id
            )
            
            # Clear state
            db.clear_user_state(user_id)
            
            if success:
                await update.message.reply_text(f"✅ {message}")
            else:
                await update.message.reply_text(f"❌ {message}")
            
            # Show admin discount menu
            keyboard = Keyboards.admin_discount_menu()
            await update.message.reply_text(
                "Discount code creation completed. What would you like to do next?",
                reply_markup=keyboard
            )
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid value: {e}. Please try again:")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again or contact support."
                )
            except:
                pass
    
    def run(self):
        """Run the bot"""
        try:
            # Create application
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            logger.info("MOON FIT Bot starting...")
            
            # Run the bot
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

if __name__ == "__main__":
    # Initialize bot
    bot = MoonFitBot()
    
    # Run bot
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise
