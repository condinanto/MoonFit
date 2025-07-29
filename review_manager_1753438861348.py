"""
Review and rating management for MOON FIT Telegram Bot
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from database import db

logger = logging.getLogger(__name__)

class ReviewManager:
    @staticmethod
    def add_review(user_id: int, product_id: int, rating: int, 
                  comment: str = None, order_id: int = None) -> Tuple[bool, str]:
        """Add a product review"""
        try:
            # Validate rating
            if rating < 1 or rating > 5:
                return False, "Rating must be between 1 and 5 stars"
            
            # Check if product exists
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            # Check if user already reviewed this product
            existing_reviews = db.get_product_reviews(product_id, approved_only=False)
            for review in existing_reviews:
                if review['user_id'] == user_id:
                    return False, "You have already reviewed this product"
            
            # Add review
            review_id = db.add_review(
                user_id=user_id,
                product_id=product_id,
                rating=rating,
                comment=comment,
                order_id=order_id
            )
            
            logger.info(f"User {user_id} added review for product {product_id}: {rating} stars")
            return True, "Review submitted successfully! It will be visible after admin approval."
            
        except Exception as e:
            logger.error(f"Error adding review: {e}")
            return False, "Failed to submit review"
    
    @staticmethod
    def get_product_reviews(product_id: int, approved_only: bool = True, limit: int = 20) -> List[Dict]:
        """Get reviews for a product"""
        try:
            reviews = db.get_product_reviews(product_id, approved_only)
            return reviews[:limit]  # Limit number of reviews displayed
        except Exception as e:
            logger.error(f"Error getting product reviews: {e}")
            return []
    
    @staticmethod
    def get_pending_reviews(limit: int = 50) -> List[Dict]:
        """Get reviews pending admin approval"""
        try:
            return db.get_pending_reviews()[:limit]
        except Exception as e:
            logger.error(f"Error getting pending reviews: {e}")
            return []
    
    @staticmethod
    def approve_review(review_id: int, admin_id: int) -> Tuple[bool, str]:
        """Approve a review"""
        try:
            success = db.approve_review(review_id)
            if success:
                db.log_admin_action(admin_id, "APPROVE_REVIEW", f"Approved review ID: {review_id}")
                logger.info(f"Admin {admin_id} approved review {review_id}")
                return True, "Review approved successfully"
            else:
                return False, "Review not found"
        except Exception as e:
            logger.error(f"Error approving review: {e}")
            return False, "Failed to approve review"
    
    @staticmethod
    def delete_review(review_id: int, admin_id: int) -> Tuple[bool, str]:
        """Delete a review"""
        try:
            success = db.delete_review(review_id)
            if success:
                db.log_admin_action(admin_id, "DELETE_REVIEW", f"Deleted review ID: {review_id}")
                logger.info(f"Admin {admin_id} deleted review {review_id}")
                return True, "Review deleted successfully"
            else:
                return False, "Review not found"
        except Exception as e:
            logger.error(f"Error deleting review: {e}")
            return False, "Failed to delete review"
    
    @staticmethod
    def get_product_rating_summary(product_id: int) -> Dict:
        """Get product rating summary statistics"""
        try:
            reviews = db.get_product_reviews(product_id, approved_only=True)
            
            if not reviews:
                return {
                    'average_rating': 0.0,
                    'total_reviews': 0,
                    'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }
            
            total_reviews = len(reviews)
            total_rating = sum(review['rating'] for review in reviews)
            average_rating = total_rating / total_reviews
            
            # Rating distribution
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for review in reviews:
                rating_distribution[review['rating']] += 1
            
            return {
                'average_rating': round(average_rating, 1),
                'total_reviews': total_reviews,
                'rating_distribution': rating_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting product rating summary: {e}")
            return {
                'average_rating': 0.0,
                'total_reviews': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
    
    @staticmethod
    def format_reviews_text(product_id: int, limit: int = 10) -> str:
        """Format product reviews for display"""
        try:
            reviews = ReviewManager.get_product_reviews(product_id, approved_only=True, limit=limit)
            rating_summary = ReviewManager.get_product_rating_summary(product_id)
            
            if not reviews:
                return "⭐ **No reviews yet**\n\nBe the first to review this product!"
            
            # Header with summary
            text = f"⭐ **Product Reviews** ({rating_summary['total_reviews']} reviews)\n"
            text += f"**Average Rating:** {ReviewManager.format_rating(rating_summary['average_rating'])}\n\n"
            
            # Individual reviews
            for review in reviews:
                stars = "⭐" * review['rating']
                user_name = review.get('first_name', 'Anonymous')
                if review.get('username'):
                    user_name = f"@{review['username']}"
                
                review_date = datetime.fromisoformat(review['created_at']).strftime('%Y-%m-%d')
                
                text += f"**{user_name}** {stars} ({review_date})\n"
                
                if review['comment']:
                    # Limit comment length for display
                    comment = review['comment']
                    if len(comment) > 150:
                        comment = comment[:147] + "..."
                    text += f"_{comment}_\n\n"
                else:
                    text += "\n"
            
            if len(reviews) == limit and rating_summary['total_reviews'] > limit:
                remaining = rating_summary['total_reviews'] - limit
                text += f"_... and {remaining} more reviews_"
            
            return text
            
        except Exception as e:
            logger.error(f"Error formatting reviews text: {e}")
            return "Error loading reviews"
    
    @staticmethod
    def format_rating(rating: float) -> str:
        """Format rating as stars"""
        full_stars = int(rating)
        half_star = 1 if rating - full_stars >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        return "⭐" * full_stars + "⭐" * half_star + "☆" * empty_stars + f" ({rating}/5)"
    
    @staticmethod
    def format_pending_reviews_text(reviews: List[Dict]) -> str:
        """Format pending reviews for admin approval"""
        if not reviews:
            return "✅ **No pending reviews**\n\nAll reviews have been processed!"
        
        text = f"📝 **Pending Reviews** ({len(reviews)} awaiting approval)\n\n"
        
        for review in reviews:
            stars = "⭐" * review['rating']
            user_name = review.get('first_name', 'Anonymous')
            if review.get('username'):
                user_name = f"@{review['username']}"
            
            review_date = datetime.fromisoformat(review['created_at']).strftime('%Y-%m-%d %H:%M')
            
            text += f"**Review #{review['id']}**\n"
            text += f"Product: {review['product_name']}\n"
            text += f"User: {user_name}\n"
            text += f"Rating: {stars}\n"
            text += f"Date: {review_date}\n"
            
            if review['comment']:
                comment = review['comment']
                if len(comment) > 200:
                    comment = comment[:197] + "..."
                text += f"Comment: _{comment}_\n"
            
            text += "\n"
        
        return text
    
    @staticmethod
    def get_review_statistics() -> Dict:
        """Get overall review statistics for admin dashboard"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total reviews
                cursor.execute('SELECT COUNT(*) FROM reviews')
                total_reviews = cursor.fetchone()[0]
                
                # Pending reviews
                cursor.execute('SELECT COUNT(*) FROM reviews WHERE approved = FALSE')
                pending_reviews = cursor.fetchone()[0]
                
                # Approved reviews
                cursor.execute('SELECT COUNT(*) FROM reviews WHERE approved = TRUE')
                approved_reviews = cursor.fetchone()[0]
                
                # Average rating
                cursor.execute('SELECT AVG(rating) FROM reviews WHERE approved = TRUE')
                avg_rating_result = cursor.fetchone()[0]
                average_rating = round(avg_rating_result, 1) if avg_rating_result else 0.0
                
                # Reviews by rating
                cursor.execute('''
                    SELECT rating, COUNT(*) 
                    FROM reviews 
                    WHERE approved = TRUE 
                    GROUP BY rating 
                    ORDER BY rating
                ''')
                rating_distribution = dict(cursor.fetchall())
                
                # Fill missing ratings with 0
                for rating in range(1, 6):
                    if rating not in rating_distribution:
                        rating_distribution[rating] = 0
                
                return {
                    'total_reviews': total_reviews,
                    'pending_reviews': pending_reviews,
                    'approved_reviews': approved_reviews,
                    'average_rating': average_rating,
                    'rating_distribution': rating_distribution
                }
                
        except Exception as e:
            logger.error(f"Error getting review statistics: {e}")
            return {
                'total_reviews': 0,
                'pending_reviews': 0,
                'approved_reviews': 0,
                'average_rating': 0.0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
    
    @staticmethod
    def check_user_can_review(user_id: int, product_id: int) -> Tuple[bool, str]:
        """Check if user can review a product"""
        try:
            # Check if product exists
            product = db.get_product(product_id)
            if not product:
                return False, "Product not found"
            
            # Check if user already reviewed this product
            existing_reviews = db.get_product_reviews(product_id, approved_only=False)
            for review in existing_reviews:
                if review['user_id'] == user_id:
                    return False, "You have already reviewed this product"
            
            # Optionally: Check if user has purchased this product
            # For now, allow anyone to review
            return True, "You can review this product"
            
        except Exception as e:
            logger.error(f"Error checking if user can review: {e}")
            return False, "Error checking review permissions"
    
    @staticmethod
    def get_user_reviews(user_id: int) -> List[Dict]:
        """Get all reviews by a specific user"""
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.*, p.name as product_name, p.type as product_type
                    FROM reviews r
                    JOIN products p ON r.product_id = p.id
                    WHERE r.user_id = ?
                    ORDER BY r.created_at DESC
                ''', (user_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting user reviews: {e}")
            return []

# Global review manager instance
review_manager = ReviewManager()
