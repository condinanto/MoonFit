# MOON FIT Telegram Bot - Architecture Overview

## Overview

MOON FIT is a comprehensive Telegram e-commerce bot for a fashion store specializing in T-shirts, hoodies, and hats. The system integrates TON cryptocurrency payments, comprehensive admin management, discount codes, product reviews, and shopping cart functionality. The bot is designed as a complete e-commerce solution with both customer-facing features and admin panel capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern
The application follows a modular monolithic architecture with clear separation of concerns:

- **Main Application Layer**: Handles Telegram bot interactions and conversation flows
- **Business Logic Layer**: Separate managers for products, cart, discounts, reviews, and payments
- **Data Access Layer**: Centralized database operations through a Database class
- **Configuration Layer**: Environment-based configuration management

### Technology Stack
- **Framework**: Python with python-telegram-bot library
- **Database**: SQLite with custom ORM-like wrapper
- **Payment Integration**: TON blockchain API
- **Deployment**: Replit-compatible structure
- **Logging**: Python's built-in logging module

## Key Components

### 1. Bot Core (`main.py`)
- **Purpose**: Main application entry point and conversation handler
- **Architecture Decision**: Uses ConversationHandler for multi-step user interactions
- **Rationale**: Provides stateful conversations for complex operations like product creation and review submission
- **Features**: Command handling, callback query routing, conversation state management

### 2. Database Management (`database.py`)
- **Purpose**: Centralized data access layer with SQLite
- **Architecture Decision**: Custom database wrapper with row factory for dict-like access
- **Schema**: Users, products, orders, reviews, discount codes, admin logs, and payment tracking
- **Rationale**: SQLite chosen for simplicity and Replit compatibility
- **Features**: Context manager for connection handling, automatic rollback on errors

### 3. Product Management (`product_manager.py`)
- **Purpose**: Handles product CRUD operations and inventory management
- **Features**: Stock tracking, category management (T-shirts, hoodies, hats), price validation
- **Architecture Decision**: Static methods for stateless operations
- **Rationale**: Product operations don't require instance state

### 4. Shopping Cart (`cart_manager.py`)
- **Purpose**: Manages user shopping carts with session persistence
- **Architecture Decision**: JSON storage in database for cart data
- **Features**: Stock validation, quantity management, price calculations
- **Rationale**: JSON storage allows flexible cart structure without complex relational design

### 5. Payment Processing (`ton_payments.py`)
- **Purpose**: Handles TON cryptocurrency payment integration
- **Architecture Decision**: Async API calls to TON blockchain services
- **Features**: Transaction verification, payment monitoring, testnet/mainnet support
- **Rationale**: TON chosen as primary payment method for crypto e-commerce

### 6. Discount System (`discount_manager.py`)
- **Purpose**: Manages promotional codes and discount calculations
- **Features**: Percentage and fixed amount discounts, usage limits, expiry dates
- **Architecture Decision**: Database-stored discount codes with validation logic
- **Rationale**: Flexible discount system for marketing campaigns

### 7. Review System (`review_manager.py`)
- **Purpose**: Handles product reviews and ratings
- **Features**: 1-5 star ratings, comment system, admin approval workflow
- **Architecture Decision**: One review per user per product limitation
- **Rationale**: Prevents spam while maintaining review authenticity

### 8. Admin Panel (`admin_panel.py`)
- **Purpose**: Administrative interface for store management
- **Features**: Analytics dashboard, product management, order tracking
- **Architecture Decision**: Role-based access control with single admin ID
- **Rationale**: Simple admin system suitable for small store operations

## Data Flow

### Customer Purchase Flow
1. User browses products by category
2. Products added to cart with stock validation
3. Cart review and discount code application
4. TON payment generation and monitoring
5. Order creation and inventory update
6. Optional product review after purchase

### Admin Management Flow
1. Admin authentication via user ID check
2. Product creation/management through conversation handlers
3. Order monitoring and status updates
4. Analytics and reporting dashboard access
5. Discount code creation and management

### Payment Verification Flow
1. Payment request generated with unique identifier
2. User transfers TON to specified wallet address
3. Background monitoring checks for incoming transactions
4. Payment verification triggers order processing
5. Inventory updates and user notification

## External Dependencies

### TON Blockchain Integration
- **API**: TON Center API for transaction monitoring
- **Wallet**: Store wallet address for receiving payments
- **Environment**: Testnet/mainnet configuration support

### Telegram Bot API
- **Bot Token**: Telegram bot authentication
- **Webhooks**: Real-time message handling
- **Inline Keyboards**: Interactive user interface

### Database Storage
- **SQLite**: Local file-based database
- **No external database dependencies**: Self-contained for Replit deployment

## Deployment Strategy

### Replit Compatibility
- **File Structure**: Flat module organization
- **Dependencies**: Python packages via requirements.txt
- **Configuration**: Environment variables for sensitive data
- **Database**: Local SQLite file in project directory

### Environment Configuration
- **BOT_TOKEN**: Telegram bot authentication token
- **ADMIN_ID**: Telegram user ID for admin access
- **TON_WALLET_ADDRESS**: Receiving wallet for payments
- **TON_API_KEY**: TON Center API access key
- **Database Path**: Configurable SQLite file location

### Scalability Considerations
- **Single Admin**: Current design supports one admin user
- **Local Database**: SQLite suitable for moderate traffic
- **Payment Processing**: Asynchronous handling for responsiveness
- **Future Migration**: Modular design allows easy database migration to PostgreSQL

The architecture prioritizes simplicity and maintainability while providing a complete e-commerce solution. The modular design allows for easy feature additions and modifications without affecting core functionality.