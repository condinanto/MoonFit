"""
Discount code management for MOON FIT Telegram Bot
"""
import logging
import random
import string
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from database import db
from utils import format_currency, calculate_discount

logger = logging.getLogger(__name__)

class DiscountManager:
    @staticmethod
    def generate_discount_code(discount_type: str, discount_value: float,
                              usage_limit: int = None, expires_in_days: int = None,
                              custom_code: str = None) -> Tuple[bool, str]:
        """Generate a new discount code"""
        try:
            # Validate discount type
            if discount_type not in ['percentage', 'fixed']:
                return False, "Invalid discount type. Must be 'percentage' or 'fixed'"
            
            # Validate discount value
            if discount_value <= 0:
                return False, "Discount value must be greater than 0"
            
            if discount_type == 'percentage' and discount_value > 100:
                return False, "Percentage discount cannot exceed 100%"
            
            if discount_type == 'fixed' and discount_value > 1000:
                return False, "Fixed discount cannot exceed $1000"
            
            # Generate or validate code
            if custom_code:
                code = custom_code.upper().strip()
                if not code.replace('_', '').replace('-', '').isalnum():
                    return False, "Code can only contain letters, numbers, hyphens, and underscores"
                if len(code) < 3 or len(code) > 20:
                    return False, "Code must be 3-20 characters long"
                
                # Check if code already exists
                existing = db.get_discount_code(code)
                if existing:
                    return False, "Code already exists"
            else:
                # Generate random code
                code = DiscountManager._generate_random_code()
                
                # Ensure uniqueness
                attempts = 0
                while db.get_discount_code(code) and attempts < 10:
                    code = DiscountManager._generate_random_code()
                    attempts += 1
                
                if attempts >= 10:
                    return False, "Failed to generate unique code. Please try again."
            
            # Calculate expiry date
            expires_at = None
            if expires_in_days:
                expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()
            
            # Add to database
            discount_id = db.add_discount_code(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                usage_limit=usage_limit,
                expires_at=expires_at
            )
            
            if discount_id:
                logger.info(f"Discount code created: {code} ({discount_type}: {discount_value})")
                
                # Format success message
                if discount_type == 'percentage':
                    value_text = f"{discount_value}%"
                else:
                    value_text = format_currency(discount_value)
                
                expiry_text = f" (expires in {expires_in_days} days)" if expires_in_days else ""
                limit_text = f" (limit {usage_limit} uses)" if usage_limit else ""
                
                return True, f"Discount code '{code}' created! {value_text} off{expiry_text}{limit_text}"
            else:
                return False, "Failed to create discount code"
                
        except Exception as e:
            logger.error(f"Error generating discount code: {e}")
            return False, "An error occurred while creating the discount code"
    
    @staticmethod
    def _generate_random_code(length: int = 8) -> str:
        """Generate random alphanumeric code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    @staticmethod
    def validate_discount_code(code: str, total_amount: float) -> Tuple[bool, str, float]:
        """
        Validate discount code and calculate discount amount
        Returns (is_valid, message, discount_amount)
        """
        try:
            if not code or not code.strip():
                return False, "Please enter a discount code", 0.0
            
            code = code.upper().strip()
            discount = db.get_discount_code(code)
            
            if not discount:
                return False, "Invalid discount code", 0.0
            
            # Check if active
            if not discount['active']:
                return False, "Discount code is no longer active", 0.0
            
            # Check expiry
            if discount['expires_at']:
                expiry_date = datetime.fromisoformat(discount['expires_at'])
                if datetime.now() > expiry_date:
                    return False, "Discount code has expired", 0.0
            
            # Check usage limit
            if discount['usage_limit'] and discount['used_count'] >= discount['usage_limit']:
                return False, "Discount code has reached its usage limit", 0.0
            
            # Calculate discount amount
            discount_amount = calculate_discount(
                total_amount, 
                discount['discount_type'], 
                discount['discount_value']
            )
            
            if discount_amount == 0:
                return False, "Discount code cannot be applied to this order", 0.0
            
            return True, f"Discount applied: {format_currency(discount_amount)} off!", discount_amount
            
        except Exception as e:
            logger.error(f"Error validating discount code: {e}")
            return False, "Error validating discount code", 0.0
    
    @staticmethod
    def apply_discount_code(code: str) -> Tuple[bool, str]:
        """Mark discount code as used"""
        try:
            code = code.upper().strip()
            success = db.use_discount_code(code)
            
            if success:
                logger.info(f"Discount code used: {code}")
                return True, "Discount code applied successfully"
            else:
                return False, "Failed to apply discount code"
                
        except Exception as e:
            logger.error(f"Error applying discount code: {e}")
            return False, "An error occurred while applying the discount"
    
    @staticmethod
    def get_all_discounts() -> List[Dict]:
        """Get all discount codes"""
        try:
            return db.get_all_discount_codes()
        except Exception as e:
            logger.error(f"Error getting discount codes: {e}")
            return []
    
    @staticmethod
    def deactivate_discount(code: str) -> Tuple[bool, str]:
        """Deactivate a discount code"""
        try:
            code = code.upper().strip()
            discount = db.get_discount_code(code)
            
            if not discount:
                return False, "Discount code not found"
            
            if not discount['active']:
                return False, "Discount code is already inactive"
            
            success = db.deactivate_discount_code(code)
            
            if success:
                logger.info(f"Discount code deactivated: {code}")
                return True, f"Discount code '{code}' has been deactivated"
            else:
                return False, "Failed to deactivate discount code"
                
        except Exception as e:
            logger.error(f"Error deactivating discount code: {e}")
            return False, "An error occurred while deactivating the discount"
    
    @staticmethod
    def get_discount_statistics() -> Dict:
        """Get discount usage statistics"""
        try:
            discounts = db.get_all_discount_codes()
            
            total_codes = len(discounts)
            active_codes = sum(1 for d in discounts if d['active'])
            expired_codes = 0
            total_uses = sum(d['used_count'] for d in discounts)
            
            # Check for expired codes
            now = datetime.now()
            for discount in discounts:
                if discount['expires_at']:
                    try:
                        expiry_date = datetime.fromisoformat(discount['expires_at'])
                        if now > expiry_date:
                            expired_codes += 1
                    except:
                        pass
            
            # Most used code
            most_used = max(discounts, key=lambda x: x['used_count']) if discounts else None
            
            return {
                'total_codes': total_codes,
                'active_codes': active_codes,
                'expired_codes': expired_codes,
                'total_uses': total_uses,
                'most_used_code': most_used['code'] if most_used else "N/A",
                'most_used_count': most_used['used_count'] if most_used else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting discount statistics: {e}")
            return {
                'total_codes': 0,
                'active_codes': 0,
                'expired_codes': 0,
                'total_uses': 0,
                'most_used_code': "N/A",
                'most_used_count': 0
            }
    
    @staticmethod
    def format_discount_list(discounts: List[Dict]) -> str:
        """Format discount codes for display"""
        if not discounts:
            return "No discount codes available."
        
        text = "🎁 **Available Discount Codes:**\n\n"
        
        for discount in discounts:
            if not discount['active']:
                continue
                
            # Check if expired
            if discount['expires_at']:
                try:
                    expiry_date = datetime.fromisoformat(discount['expires_at'])
                    if datetime.now() > expiry_date:
                        continue
                except:
                    pass
            
            # Format discount value
            if discount['discount_type'] == 'percentage':
                value_text = f"{discount['discount_value']}% off"
            else:
                value_text = f"{format_currency(discount['discount_value'])} off"
            
            # Format usage info
            if discount['usage_limit']:
                usage_text = f"({discount['used_count']}/{discount['usage_limit']} used)"
            else:
                usage_text = f"({discount['used_count']} used)"
            
            # Format expiry
            if discount['expires_at']:
                try:
                    expiry_date = datetime.fromisoformat(discount['expires_at'])
                    expiry_text = f" - Expires: {expiry_date.strftime('%Y-%m-%d')}"
                except:
                    expiry_text = ""
            else:
                expiry_text = ""
            
            text += f"**{discount['code']}** - {value_text} {usage_text}{expiry_text}\n"
        
        return text
    
    @staticmethod
    def create_bulk_codes(prefix: str, count: int, discount_type: str, 
                         discount_value: float, usage_limit: int = 1,
                         expires_in_days: int = None) -> Tuple[bool, str, List[str]]:
        """Create multiple discount codes with same parameters"""
        try:
            if count <= 0 or count > 100:
                return False, "Count must be between 1 and 100", []
            
            created_codes = []
            failed_codes = []
            
            for i in range(count):
                code = f"{prefix.upper()}{i+1:03d}"  # e.g., SALE001, SALE002
                
                success, message = DiscountManager.generate_discount_code(
                    discount_type=discount_type,
                    discount_value=discount_value,
                    usage_limit=usage_limit,
                    expires_in_days=expires_in_days,
                    custom_code=code
                )
                
                if success:
                    created_codes.append(code)
                else:
                    failed_codes.append(f"{code}: {message}")
            
            if created_codes:
                logger.info(f"Bulk codes created: {len(created_codes)} codes with prefix {prefix}")
                
                result_message = f"Created {len(created_codes)} discount codes successfully!"
                if failed_codes:
                    result_message += f"\n{len(failed_codes)} codes failed to create."
                
                return True, result_message, created_codes
            else:
                return False, "No codes were created", []
                
        except Exception as e:
            logger.error(f"Error creating bulk codes: {e}")
            return False, "An error occurred while creating bulk codes", []
