"""
Admin panel functionality for MOON FIT Telegram Bot
"""
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from database import db
from product_manager import product_manager
from discount_manager import discount_manager
from review_manager import review_manager
from config import ADMIN_ID, CURRENCY

logger = logging.getLogger(__name__)

class AdminPanel:
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == ADMIN_ID
    
    @staticmethod
    def get_dashboard_stats() -> Dict:
        """Get admin dashboard statistics"""
        try:
            stats = db.get_sales_stats()
            
            # Get additional stats
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute('SELECT COUNT(*) FROM users')
                stats['total_users'] = cursor.fetchone()[0]
                
                # Pending orders
                cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
                stats['pending_orders'] = cursor.fetchone()[0]
                
                # Low stock products
                cursor.execute('SELECT COUNT(*) FROM products WHERE stock_quantity <= 10 AND active = TRUE')
                stats['low_stock_products'] = cursor.fetchone()[0]
                
                # Today's orders
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
                    FROM orders 
                    WHERE date(created_at) = date('now') AND status != 'cancelled'
                ''')
                today_data = cursor.fetchone()
                stats['today_orders'] = today_data[0]
                stats['today_revenue'] = today_data[1]
                
                # Pending reviews
                cursor.execute('SELECT COUNT(*) FROM reviews WHERE approved = FALSE')
                stats['pending_reviews'] = cursor.fetchone()[0]
                
                # Active discount codes
                cursor.execute('SELECT COUNT(*) FROM discount_codes WHERE active = TRUE')
                stats['active_discounts'] = cursor.fetchone()[0]
                
            return stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    @staticmethod
    def format_dashboard_text(stats: Dict) -> str:
        """Format dashboard statistics for display"""
        if not stats:
            return "❌ Unable to load dashboard statistics"
        
        text = "📊 **Admin Dashboard**\n\n"
        
        # Sales overview
        text += "💰 **Sales Overview**\n"
        text += f"   Total Orders: {stats.get('total_orders', 0)}\n"
        text += f"   Total Revenue: {stats.get('total_revenue', 0):.3f} {CURRENCY}\n"
        text += f"   Today's Orders: {stats.get('today_orders', 0)}\n"
        text += f"   Today's Revenue: {stats.get('today_revenue', 0):.3f} {CURRENCY}\n\n"
        
        # Pending items
        text += "⏳ **Pending Items**\n"
        text += f"   Pending Orders: {stats.get('pending_orders', 0)}\n"
        text += f"   Pending Reviews: {stats.get('pending_reviews', 0)}\n\n"
        
        # Store status
        text += "🏪 **Store Status**\n"
        text += f"   Total Users: {stats.get('total_users', 0)}\n"
        text += f"   Low Stock Products: {stats.get('low_stock_products', 0)}\n"
        text += f"   Active Discounts: {stats.get('active_discounts', 0)}\n\n"
        
        # Discount summary
        if stats.get('discount_orders', 0) > 0:
            text += "🎫 **Discount Usage**\n"
            text += f"   Orders with Discounts: {stats.get('discount_orders', 0)}\n"
            text += f"   Total Discounts Given: {stats.get('total_discounts', 0):.3f} {CURRENCY}\n\n"
        
        # Sales by product type
        if stats.get('by_type'):
            text += "📈 **Sales by Category**\n"
            for category in stats['by_type']:
                emoji = {'tshirt': '👕', 'hoodie': '👔', 'hat': '🧢'}.get(category['type'], '📦')
                text += f"   {emoji} {category['type'].title()}: {category['orders']} orders, {category['revenue']:.3f} {CURRENCY}\n"
        
        return text
    
    @staticmethod
    def get_recent_orders(limit: int = 10) -> List[Dict]:
        """Get recent orders for admin review"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT o.*, u.username, u.first_name
                    FROM orders o
                    JOIN users u ON o.user_id = u.user_id
                    ORDER BY o.created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                orders = []
                for row in cursor.fetchall():
                    order = dict(row)
                    order['products'] = db.get_order(order['id'])['products'] if order['id'] else []
                    orders.append(order)
                
                return orders
                
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []
    
    @staticmethod
    def format_orders_text(orders: List[Dict]) -> str:
        """Format orders list for admin display"""
        if not orders:
            return "📦 **No orders found**"
        
        text = f"📦 **Recent Orders** ({len(orders)})\n\n"
        
        for order in orders:
            status_emoji = {
                'pending': '⏳',
                'paid': '💰',
                'shipped': '📦',
                'delivered': '✅',
                'cancelled': '❌'
            }.get(order['status'], '❓')
            
            user_name = order.get('first_name', 'Unknown')
            if order.get('username'):
                user_name = f"@{order['username']}"
            
            order_date = datetime.fromisoformat(order['created_at']).strftime('%Y-%m-%d %H:%M')
            
            text += f"**Order #{order['id']}** {status_emoji}\n"
            text += f"User: {user_name}\n"
            text += f"Amount: {order['final_amount']:.3f} {CURRENCY}"
            
            if order.get('discount_code'):
                text += f" (Discount: -{order['discount_amount']:.3f})"
            
            text += f"\nDate: {order_date}\n"
            text += f"Status: {order['status'].title()}\n\n"
        
        return text
    
    @staticmethod
    def update_order_status(order_id: int, new_status: str, admin_id: int) -> Tuple[bool, str]:
        """Update order status"""
        try:
            valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']
            if new_status not in valid_statuses:
                return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            
            order = db.get_order(order_id)
            if not order:
                return False, "Order not found"
            
            old_status = order['status']
            db.update_order_status(order_id, new_status)
            
            # Log admin action
            db.log_admin_action(
                admin_id,
                "UPDATE_ORDER_STATUS",
                f"Order #{order_id}: {old_status} → {new_status}"
            )
            
            logger.info(f"Admin {admin_id} updated order {order_id} status: {old_status} → {new_status}")
            return True, f"Order #{order_id} status updated to {new_status}"
            
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False, "Failed to update order status"
    
    @staticmethod
    def get_order_details(order_id: int) -> Optional[Dict]:
        """Get detailed order information for admin"""
        try:
            order = db.get_order(order_id)
            if not order:
                return None
            
            # Get user information
            user = db.get_user(order['user_id'])
            if user:
                order['user_info'] = {
                    'username': user.get('username'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name')
                }
            
            # Add formatted dates
            order['created_at_formatted'] = datetime.fromisoformat(order['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            if order['updated_at']:
                order['updated_at_formatted'] = datetime.fromisoformat(order['updated_at']).strftime('%Y-%m-%d %H:%M:%S')
            
            return order
            
        except Exception as e:
            logger.error(f"Error getting order details: {e}")
            return None
    
    @staticmethod
    def format_order_details(order: Dict) -> str:
        """Format detailed order information"""
        if not order:
            return "Order not found"
        
        text = f"📦 **Order #{order['id']} Details**\n\n"
        
        # Order status
        status_emoji = {
            'pending': '⏳',
            'paid': '💰',
            'shipped': '📦',
            'delivered': '✅',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        text += f"**Status:** {status_emoji} {order['status'].title()}\n"
        
        # Customer information
        user_info = order.get('user_info', {})
        customer_name = user_info.get('first_name', 'Unknown')
        if user_info.get('username'):
            customer_name = f"@{user_info['username']} ({customer_name})"
        
        text += f"**Customer:** {customer_name} (ID: {order['user_id']})\n"
        text += f"**Order Date:** {order['created_at_formatted']}\n"
        
        if order.get('updated_at_formatted'):
            text += f"**Last Updated:** {order['updated_at_formatted']}\n"
        
        text += "\n**Items Ordered:**\n"
        
        # Order items
        for item in order['products']:
            text += f"• {item['name']} x{item['quantity']}\n"
            text += f"  Price: {item['price']:.3f} {CURRENCY} each\n"
            text += f"  Subtotal: {item['total_price']:.3f} {CURRENCY}\n\n"
        
        # Pricing information
        text += f"**Subtotal:** {order['total_amount']:.3f} {CURRENCY}\n"
        
        if order.get('discount_code'):
            text += f"**Discount Code:** {order['discount_code']}\n"
            text += f"**Discount Amount:** -{order['discount_amount']:.3f} {CURRENCY}\n"
        
        text += f"**Final Total:** {order['final_amount']:.3f} {CURRENCY}\n"
        
        # Payment information
        if order.get('payment_hash'):
            text += f"\n**Payment Hash:** `{order['payment_hash']}`\n"
        
        return text
    
    @staticmethod
    def get_admin_logs(limit: int = 20) -> List[Dict]:
        """Get recent admin activity logs"""
        try:
            return db.get_admin_logs(limit)
        except Exception as e:
            logger.error(f"Error getting admin logs: {e}")
            return []
    
    @staticmethod
    def format_admin_logs(logs: List[Dict]) -> str:
        """Format admin logs for display"""
        if not logs:
            return "📝 **No admin activity logs found**"
        
        text = f"📝 **Admin Activity Logs** (Last {len(logs)})\n\n"
        
        for log in logs:
            timestamp = datetime.fromisoformat(log['timestamp']).strftime('%m-%d %H:%M')
            admin_name = log.get('username', f"Admin {log['admin_id']}")
            
            text += f"**{timestamp}** - {admin_name}\n"
            text += f"Action: {log['action']}\n"
            
            if log.get('details'):
                details = log['details']
                if len(details) > 100:
                    details = details[:97] + "..."
                text += f"Details: _{details}_\n"
            
            text += "\n"
        
        return text
    
    @staticmethod
    def send_notification_to_admin(bot, message: str):
        """Send notification to admin"""
        try:
            import asyncio
            asyncio.create_task(bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='Markdown'))
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
    
    @staticmethod
    def get_analytics_report(days: int = 30) -> Dict:
        """Generate analytics report for specified period"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Orders in period
                cursor.execute('''
                    SELECT COUNT(*), COALESCE(SUM(final_amount), 0)
                    FROM orders 
                    WHERE created_at >= ? AND created_at <= ?
                    AND status != 'cancelled'
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                period_orders, period_revenue = cursor.fetchone()
                
                # Daily sales
                cursor.execute('''
                    SELECT date(created_at) as order_date, 
                           COUNT(*) as orders, 
                           COALESCE(SUM(final_amount), 0) as revenue
                    FROM orders 
                    WHERE created_at >= ? AND created_at <= ?
                    AND status != 'cancelled'
                    GROUP BY date(created_at)
                    ORDER BY order_date DESC
                    LIMIT 7
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                daily_sales = [dict(row) for row in cursor.fetchall()]
                
                # Top products
                cursor.execute('''
                    SELECT p.name, p.type, COUNT(*) as orders,
                           COALESCE(SUM(json_extract(op.value, '$.total_price')), 0) as revenue
                    FROM orders o
                    JOIN (
                        SELECT id as order_id, value
                        FROM orders, json_each(products)
                        WHERE created_at >= ? AND created_at <= ?
                        AND status != 'cancelled'
                    ) op ON o.id = op.order_id
                    JOIN products p ON json_extract(op.value, '$.product_id') = p.id
                    GROUP BY p.id
                    ORDER BY orders DESC
                    LIMIT 5
                ''', (start_date.isoformat(), end_date.isoformat()))
                
                top_products = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'period_days': days,
                    'period_orders': period_orders,
                    'period_revenue': period_revenue,
                    'daily_sales': daily_sales,
                    'top_products': top_products,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                }
                
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            return {}
    
    @staticmethod
    def format_analytics_report(report: Dict) -> str:
        """Format analytics report for display"""
        if not report:
            return "❌ Unable to generate analytics report"
        
        text = f"📈 **Analytics Report** ({report['period_days']} days)\n"
        text += f"Period: {report['start_date']} to {report['end_date']}\n\n"
        
        # Summary
        text += "📊 **Summary**\n"
        text += f"Total Orders: {report['period_orders']}\n"
        text += f"Total Revenue: {report['period_revenue']:.3f} {CURRENCY}\n"
        
        if report['period_orders'] > 0:
            avg_order = report['period_revenue'] / report['period_orders']
            text += f"Average Order Value: {avg_order:.3f} {CURRENCY}\n"
        
        text += "\n"
        
        # Daily sales (last 7 days)
        if report.get('daily_sales'):
            text += "📅 **Daily Sales** (Last 7 days)\n"
            for day in report['daily_sales']:
                text += f"{day['order_date']}: {day['orders']} orders, {day['revenue']:.3f} {CURRENCY}\n"
            text += "\n"
        
        # Top products
        if report.get('top_products'):
            text += "🏆 **Top Products**\n"
            for i, product in enumerate(report['top_products'], 1):
                emoji = {'tshirt': '👕', 'hoodie': '👔', 'hat': '🧢'}.get(product['type'], '📦')
                text += f"{i}. {emoji} {product['name']}: {product['orders']} orders, {product['revenue']:.3f} {CURRENCY}\n"
        
        return text

# Global admin panel instance
admin_panel = AdminPanel()
