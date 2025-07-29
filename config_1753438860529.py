"""
Configuration file for MOON FIT Telegram Bot
"""
import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '7318781825:AAF-Hg1XgVg14fEsPSEt1u1NXyDCXxIYhlg')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7213670865'))
BOT_USERNAME = '@MOONFITBOT'
BOT_NAME = 'MOON FIT'

# TON Configuration
TON_WALLET_ADDRESS = os.getenv('TON_WALLET_ADDRESS', 'UQBvVEFeJdKt9KR8KXKc8m4TGWqlDNjHGDZF4OMQ8K9XN9KX')
TON_API_KEY = os.getenv('TON_API_KEY', 'default_key')
TON_TESTNET = os.getenv('TON_TESTNET', 'True').lower() == 'true'

# Database Configuration
DATABASE_PATH = 'moonfit_store.db'

# App Configuration
HOST = '0.0.0.0'
PORT = 5000

# Payment Configuration
PAYMENT_TIMEOUT = 300  # 5 minutes in seconds
MIN_TON_AMOUNT = 0.01  # Minimum TON amount for payments

# Store Configuration
STORE_NAME = 'MOON FIT'
STORE_DESCRIPTION = 'Fashion store for stylish T-shirts, hoodies, and hats'
CURRENCY = 'TON'

# Message Templates
WELCOME_MESSAGE = f"""
🌙 Welcome to {STORE_NAME}! 

Your premium destination for stylish fashion:
👕 T-shirts with unique designs
👔 Comfortable hoodies
🧢 Trendy hats

All payments accepted in TON cryptocurrency 💎

Choose an option below to get started:
"""

ADMIN_WELCOME = f"""
🔧 Admin Panel - {STORE_NAME}

Welcome to the administrative dashboard.
Manage your store efficiently:

📦 Products Management
💰 Orders & Sales
🎫 Discount Codes
⭐ Customer Reviews
📊 Analytics

Select an option below:
"""

# Error Messages
ERROR_MESSAGES = {
    'invalid_command': '❌ Invalid command. Please use the menu buttons.',
    'payment_failed': '❌ Payment verification failed. Please try again.',
    'product_not_found': '❌ Product not found.',
    'insufficient_stock': '❌ Insufficient stock available.',
    'invalid_discount': '❌ Invalid or expired discount code.',
    'admin_only': '❌ This feature is only available for administrators.',
    'database_error': '❌ Database error occurred. Please try again later.',
    'network_error': '❌ Network error. Please check your connection.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'order_placed': '✅ Order placed successfully! Payment instructions sent.',
    'payment_confirmed': '✅ Payment confirmed! Your order is being processed.',
    'product_added': '✅ Product added successfully!',
    'product_updated': '✅ Product updated successfully!',
    'product_deleted': '✅ Product deleted successfully!',
    'discount_created': '✅ Discount code created successfully!',
    'review_submitted': '✅ Review submitted successfully!'
}
