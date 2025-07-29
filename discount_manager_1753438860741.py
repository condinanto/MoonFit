"""
Discount code management for MOON FIT Telegram Bot
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import db
from config import CURRENCY

logger = logging.getLogger(__name__)

class DiscountManager:
    @staticmethod
    def create_discount_code(code: str, discount_type: str, discount_value: float,
                           usage_limit: Optional[int] = None, expiry_days: Optional[int] = None,
                           created_by: int = None) -> Tuple[bool, str]:
        """Create a new discount code"""
        try:
            # Validate code format
            if not DiscountManager.validate_code_format(code):
                return False, "Code must be 3-20 characters, alphanumeric only"
            
            # Validate discount type and value
            if discount_type not in ['percentage', 'fixed']:
                return False, "Discount type must be 'percentage' or 'fixed'"
            
            if discount_type == 'percentage':
                if discount_value <= 0 or discount_value > 100:
                    return False, "Percentage discount must be between 0-100%"
            else:  # fixed
                if discount_value <= 0:
                    return False, "Fixed discount must be greater than 0"
            
            # Calculate expiry date
            expiry_date = None
            if expiry_days:
                expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
            
            # Create discount code
            success = db.create_discount_code(
                code=code.upper(),
                discount_type=discount_type,
                discount_value=discount_value,
                usage_limit=usage_limit,
                expiry_date=expiry_date,
                created_by=created_by
            )
            
            if success:
                logger.info(f"Created discount code: {code} by user {created_by}")
                return True, f"Discount code '{code}' created successfully!"
            else:
                return False, "Discount code already exists"
                
        except Exception as e:
            logger.error(f"Error creating discount code: {e}")
            return False, "Failed to create discount code"
    
    @staticmethod
    def validate_code_format(code: str) -> bool:
        """Validate discount code format"""
        if not code or len(code) < 3 or len(code) > 20:
            return False
        
        # Only alphanumeric characters allowed
        return re.match(r'^[A-Z0-9]+$', code.upper()) is not None
    
    @staticmethod
    def apply_discount(code: str, user_id: int, total_amount: float) -> Tuple[bool, str, float]:
        """
        Apply discount code to order
        Returns (success, message, discount_amount)
        """
        try:
            # Validate discount code
            is_valid, message, discount = db.validate_discount_code(code.upper(), user_id)
            
            if not is_valid:
                return False, message, 0.0
            
            # Calculate discount amount
            if discount['discount_type'] == 'percentage':
                discount_amount = total_amount * (discount['discount_value'] / 100)
            else:  # fixed
                discount_amount = min(discount['discount_value'], total_amount)
            
            # Ensure discount doesn't exceed total
            discount_amount = min(discount_amount, total_amount)
            
            success_message = f"Applied {DiscountManager.format_discount(discount)} - Save {discount_amount:.3f} {CURRENCY}!"
            return True, success_message, discount_amount
            
        except Exception as e:
            logger.error(f"Error applying discount: {e}")
            return False, "Error applying discount code", 0.0
    
    @staticmethod
    def format_discount(discount: Dict) -> str:
        """Format discount for display"""
        if discount['discount_type'] == 'percentage':
            return f"{discount['discount_value']:.0f}% OFF"
        else:
            return f"{discount['discount_value']:.3f} {CURRENCY} OFF"
    
    @staticmethod
    def get_discount_info(code: str) -> Optional[Dict]:
        """Get discount code information"""
        try:
            return db.get_discount_code(code.upper())
        except Exception as e:
            logger.error(f"Error getting discount info: {e}")
            return None
    
    @staticmethod
    def get_all_discount_codes() -> List[Dict]:
        """Get all discount codes for admin view"""
        try:
            return db.get_all_discount_codes()
        except Exception as e:
            logger.error(f"Error getting all discount codes: {e}")
            return []
    
    @staticmethod
    def toggle_discount_code(code_id: int) -> Tuple[bool, str]:
        """Toggle discount code active status"""
        try:
            success = db.toggle_discount_code(code_id)
            if success:
                return True, "Discount code status updated"
            else:
                return False, "Discount code not found"
        except Exception as e:
            logger.error(f"Error toggling discount code: {e}")
            return False, "Failed to update discount code"
    
    @staticmethod
    def get_discount_usage_stats(code_id: Optional[int] = None) -> Dict:
        """Get discount usage statistics"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                if code_id:
                    # Get stats for specific discount code
                    cursor.execute('''
                        SELECT dc.*, 
                               COUNT(du.id) as actual_usage,
                               COALESCE(SUM(o.discount_amount), 0) as total_discount_given
                        FROM discount_codes dc
                        LEFT JOIN discount_usage du ON dc.id = du.code_id
                        LEFT JOIN orders o ON du.order_id = o.id
                        WHERE dc.id = ?
                        GROUP BY dc.id
                    ''', (code_id,))
                    
                    row = cursor.fetchone()
                    return dict(row) if row else {}
                else:
                    # Get overall stats
                    cursor.execute('''
                        SELECT 
                            COUNT(DISTINCT dc.id) as total_codes,
                            COUNT(DISTINCT CASE WHEN dc.active THEN dc.id END) as active_codes,
                            COUNT(du.id) as total_usage,
                            COALESCE(SUM(o.discount_amount), 0) as total_discount_given,
                            COUNT(DISTINCT du.user_id) as unique_users
                        FROM discount_codes dc
                        LEFT JOIN discount_usage du ON dc.id = du.code_id
                        LEFT JOIN orders o ON du.order_id = o.id
                    ''')
                    
                    row = cursor.fetchone()
                    return dict(row) if row else {}
                    
        except Exception as e:
            logger.error(f"Error getting discount usage stats: {e}")
            return {}
    
    @staticmethod
    def get_top_discount_codes(limit: int = 10) -> List[Dict]:
        """Get most used discount codes"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT dc.code, dc.discount_type, dc.discount_value,
                           COUNT(du.id) as usage_count,
                           COALESCE(SUM(o.discount_amount), 0) as total_discount_given
                    FROM discount_codes dc
                    LEFT JOIN discount_usage du ON dc.id = du.code_id
                    LEFT JOIN orders o ON du.order_id = o.id
                    GROUP BY dc.id
                    ORDER BY usage_count DESC
                    LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting top discount codes: {e}")
            return []
    
    @staticmethod
    def cleanup_expired_codes() -> int:
        """Deactivate expired discount codes"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE discount_codes 
                    SET active = FALSE 
                    WHERE expiry_date IS NOT NULL 
                    AND datetime(expiry_date) < datetime('now')
                    AND active = TRUE
                ''')
                conn.commit()
                
                expired_count = cursor.rowcount
                if expired_count > 0:
                    logger.info(f"Deactivated {expired_count} expired discount codes")
                
                return expired_count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired codes: {e}")
            return 0
    
    @staticmethod
    def format_discount_list(discounts: List[Dict]) -> str:
        """Format discount codes list for display"""
        if not discounts:
            return "No discount codes found."
        
        text = "🎫 **Discount Codes**\n\n"
        
        for discount in discounts:
            status = "✅ Active" if discount['active'] else "❌ Inactive"
            discount_text = DiscountManager.format_discount(discount)
            
            expiry = "No expiry"
            if discount['expiry_date']:
                expiry_date = datetime.fromisoformat(discount['expiry_date'])
                if expiry_date < datetime.now():
                    expiry = "❌ Expired"
                else:
                    expiry = f"📅 Expires: {expiry_date.strftime('%Y-%m-%d')}"
            
            usage = f"{discount['used_count']}/{discount['usage_limit'] or '∞'}"
            
            text += f"**{discount['code']}** - {discount_text}\n"
            text += f"   Status: {status}\n"
            text += f"   Usage: {usage}\n"
            text += f"   {expiry}\n\n"
        
        return text
    
    @staticmethod
    def check_code_availability(code: str) -> bool:
        """Check if discount code is available for creation"""
        existing = db.get_discount_code(code.upper())
        return existing is None
    
    @staticmethod
    def get_user_discount_history(user_id: int) -> List[Dict]:
        """Get user's discount usage history"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT dc.code, dc.discount_type, dc.discount_value,
                           o.discount_amount, du.used_at, o.id as order_id
                    FROM discount_usage du
                    JOIN discount_codes dc ON du.code_id = dc.id
                    JOIN orders o ON du.order_id = o.id
                    WHERE du.user_id = ?
                    ORDER BY du.used_at DESC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting user discount history: {e}")
            return []

# Global discount manager instance
discount_manager = DiscountManager()
