"""
Configuration settings for MOON FIT Telegram Bot
"""
import os

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7318781825:AAF-Hg1XgVg14fEsPSEt1u1NXyDCXxIYhlg")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7213670865"))  # Replace with actual admin Telegram ID

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "moonfit_store.db")

# TON Payment Configuration
TON_WALLET_ADDRESS = os.getenv("TON_WALLET_ADDRESS", "UQBjcatsfBR_MJBtzaxjkmrl9HS4aAQsWkAGGvSDf10_onwi")  # Replace with actual TON wallet
TON_API_KEY = os.getenv("TON_API_KEY", "your_ton_api_key")
TON_TESTNET = os.getenv("TON_TESTNET", "true").lower() == "true"
TON_CONVERSION_RATE = float(os.getenv("TON_CONVERSION_RATE", "0.001"))  # USD to TON rate

# Payment Settings
PAYMENT_TIMEOUT = int(os.getenv("PAYMENT_TIMEOUT", "1800"))  # 30 minutes
MIN_TON_AMOUNT = float(os.getenv("MIN_TON_AMOUNT", "0.01"))

# Store Configuration
STORE_NAME = "MOON FIT"
CURRENCY = "USD"
STORE_DESCRIPTION = "Premium fashion store specializing in T-shirts, hoodies, and hats"

# Product Categories
PRODUCT_CATEGORIES = {
    'tshirt': {
        'name': 'T-shirts',
        'emoji': '👕',
        'description': 'Premium quality t-shirts'
    },
    'hoodie': {
        'name': 'Hoodies',
        'emoji': '👔',
        'description': 'Comfortable hoodies for all seasons'
    },
    'hat': {
        'name': 'Hats',
        'emoji': '🧢',
        'description': 'Stylish hats and caps'
    }
}

# Pagination Settings
PRODUCTS_PER_PAGE = 10
REVIEWS_PER_PAGE = 10
ORDERS_PER_PAGE = 10

# Rate Limiting
MAX_CART_ITEMS = 20
MAX_REVIEW_LENGTH = 500
MAX_PRODUCT_NAME_LENGTH = 100
MAX_PRODUCT_DESCRIPTION_LENGTH = 1000

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Feature Flags
ENABLE_REVIEWS = True
ENABLE_DISCOUNTS = True
ENABLE_ANALYTICS = True
ENABLE_ADMIN_LOGS = True

# Default Values
DEFAULT_PRODUCT_IMAGE = "https://via.placeholder.com/300x300?text=MOON+FIT"
DEFAULT_STOCK_THRESHOLD = 5  # Low stock warning threshold
