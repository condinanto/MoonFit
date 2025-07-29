"""
Admin panel functionality for MOON FIT Telegram Bot
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import db
from product_manager import ProductManager
from discount_manager import DiscountManager
from review_manager import ReviewManager
from utils import format_currency, format_datetime

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.product_manager = ProductManager()
        self.discount_manager = DiscountManager()
        self.review_manager = ReviewManager()
    
    def get_dashboard_stats(self) -> Dict:
        """Get main dashboard statistics"""
        try:
            analytics = db.get_analytics_data()
            
            return {
                'total_products': analytics['total_products'],
                'total_orders': analytics['total_orders'],
                'total_users': analytics['total_users'],
                'total_revenue': analytics['total_revenue'],
                'pending_reviews': analytics['pending_reviews']
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                'total_products': 0,
                'total_orders': 0,
                'total_users': 0,
                'total_revenue': 0.0,
                'pending_reviews': 0
            }
    
    def get_analytics_data(self) -> Dict:
        """Get comprehensive analytics data"""
        try:
            analytics = db.get_analytics_data()
            
            # Add formatted recent activity
            recent_logs = db.get_admin_logs(10)
            recent_activity = ""
            
            if recent_logs:
                for log in recent_logs[:5]:
                    timestamp = format_datetime(log['timestamp'], 'short')
                    recent_activity += f"• {timestamp} - {log['action']}\n"
            else:
                recent_activity = "• No recent activity"
            
            analytics['recent_activity'] = recent_activity
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {
                'total_revenue': 0.0,
                'total_orders': 0,
                'avg_order_value': 0.0,
                'total_products': 0,
                'most_popular_product': 'N/A',
                'low_stock_count': 0,
                'total_users': 0,
                'new_users_today': 0,
                'total_reviews': 0,
                'avg_rating': 0.0,
                'pending_reviews': 0,
                'recent_activity': '• No data available'
            }
    
    def get_admin_logs(self, limit: int = 50) -> List[Dict]:
        """Get admin activity logs"""
        try:
            return db.get_admin_logs(limit)
        except Exception as e:
            logger.error(f"Error getting admin logs: {e}")
            return []
    
    def get_sales_report(self, days: int = 30) -> Dict:
        """Get sales report for specified period"""
        try:
            # Get all orders
            all_orders = db.get_all_orders()
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_orders = []
            
            for order in all_orders:
                order_date = datetime.fromisoformat(order['created_at'])
                if order_date >= cutoff_date:
                    recent_orders.append(order)
            
            # Calculate metrics
            total_orders = len(recent_orders)
            paid_orders = [o for o in recent_orders if o['status'] == 'paid']
            total_revenue = sum(o['total_amount'] - o['discount_amount'] for o in paid_orders)
            avg_order_value = total_revenue / len(paid_orders) if paid_orders else 0
            
            # Daily breakdown
            daily_sales = {}
            for order in paid_orders:
                order_date = datetime.fromisoformat(order['created_at']).date()
                date_str = order_date.strftime('%Y-%m-%d')
                
                if date_str not in daily_sales:
                    daily_sales[date_str] = {'orders': 0, 'revenue': 0}
                
                daily_sales[date_str]['orders'] += 1
                daily_sales[date_str]['revenue'] += order['total_amount'] - order['discount_amount']
            
            return {
                'period_days': days,
                'total_orders': total_orders,
                'paid_orders': len(paid_orders),
                'total_revenue': total_revenue,
                'avg_order_value': avg_order_value,
                'conversion_rate': (len(paid_orders) / total_orders * 100) if total_orders > 0 else 0,
                'daily_sales': daily_sales
            }
            
        except Exception as e:
            logger.error(f"Error generating sales report: {e}")
            return {
                'period_days': days,
                'total_orders': 0,
                'paid_orders': 0,
                'total_revenue': 0.0,
                'avg_order_value': 0.0,
                'conversion_rate': 0.0,
                'daily_sales': {}
            }
    
    def get_product_performance(self) -> List[Dict]:
        """Get product performance metrics"""
        try:
            products = db.get_all_products()
            all_orders = db.get_all_orders()
            
            product_stats = {}
            
            # Initialize stats for all products
            for product in products:
                product_stats[product['id']] = {
                    'product_id': product['id'],
                    'name': product['name'],
                    'type': product['type'],
                    'price': product['price'],
                    'stock': product['stock_quantity'],
                    'orders': 0,
                    'quantity_sold': 0,
                    'revenue': 0.0,
                    'avg_rating': 0.0,
                    'review_count': 0
                }
            
            # Analyze orders
            for order in all_orders:
                if order['status'] == 'paid':
                    order_data = order.get('order_data', [])
                    for item in order_data:
                        product_id = item.get('product_id')
                        if product_id in product_stats:
                            quantity = item.get('quantity', 0)
                            price = item.get('price', 0)
                            
                            product_stats[product_id]['orders'] += 1
                            product_stats[product_id]['quantity_sold'] += quantity
                            product_stats[product_id]['revenue'] += price * quantity
            
            # Add review data
            for product_id, stats in product_stats.items():
                reviews = db.get_product_reviews(product_id, approved_only=True)
                if reviews:
                    stats['review_count'] = len(reviews)
                    stats['avg_rating'] = sum(r['rating'] for r in reviews) / len(reviews)
            
            # Convert to list and sort by revenue
            performance_list = list(product_stats.values())
            performance_list.sort(key=lambda x: x['revenue'], reverse=True)
            
            return performance_list
            
        except Exception as e:
            logger.error(f"Error getting product performance: {e}")
            return []
    
    def get_user_analytics(self) -> Dict:
        """Get user behavior analytics"""
        try:
            total_users = db.get_user_count()
            all_orders = db.get_all_orders()
            
            # User activity
            users_with_orders = len(set(order['user_id'] for order in all_orders))
            users_with_paid_orders = len(set(
                order['user_id'] for order in all_orders if order['status'] == 'paid'
            ))
            
            # Order frequency
            user_order_counts = {}
            for order in all_orders:
                if order['status'] == 'paid':
                    user_id = order['user_id']
                    user_order_counts[user_id] = user_order_counts.get(user_id, 0) + 1
            
            # Calculate metrics
            repeat_customers = sum(1 for count in user_order_counts.values() if count > 1)
            avg_orders_per_customer = (
                sum(user_order_counts.values()) / len(user_order_counts)
                if user_order_counts else 0
            )
            
            return {
                'total_users': total_users,
                'users_with_orders': users_with_orders,
                'users_with_paid_orders': users_with_paid_orders,
                'repeat_customers': repeat_customers,
                'avg_orders_per_customer': round(avg_orders_per_customer, 2),
                'conversion_rate': (users_with_paid_orders / total_users * 100) if total_users > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {
                'total_users': 0,
                'users_with_orders': 0,
                'users_with_paid_orders': 0,
                'repeat_customers': 0,
                'avg_orders_per_customer': 0.0,
                'conversion_rate': 0.0
            }
    
    def format_analytics_report(self) -> str:
        """Format comprehensive analytics report"""
        try:
            analytics = self.get_analytics_data()
            sales_report = self.get_sales_report(30)
            user_analytics = self.get_user_analytics()
            product_performance = self.get_product_performance()[:5]  # Top 5
            
            text = f"""
📊 **Comprehensive Analytics Report**

**📈 Sales Overview (Last 30 Days):**
• Total Revenue: {format_currency(sales_report['total_revenue'])}
• Orders: {sales_report['paid_orders']} paid / {sales_report['total_orders']} total
• Average Order Value: {format_currency(sales_report['avg_order_value'])}
• Conversion Rate: {sales_report['conversion_rate']:.1f}%

**👥 User Analytics:**
• Total Users: {user_analytics['total_users']}
• Active Customers: {user_analytics['users_with_paid_orders']}
• Repeat Customers: {user_analytics['repeat_customers']}
• Customer Conversion: {user_analytics['conversion_rate']:.1f}%

**📦 Product Performance:**
• Total Products: {analytics['total_products']}
• Low Stock Items: {analytics['low_stock_count']}
• Average Rating: {analytics['avg_rating']}/5.0

**🏆 Top Performing Products:**
            """
            
            for i, product in enumerate(product_performance, 1):
                text += f"\n{i}. {product['name']}: {format_currency(product['revenue'])} revenue"
            
            text += f"""

**⭐ Review Statistics:**
• Total Reviews: {analytics['total_reviews']}
• Pending Approval: {analytics['pending_reviews']}
• Average Rating: {analytics['avg_rating']}/5.0
            """
            
            return text
            
        except Exception as e:
            logger.error(f"Error formatting analytics report: {e}")
            return "❌ Error generating analytics report"
    
    def export_data(self, data_type: str) -> Dict:
        """Export data for external analysis"""
        try:
            if data_type == "products":
                return {
                    'type': 'products',
                    'data': db.get_all_products(),
                    'count': db.get_product_count()
                }
            elif data_type == "orders":
                return {
                    'type': 'orders',
                    'data': db.get_all_orders(),
                    'count': db.get_order_count()
                }
            elif data_type == "users":
                # Note: This would need user export method in database
                return {
                    'type': 'users',
                    'data': [],
                    'count': db.get_user_count()
                }
            elif data_type == "reviews":
                return {
                    'type': 'reviews',
                    'data': db.get_pending_reviews() + [
                        review for product in db.get_all_products()
                        for review in db.get_product_reviews(product['id'], approved_only=False)
                    ],
                    'count': db.get_review_count()
                }
            else:
                return {'error': 'Invalid data type'}
                
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {'error': str(e)}
    
    def get_inventory_alerts(self) -> List[Dict]:
        """Get inventory-related alerts"""
        try:
            alerts = []
            
            # Low stock alerts
            low_stock_products = db.get_low_stock_products(5)
            for product in low_stock_products:
                alerts.append({
                    'type': 'low_stock',
                    'severity': 'warning' if product['stock_quantity'] > 0 else 'critical',
                    'message': f"{product['name']}: {product['stock_quantity']} items remaining",
                    'product_id': product['id']
                })
            
            # Pending reviews alert
            pending_count = db.get_pending_review_count()
            if pending_count > 0:
                alerts.append({
                    'type': 'pending_reviews',
                    'severity': 'info',
                    'message': f"{pending_count} reviews awaiting approval"
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting inventory alerts: {e}")
            return []
    
    def log_action(self, admin_id: int, action: str, details: str = None):
        """Log admin action"""
        try:
            db.log_admin_action(admin_id, action, details)
            logger.info(f"Admin action logged: {action} by user {admin_id}")
        except Exception as e:
            logger.error(f"Error logging admin action: {e}")
