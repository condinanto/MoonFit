"""
Initialize MOON FIT store with sample products
"""
from database import db
from product_manager import ProductManager

def add_sample_products():
    """Add sample products to the store"""
    products = [
        # T-shirts
        {
            'name': 'MOON Classic Tee',
            'type': 'tshirt',
            'price': 29.99,
            'stock_quantity': 50,
            'description': 'Comfortable cotton t-shirt with MOON FIT logo. Perfect for everyday wear.',
            'image_url': 'https://via.placeholder.com/300x300/2C3E50/FFFFFF?text=MOON+TEE'
        },
        {
            'name': 'Lunar Phase Tee',
            'type': 'tshirt', 
            'price': 34.99,
            'stock_quantity': 30,
            'description': 'Premium t-shirt featuring artistic lunar phase design. Made from organic cotton.',
            'image_url': 'https://via.placeholder.com/300x300/34495E/FFFFFF?text=LUNAR+TEE'
        },
        {
            'name': 'Eclipse Design Tee',
            'type': 'tshirt',
            'price': 32.99,
            'stock_quantity': 25,
            'description': 'Unique eclipse-themed t-shirt with glow-in-the-dark elements.',
            'image_url': 'https://via.placeholder.com/300x300/1A252F/FFFFFF?text=ECLIPSE+TEE'
        },
        
        # Hoodies
        {
            'name': 'MOON Cozy Hoodie',
            'type': 'hoodie',
            'price': 59.99,
            'stock_quantity': 40,
            'description': 'Ultra-soft fleece hoodie with spacious front pocket. Perfect for cool evenings.',
            'image_url': 'https://via.placeholder.com/300x300/8E44AD/FFFFFF?text=MOON+HOODIE'
        },
        {
            'name': 'Galaxy Explorer Hoodie',
            'type': 'hoodie',
            'price': 69.99,
            'stock_quantity': 20,
            'description': 'Premium hoodie with detailed galaxy print and adjustable drawstrings.',
            'image_url': 'https://via.placeholder.com/300x300/2980B9/FFFFFF?text=GALAXY+HOODIE'
        },
        {
            'name': 'Midnight Runner Hoodie',
            'type': 'hoodie',
            'price': 64.99,
            'stock_quantity': 35,
            'description': 'Athletic hoodie with moisture-wicking fabric. Ideal for outdoor activities.',
            'image_url': 'https://via.placeholder.com/300x300/16A085/FFFFFF?text=RUNNER+HOODIE'
        },
        
        # Hats
        {
            'name': 'MOON Fitted Cap',
            'type': 'hat',
            'price': 24.99,
            'stock_quantity': 60,
            'description': 'Classic fitted cap with embroidered MOON FIT logo. Adjustable strap.',
            'image_url': 'https://via.placeholder.com/300x300/E74C3C/FFFFFF?text=MOON+CAP'
        },
        {
            'name': 'Lunar Trucker Hat',
            'type': 'hat',
            'price': 19.99,
            'stock_quantity': 45,
            'description': 'Retro trucker hat with mesh back and vintage lunar design.',
            'image_url': 'https://via.placeholder.com/300x300/F39C12/FFFFFF?text=TRUCKER+HAT'
        },
        {
            'name': 'Star Gazer Beanie',
            'type': 'hat',
            'price': 22.99,
            'stock_quantity': 55,
            'description': 'Warm knit beanie with constellation pattern. Perfect for winter stargazing.',
            'image_url': 'https://via.placeholder.com/300x300/9B59B6/FFFFFF?text=BEANIE'
        }
    ]
    
    product_manager = ProductManager()
    
    for product in products:
        result = product_manager.add_product(
            name=product['name'],
            product_type=product['type'], 
            price=product['price'],
            stock_quantity=product['stock_quantity'],
            description=product['description'],
            image_url=product['image_url']
        )
        
        if result[0]:
            print(f"✓ Added: {product['name']}")
        else:
            print(f"✗ Failed to add: {product['name']} - {result[1]}")

def add_sample_discount_codes():
    """Add sample discount codes"""
    from discount_manager import DiscountManager
    discount_manager = DiscountManager()
    
    discount_codes = [
        {
            'code': 'WELCOME10',
            'discount_type': 'percentage',
            'discount_value': 10.0,
            'usage_limit': 100,
            'expires_at': None
        },
        {
            'code': 'SAVE20',
            'discount_type': 'fixed',
            'discount_value': 20.0,
            'usage_limit': 50,
            'expires_at': None
        },
        {
            'code': 'LUNAR50',
            'discount_type': 'percentage',
            'discount_value': 15.0,
            'usage_limit': 25,
            'expires_at': None
        }
    ]
    
    for discount in discount_codes:
        result = discount_manager.generate_discount_code(
            code=discount['code'],
            discount_type=discount['discount_type'],
            discount_value=discount['discount_value'],
            usage_limit=discount['usage_limit'],
            expires_at=discount['expires_at']
        )
        
        if result[0]:
            print(f"✓ Added discount code: {discount['code']}")
        else:
            print(f"✗ Failed to add discount code: {discount['code']} - {result[1]}")

if __name__ == "__main__":
    print("🌙 Initializing MOON FIT store with sample data...")
    
    print("\n📦 Adding sample products...")
    add_sample_products()
    
    print("\n🎁 Adding sample discount codes...")
    add_sample_discount_codes()
    
    print("\n✅ Sample data initialization complete!")
    print("\nYour MOON FIT store now has:")
    print("• 9 sample products (3 T-shirts, 3 hoodies, 3 hats)")
    print("• 3 discount codes (WELCOME10, SAVE20, LUNAR50)")
    print("• Ready for customer testing!")