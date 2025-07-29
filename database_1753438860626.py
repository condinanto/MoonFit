"""
Database management for MOON FIT Telegram Bot
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    cart_data TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('tshirt', 'hoodie', 'hat')),
                    price REAL NOT NULL,
                    description TEXT,
                    image_url TEXT,
                    stock_quantity INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    products TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    discount_code TEXT,
                    discount_amount REAL DEFAULT 0,
                    final_amount REAL NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
                    payment_hash TEXT,
                    ton_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Reviews table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    order_id INTEGER,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Discount codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discount_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_type TEXT CHECK (discount_type IN ('percentage', 'fixed')) NOT NULL,
                    discount_value REAL NOT NULL,
                    usage_limit INTEGER DEFAULT NULL,
                    used_count INTEGER DEFAULT 0,
                    expiry_date TIMESTAMP,
                    active BOOLEAN DEFAULT TRUE,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
                )
            ''')
            
            # Discount usage tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discount_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    order_id INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (code_id) REFERENCES discount_codes (id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Admin logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users (user_id)
                )
            ''')
            
            # User sessions table for conversation state
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    user_id INTEGER PRIMARY KEY,
                    state TEXT,
                    data TEXT DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    # User management methods
    def create_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None, last_name: Optional[str] = None):
        """Create a new user or update existing user info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_cart(self, user_id: int) -> List[Dict]:
        """Get user's shopping cart"""
        user = self.get_user(user_id)
        if user and user['cart_data']:
            try:
                return json.loads(user['cart_data'])
            except json.JSONDecodeError:
                return []
        return []
    
    def update_user_cart(self, user_id: int, cart_data: List[Dict]):
        """Update user's shopping cart"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET cart_data = ? WHERE user_id = ?
            ''', (json.dumps(cart_data), user_id))
            conn.commit()
    
    def clear_user_cart(self, user_id: int):
        """Clear user's shopping cart"""
        self.update_user_cart(user_id, [])
    
    # Product management methods
    def add_product(self, name: str, product_type: str, price: float, description: Optional[str] = None, 
                   image_url: Optional[str] = None, stock_quantity: int = 0) -> int:
        """Add a new product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, type, price, description, image_url, stock_quantity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, product_type, price, description, image_url, stock_quantity))
            conn.commit()
            return cursor.lastrowid
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE id = ? AND active = TRUE', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_products_by_type(self, product_type: str) -> List[Dict]:
        """Get all active products by type"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM products WHERE type = ? AND active = TRUE 
                ORDER BY created_at DESC
            ''', (product_type,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_products(self, include_inactive: bool = False) -> List[Dict]:
        """Get all products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
            else:
                cursor.execute('SELECT * FROM products WHERE active = TRUE ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_product(self, product_id: int, **kwargs):
        """Update product information"""
        if not kwargs:
            return
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [product_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', values)
            conn.commit()
    
    def delete_product(self, product_id: int):
        """Soft delete a product by setting active to FALSE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE products SET active = FALSE WHERE id = ?', (product_id,))
            conn.commit()
    
    def update_stock(self, product_id: int, quantity_change: int):
        """Update product stock quantity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE products SET stock_quantity = stock_quantity + ? 
                WHERE id = ?
            ''', (quantity_change, product_id))
            conn.commit()
    
    # Order management methods
    def create_order(self, user_id: int, products: List[Dict], total_amount: float,
                    discount_code: Optional[str] = None, discount_amount: float = 0,
                    final_amount: Optional[float] = None) -> int:
        """Create a new order"""
        if final_amount is None:
            final_amount = total_amount - discount_amount
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders (user_id, products, total_amount, discount_code, 
                                  discount_amount, final_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, json.dumps(products), total_amount, discount_code, 
                  discount_amount, final_amount))
            conn.commit()
            return cursor.lastrowid
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Get order by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            row = cursor.fetchone()
            if row:
                order = dict(row)
                order['products'] = json.loads(order['products'])
                return order
            return None
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Get all orders for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                order['products'] = json.loads(order['products'])
                orders.append(order)
            return orders
    
    def update_order_status(self, order_id: int, status: str, payment_hash: str = None):
        """Update order status and payment information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if payment_hash:
                cursor.execute('''
                    UPDATE orders SET status = ?, payment_hash = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, payment_hash, order_id))
            else:
                cursor.execute('''
                    UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, order_id))
            conn.commit()
    
    def get_pending_orders(self) -> List[Dict]:
        """Get all pending orders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM orders WHERE status = 'pending' 
                ORDER BY created_at DESC
            ''')
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                order['products'] = json.loads(order['products'])
                orders.append(order)
            return orders
    
    # Discount code methods
    def create_discount_code(self, code: str, discount_type: str, discount_value: float,
                           usage_limit: int = None, expiry_date: str = None, 
                           created_by: int = None) -> bool:
        """Create a new discount code"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO discount_codes (code, discount_type, discount_value, 
                                              usage_limit, expiry_date, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (code, discount_type, discount_value, usage_limit, expiry_date, created_by))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Code already exists
    
    def get_discount_code(self, code: str) -> Optional[Dict]:
        """Get discount code by code string"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM discount_codes WHERE code = ? AND active = TRUE
            ''', (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def validate_discount_code(self, code: str, user_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """Validate if discount code can be used"""
        discount = self.get_discount_code(code)
        
        if not discount:
            return False, "Discount code not found or inactive", None
        
        # Check expiry date
        if discount['expiry_date']:
            expiry = datetime.fromisoformat(discount['expiry_date'])
            if datetime.now() > expiry:
                return False, "Discount code has expired", None
        
        # Check usage limit
        if discount['usage_limit'] and discount['used_count'] >= discount['usage_limit']:
            return False, "Discount code usage limit reached", None
        
        # Check if user already used this code
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM discount_usage WHERE code_id = ? AND user_id = ?
            ''', (discount['id'], user_id))
            if cursor.fetchone()[0] > 0:
                return False, "You have already used this discount code", None
        
        return True, "Valid discount code", discount
    
    def use_discount_code(self, code_id: int, user_id: int, order_id: int):
        """Record discount code usage and increment used count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Record usage
            cursor.execute('''
                INSERT INTO discount_usage (code_id, user_id, order_id)
                VALUES (?, ?, ?)
            ''', (code_id, user_id, order_id))
            
            # Increment used count
            cursor.execute('''
                UPDATE discount_codes SET used_count = used_count + 1
                WHERE id = ?
            ''', (code_id,))
            conn.commit()
    
    def get_all_discount_codes(self) -> List[Dict]:
        """Get all discount codes for admin"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT dc.*, u.username as created_by_username 
                FROM discount_codes dc
                LEFT JOIN users u ON dc.created_by = u.user_id
                ORDER BY dc.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def toggle_discount_code(self, code_id: int) -> bool:
        """Toggle discount code active status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE discount_codes SET active = NOT active WHERE id = ?
            ''', (code_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # Review methods
    def add_review(self, user_id: int, product_id: int, rating: int, 
                  comment: str = None, order_id: int = None) -> int:
        """Add a product review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reviews (user_id, product_id, rating, comment, order_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, product_id, rating, comment, order_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_product_reviews(self, product_id: int, approved_only: bool = True) -> List[Dict]:
        """Get reviews for a specific product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if approved_only:
                cursor.execute('''
                    SELECT r.*, u.username, u.first_name 
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.product_id = ? AND r.approved = TRUE
                    ORDER BY r.created_at DESC
                ''', (product_id,))
            else:
                cursor.execute('''
                    SELECT r.*, u.username, u.first_name 
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    WHERE r.product_id = ?
                    ORDER BY r.created_at DESC
                ''', (product_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get all pending reviews for admin approval"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, u.username, u.first_name, p.name as product_name
                FROM reviews r
                JOIN users u ON r.user_id = u.user_id
                JOIN products p ON r.product_id = p.id
                WHERE r.approved = FALSE
                ORDER BY r.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def approve_review(self, review_id: int) -> bool:
        """Approve a review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reviews SET approved = TRUE WHERE id = ?', (review_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_review(self, review_id: int) -> bool:
        """Delete a review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # User session methods for conversation state
    def set_user_state(self, user_id: int, state: str, data: Dict = None):
        """Set user conversation state"""
        if data is None:
            data = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_sessions (user_id, state, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, state, json.dumps(data)))
            conn.commit()
    
    def get_user_state(self, user_id: int) -> Tuple[Optional[str], Dict]:
        """Get user conversation state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT state, data FROM user_sessions WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row['data']) if row['data'] else {}
                except json.JSONDecodeError:
                    data = {}
                return row['state'], data
            return None, {}
    
    def clear_user_state(self, user_id: int):
        """Clear user conversation state"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # Admin logs
    def log_admin_action(self, admin_id: int, action: str, details: str = None):
        """Log admin action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action, details)
                VALUES (?, ?, ?)
            ''', (admin_id, action, details))
            conn.commit()
    
    def get_admin_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent admin logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.*, u.username 
                FROM admin_logs al
                JOIN users u ON al.admin_id = u.user_id
                ORDER BY al.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Analytics methods
    def get_sales_stats(self) -> Dict:
        """Get sales statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total sales
            cursor.execute('''
                SELECT COUNT(*) as total_orders, 
                       COALESCE(SUM(final_amount), 0) as total_revenue
                FROM orders WHERE status != 'cancelled'
            ''')
            stats = dict(cursor.fetchone())
            
            # Sales by product type
            cursor.execute('''
                SELECT p.type, COUNT(*) as orders, COALESCE(SUM(o.final_amount), 0) as revenue
                FROM orders o
                JOIN (
                    SELECT DISTINCT order_id, product_id
                    FROM (
                        SELECT id as order_id, json_extract(value, '$.product_id') as product_id
                        FROM orders, json_each(products)
                        WHERE status != 'cancelled'
                    )
                ) op ON o.id = op.order_id
                JOIN products p ON op.product_id = p.id
                GROUP BY p.type
            ''')
            stats['by_type'] = [dict(row) for row in cursor.fetchall()]
            
            # Discount usage stats
            cursor.execute('''
                SELECT COUNT(*) as discount_orders,
                       COALESCE(SUM(discount_amount), 0) as total_discounts
                FROM orders WHERE discount_code IS NOT NULL AND status != 'cancelled'
            ''')
            discount_stats = dict(cursor.fetchone())
            stats.update(discount_stats)
            
            return stats

# Global database instance
db = Database()
