"""
Database management for MOON FIT Telegram Bot
SQLite database with custom ORM-like wrapper
"""
import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from contextlib import contextmanager
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Products table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('tshirt', 'hoodie', 'hat')),
                    price REAL NOT NULL CHECK (price > 0),
                    stock_quantity INTEGER NOT NULL DEFAULT 0,
                    description TEXT,
                    image_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Shopping carts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS carts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    cart_data TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    order_data TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    discount_code TEXT,
                    discount_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
                    payment_hash TEXT,
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
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (order_id) REFERENCES orders (id),
                    UNIQUE(user_id, product_id)
                )
            ''')
            
            # Discount codes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS discount_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_type TEXT NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
                    discount_value REAL NOT NULL CHECK (discount_value > 0),
                    usage_limit INTEGER,
                    used_count INTEGER DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Admin logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_type ON products (type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reviews_approved ON reviews (approved)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_discount_codes_code ON discount_codes (code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp ON admin_logs (timestamp)')
            
            logger.info("Database initialized successfully")
    
    # User management methods
    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        """Add or update user in database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_active)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, username, first_name, last_name))
            return cursor.lastrowid
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by user_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            return cursor.fetchone()[0]
    
    # Product management methods
    def add_product(self, name: str, product_type: str, price: float, 
                   stock_quantity: int, description: str = None, image_url: str = None) -> int:
        """Add new product to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, type, price, stock_quantity, description, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, product_type, price, stock_quantity, description, image_url))
            return cursor.lastrowid
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_products_by_type(self, product_type: str) -> List[Dict]:
        """Get all products of specific type"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM products WHERE type = ? ORDER BY name',
                (product_type,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products ORDER BY type, name')
            return [dict(row) for row in cursor.fetchall()]
    
    def update_product_stock(self, product_id: int, new_stock: int) -> bool:
        """Update product stock quantity"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE products SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_stock, product_id)
            )
            return cursor.rowcount > 0
    
    def delete_product(self, product_id: int) -> bool:
        """Delete product from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
            return cursor.rowcount > 0
    
    def get_product_count(self) -> int:
        """Get total number of products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM products')
            return cursor.fetchone()[0]
    
    def get_low_stock_products(self, threshold: int = 5) -> List[Dict]:
        """Get products with low stock"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM products WHERE stock_quantity <= ? ORDER BY stock_quantity ASC',
                (threshold,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # Cart management methods
    def get_cart(self, user_id: int) -> Dict:
        """Get user's cart data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT cart_data FROM carts WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return {}
            return {}
    
    def update_cart(self, user_id: int, cart_data: Dict) -> bool:
        """Update user's cart data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cart_json = json.dumps(cart_data)
            cursor.execute('''
                INSERT OR REPLACE INTO carts (user_id, cart_data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, cart_json))
            return cursor.rowcount > 0
    
    def clear_cart(self, user_id: int) -> bool:
        """Clear user's cart"""
        return self.update_cart(user_id, {})
    
    # Order management methods
    def create_order(self, user_id: int, order_data: List[Dict], total_amount: float,
                    discount_code: str = None, discount_amount: float = 0) -> int:
        """Create new order"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            order_json = json.dumps(order_data)
            cursor.execute('''
                INSERT INTO orders (user_id, order_data, total_amount, discount_code, discount_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, order_json, total_amount, discount_code, discount_amount))
            return cursor.lastrowid
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Get order by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            row = cursor.fetchone()
            if row:
                order = dict(row)
                try:
                    order['order_data'] = json.loads(order['order_data'])
                except json.JSONDecodeError:
                    order['order_data'] = []
                return order
            return None
    
    def update_order_status(self, order_id: int, status: str, payment_hash: str = None) -> bool:
        """Update order status"""
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
            return cursor.rowcount > 0
    
    def get_orders_by_user(self, user_id: int) -> List[Dict]:
        """Get all orders for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                try:
                    order['order_data'] = json.loads(order['order_data'])
                except json.JSONDecodeError:
                    order['order_data'] = []
                orders.append(order)
            return orders
    
    def get_all_orders(self) -> List[Dict]:
        """Get all orders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                try:
                    order['order_data'] = json.loads(order['order_data'])
                except json.JSONDecodeError:
                    order['order_data'] = []
                orders.append(order)
            return orders
    
    def get_order_count(self) -> int:
        """Get total number of orders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM orders')
            return cursor.fetchone()[0]
    
    def get_total_revenue(self) -> float:
        """Get total revenue from paid orders"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT SUM(total_amount - discount_amount) FROM orders WHERE status = ?',
                ('paid',)
            )
            result = cursor.fetchone()[0]
            return result if result else 0.0
    
    # Review management methods
    def add_review(self, user_id: int, product_id: int, rating: int,
                  comment: str = None, order_id: int = None) -> int:
        """Add product review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reviews (user_id, product_id, rating, comment, order_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, product_id, rating, comment, order_id))
            return cursor.lastrowid
    
    def get_product_reviews(self, product_id: int, approved_only: bool = True) -> List[Dict]:
        """Get reviews for a product"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if approved_only:
                query = '''
                    SELECT r.*, u.username, u.first_name, u.last_name, p.name as product_name
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    JOIN products p ON r.product_id = p.id
                    WHERE r.product_id = ? AND r.approved = TRUE
                    ORDER BY r.created_at DESC
                '''
            else:
                query = '''
                    SELECT r.*, u.username, u.first_name, u.last_name, p.name as product_name
                    FROM reviews r
                    JOIN users u ON r.user_id = u.user_id
                    JOIN products p ON r.product_id = p.id
                    WHERE r.product_id = ?
                    ORDER BY r.created_at DESC
                '''
            cursor.execute(query, (product_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get reviews pending approval"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, u.username, u.first_name, u.last_name, p.name as product_name
                FROM reviews r
                JOIN users u ON r.user_id = u.user_id
                JOIN products p ON r.product_id = p.id
                WHERE r.approved = FALSE
                ORDER BY r.created_at ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def approve_review(self, review_id: int) -> bool:
        """Approve a review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE reviews SET approved = TRUE WHERE id = ?', (review_id,))
            return cursor.rowcount > 0
    
    def delete_review(self, review_id: int) -> bool:
        """Delete a review"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
            return cursor.rowcount > 0
    
    def get_review_count(self) -> int:
        """Get total number of reviews"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reviews')
            return cursor.fetchone()[0]
    
    def get_pending_review_count(self) -> int:
        """Get number of pending reviews"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reviews WHERE approved = FALSE')
            return cursor.fetchone()[0]
    
    def get_user_reviews(self, user_id: int) -> List[Dict]:
        """Get all reviews by a specific user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, p.name as product_name, p.type as product_type
                FROM reviews r
                JOIN products p ON r.product_id = p.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Discount code management methods
    def add_discount_code(self, code: str, discount_type: str, discount_value: float,
                         usage_limit: int = None, expires_at: str = None) -> int:
        """Add discount code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO discount_codes (code, discount_type, discount_value, usage_limit, expires_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (code, discount_type, discount_value, usage_limit, expires_at))
            return cursor.lastrowid
    
    def get_discount_code(self, code: str) -> Optional[Dict]:
        """Get discount code by code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM discount_codes WHERE code = ?', (code,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_discount_codes(self) -> List[Dict]:
        """Get all discount codes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM discount_codes ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def use_discount_code(self, code: str) -> bool:
        """Increment usage count for discount code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE discount_codes SET used_count = used_count + 1 WHERE code = ?',
                (code,)
            )
            return cursor.rowcount > 0
    
    def deactivate_discount_code(self, code: str) -> bool:
        """Deactivate discount code"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE discount_codes SET active = FALSE WHERE code = ?', (code,))
            return cursor.rowcount > 0
    
    # Admin log methods
    def log_admin_action(self, admin_id: int, action: str, details: str = None):
        """Log admin action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_logs (admin_id, action, details)
                VALUES (?, ?, ?)
            ''', (admin_id, action, details))
    
    def get_admin_logs(self, limit: int = 50) -> List[Dict]:
        """Get admin logs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM admin_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # Analytics methods
    def get_analytics_data(self) -> Dict:
        """Get comprehensive analytics data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute('SELECT COUNT(*) FROM products')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM orders')
            total_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM reviews')
            total_reviews = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM reviews WHERE approved = FALSE')
            pending_reviews = cursor.fetchone()[0]
            
            # Revenue
            cursor.execute('SELECT SUM(total_amount - discount_amount) FROM orders WHERE status = ?', ('paid',))
            revenue_result = cursor.fetchone()[0]
            total_revenue = revenue_result if revenue_result else 0.0
            
            # Average order value
            cursor.execute('SELECT AVG(total_amount - discount_amount) FROM orders WHERE status = ?', ('paid',))
            avg_result = cursor.fetchone()[0]
            avg_order_value = avg_result if avg_result else 0.0
            
            # Average rating
            cursor.execute('SELECT AVG(rating) FROM reviews WHERE approved = TRUE')
            rating_result = cursor.fetchone()[0]
            avg_rating = rating_result if rating_result else 0.0
            
            # Most popular product (simplified - just get first product for now)
            cursor.execute('SELECT name FROM products LIMIT 1')
            popular_result = cursor.fetchone()
            most_popular = popular_result[0] if popular_result else "N/A"
            
            # Low stock count
            cursor.execute('SELECT COUNT(*) FROM products WHERE stock_quantity <= 5')
            low_stock_count = cursor.fetchone()[0]
            
            # New users today
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) = DATE('now')
            ''')
            new_users_today = cursor.fetchone()[0]
            
            return {
                'total_products': total_products,
                'total_orders': total_orders,
                'total_users': total_users,
                'total_reviews': total_reviews,
                'pending_reviews': pending_reviews,
                'total_revenue': total_revenue,
                'avg_order_value': avg_order_value,
                'avg_rating': round(avg_rating, 1),
                'most_popular_product': most_popular,
                'low_stock_count': low_stock_count,
                'new_users_today': new_users_today
            }

# Global database instance
db = Database()
