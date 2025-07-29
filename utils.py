"""
Utility functions for MOON FIT Telegram Bot
"""
import re
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from config import CURRENCY, ADMIN_ID

logger = logging.getLogger(__name__)

def format_currency(amount: float, currency: str = CURRENCY) -> str:
    """Format amount as currency string"""
    try:
        return f"{amount:.3f} {currency}"
    except (TypeError, ValueError):
        return f"0.000 {currency}"

def validate_input(text: str, input_type: str = "text", min_length: int = 1, max_length: int = 1000) -> tuple[bool, str]:
    """
    Validate user input based on type
    Returns (is_valid, error_message)
    """
    if not text or not isinstance(text, str):
        return False, "Input cannot be empty"
    
    text = text.strip()
    
    if len(text) < min_length:
        return False, f"Input must be at least {min_length} characters"
    
    if len(text) > max_length:
        return False, f"Input must be no more than {max_length} characters"
    
    if input_type == "price":
        try:
            price = float(text)
            if price <= 0:
                return False, "Price must be greater than 0"
            if price > 10000:
                return False, "Price is too high"
            return True, ""
        except ValueError:
            return False, "Invalid price format"
    
    elif input_type == "stock":
        try:
            stock = int(text)
            if stock < 0:
                return False, "Stock cannot be negative"
            return True, ""
        except ValueError:
            return False, "Invalid stock quantity"
    
    elif input_type == "discount_code":
        if not re.match(r'^[A-Z0-9]+$', text.upper()):
            return False, "Code must contain only letters and numbers"
        if len(text) < 3 or len(text) > 20:
            return False, "Code must be 3-20 characters long"
        return True, ""
    
    elif input_type == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, text):
            return False, "Invalid email format"
        return True, ""
    
    elif input_type == "url":
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, text):
            return False, "Invalid URL format"
        return True, ""
    
    # Default text validation
    return True, ""

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input for database storage"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    # Remove potentially dangerous characters for Markdown
    dangerous_chars = ['`', '*', '_', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in dangerous_chars:
        text = text.replace(char, f"\\{char}")
    
    return text

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    if not text:
        return ""
    
    # Characters that need escaping in Telegram Markdown
    escape_chars = ['_', '*', '`', '[']
    
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    
    return text

def format_datetime(dt_string: str, format_type: str = "full") -> str:
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        if format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M")
        elif format_type == "short":
            return dt.strftime("%m-%d %H:%M")
        else:  # full
            return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    except (ValueError, AttributeError):
        return "Invalid date"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_product_name(name: str, product_type: str) -> str:
    """Format product name with type emoji"""
    type_emojis = {
        'tshirt': '👕',
        'hoodie': '👔',
        'hat': '🧢'
    }
    
    emoji = type_emojis.get(product_type, '📦')
    return f"{emoji} {name}"

def format_order_status(status: str) -> str:
    """Format order status with emoji"""
    status_map = {
        'pending': '⏳ Pending',
        'paid': '💰 Paid',
        'shipped': '📦 Shipped',
        'delivered': '✅ Delivered',
        'cancelled': '❌ Cancelled'
    }
    
    return status_map.get(status, f"❓ {status.title()}")

def format_rating_stars(rating: float) -> str:
    """Format rating as star emojis"""
    if rating <= 0:
        return "☆☆☆☆☆"
    
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    return "⭐" * full_stars + "⭐" * half_star + "☆" * empty_stars

def parse_callback_data(data: str) -> Dict[str, Any]:
    """Parse callback data into components"""
    parts = data.split("_")
    
    if len(parts) < 2:
        return {"action": data}
    
    result = {"action": parts[0]}
    
    # Handle common patterns
    if parts[0] in ["product", "add", "remove"]:
        if len(parts) >= 3:
            result["target"] = parts[1]
            result["id"] = int(parts[2]) if parts[2].isdigit() else parts[2]
    elif parts[0] == "admin":
        result["section"] = parts[1]
        if len(parts) >= 3:
            result["action"] = parts[2]
            if len(parts) >= 4:
                result["id"] = int(parts[3]) if parts[3].isdigit() else parts[3]
    
    return result

def generate_order_summary(products: List[Dict], total_amount: float, 
                         discount_code: str = None, discount_amount: float = 0) -> str:
    """Generate order summary text"""
    text = "📋 **Order Summary**\n\n"
    
    for item in products:
        text += f"• {item['name']} x{item['quantity']}\n"
        text += f"  {format_currency(item['price'])} each = {format_currency(item['total_price'])}\n\n"
    
    text += f"**Subtotal:** {format_currency(total_amount)}\n"
    
    if discount_code:
        text += f"**Discount ({discount_code}):** -{format_currency(discount_amount)}\n"
        text += f"**Final Total:** {format_currency(total_amount - discount_amount)}\n"
    else:
        text += f"**Total:** {format_currency(total_amount)}\n"
    
    return text

def validate_ton_address(address: str) -> bool:
    """Basic TON address validation"""
    if not address:
        return False
    
    # TON addresses are typically 48 characters long and start with specific characters
    if len(address) != 48:
        return False
    
    # Basic pattern check (this is simplified, real validation would be more complex)
    if not re.match(r'^[A-Za-z0-9_-]+$', address):
        return False
    
    return True

def calculate_discount(total_amount: float, discount_type: str, discount_value: float) -> float:
    """Calculate discount amount"""
    if discount_type == "percentage":
        discount = total_amount * (discount_value / 100)
    else:  # fixed amount
        discount = discount_value
    
    # Ensure discount doesn't exceed total
    return min(discount, total_amount)

async def send_admin_notification(bot, message: str):
    """Send notification to admin"""
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=message,
            parse_mode='Markdown'
        )
        logger.info("Admin notification sent successfully")
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")

def format_user_info(user) -> str:
    """Format user information for display"""
    if not user:
        return "Unknown User"
    
    name_parts = []
    
    if hasattr(user, 'first_name') and user.first_name:
        name_parts.append(user.first_name)
    
    if hasattr(user, 'last_name') and user.last_name:
        name_parts.append(user.last_name)
    
    name = " ".join(name_parts) if name_parts else "Unknown"
    
    if hasattr(user, 'username') and user.username:
        return f"@{user.username} ({name})"
    
    return name

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def is_valid_image_url(url: str) -> bool:
    """Check if URL is likely a valid image URL"""
    if not url:
        return False
    
    # Basic URL pattern
    if not re.match(r'^https?://', url):
        return False
    
    # Check for common image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
    url_lower = url.lower()
    
    return any(url_lower.endswith(ext) for ext in image_extensions)

def generate_payment_reference(order_id: int, user_id: int) -> str:
    """Generate payment reference for TON transactions"""
    return f"ORDER_{order_id}_{user_id}_{int(datetime.now().timestamp())}"

def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data showing only last few characters"""
    if not data or len(data) <= visible_chars:
        return data
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]

class RateLimiter:
    """Simple rate limiter for bot operations"""
    
    def __init__(self):
        self.user_timestamps = {}
        self.global_timestamps = []
    
    def is_allowed(self, user_id: int, operation: str = "default", 
                   user_limit: int = 10, global_limit: int = 100, 
                   window_seconds: int = 60) -> bool:
        """
        Check if operation is allowed within rate limits
        """
        now = datetime.now().timestamp()
        window_start = now - window_seconds
        
        # Clean old timestamps
        self.global_timestamps = [ts for ts in self.global_timestamps if ts > window_start]
        
        if user_id not in self.user_timestamps:
            self.user_timestamps[user_id] = {}
        
        if operation not in self.user_timestamps[user_id]:
            self.user_timestamps[user_id][operation] = []
        
        # Clean old user timestamps
        self.user_timestamps[user_id][operation] = [
            ts for ts in self.user_timestamps[user_id][operation] if ts > window_start
        ]
        
        # Check limits
        user_count = len(self.user_timestamps[user_id][operation])
        global_count = len(self.global_timestamps)
        
        if user_count >= user_limit or global_count >= global_limit:
            return False
        
        # Record this operation
        self.user_timestamps[user_id][operation].append(now)
        self.global_timestamps.append(now)
        
        return True

# Global rate limiter instance
rate_limiter = RateLimiter()

def log_user_action(user_id: int, action: str, details: str = None):
    """Log user action for debugging and analytics"""
    log_message = f"User {user_id} performed action: {action}"
    if details:
        log_message += f" - {details}"
    
    logger.info(log_message)

def format_stock_status(stock_quantity: int) -> tuple[str, str]:
    """
    Format stock status with emoji and text
    Returns (emoji, status_text)
    """
    if stock_quantity == 0:
        return "🔴", "Out of Stock"
    elif stock_quantity < 5:
        return "🟡", f"Low Stock ({stock_quantity} left)"
    elif stock_quantity < 20:
        return "🟠", f"Limited Stock ({stock_quantity} available)"
    else:
        return "🟢", f"In Stock ({stock_quantity} available)"

def create_pagination_keyboard(items: List[Any], current_page: int = 0, 
                             items_per_page: int = 10, callback_prefix: str = "page") -> List[List]:
    """Create pagination keyboard for long lists"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    if total_pages <= 1:
        return []
    
    keyboard = []
    row = []
    
    # Previous page
    if current_page > 0:
        row.append(f"← Previous")
    
    # Page info
    row.append(f"Page {current_page + 1}/{total_pages}")
    
    # Next page
    if current_page < total_pages - 1:
        row.append(f"Next →")
    
    if row:
        keyboard.append(row)
    
    return keyboard

def format_analytics_summary(analytics_data: Dict) -> str:
    """Format analytics data for display"""
    try:
        text = f"""
📊 **Analytics Summary**

**Sales Performance:**
• Total Revenue: {format_currency(analytics_data.get('total_revenue', 0))}
• Total Orders: {analytics_data.get('total_orders', 0)}
• Average Order Value: {format_currency(analytics_data.get('avg_order_value', 0))}

**Product Metrics:**
• Total Products: {analytics_data.get('total_products', 0)}
• Low Stock Alerts: {analytics_data.get('low_stock_count', 0)}

**User Activity:**
• Total Users: {analytics_data.get('total_users', 0)}
• New Users Today: {analytics_data.get('new_users_today', 0)}

**Review System:**
• Total Reviews: {analytics_data.get('total_reviews', 0)}
• Average Rating: {analytics_data.get('avg_rating', 0)}/5.0
• Pending Reviews: {analytics_data.get('pending_reviews', 0)}
        """
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Error formatting analytics summary: {e}")
        return "❌ Error formatting analytics data"

def validate_admin_access(user_id: int) -> bool:
    """Validate if user has admin access"""
    return user_id == ADMIN_ID

def format_error_message(error: str, action: str = None) -> str:
    """Format error message for user display"""
    base_message = f"❌ **Error**\n\n{error}"
    
    if action:
        base_message += f"\n\n**Action:** {action}"
    
    base_message += "\n\nPlease try again or contact support if the problem persists."
    
    return base_message

def clean_input_text(text: str) -> str:
    """Clean and normalize input text"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove null bytes and control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    return text.strip()
