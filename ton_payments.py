"""
TON payment processing for MOON FIT Telegram Bot
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from config import TON_WALLET_ADDRESS, TON_API_KEY, TON_TESTNET, PAYMENT_TIMEOUT, MIN_TON_AMOUNT

logger = logging.getLogger(__name__)

class TONPaymentProcessor:
    def __init__(self):
        self.wallet_address = TON_WALLET_ADDRESS
        self.api_key = TON_API_KEY
        self.testnet = TON_TESTNET
        
        # API endpoints
        if self.testnet:
            self.api_base = "https://testnet.toncenter.com/api/v2"
        else:
            self.api_base = "https://toncenter.com/api/v2"
    
    async def get_transaction_history(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get transaction history for the wallet"""
        try:
            url = f"{self.api_base}/getTransactions"
            params = {
                'address': self.wallet_address,
                'limit': limit,
                'offset': offset,
                'api_key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result', [])
                    
                    logger.error(f"Failed to get transactions: {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            return []
    
    async def verify_payment(self, expected_amount: float, comment: str, 
                           timeout: int = PAYMENT_TIMEOUT) -> Tuple[bool, Optional[str]]:
        """
        Verify if payment with specific amount and comment was received
        Returns (success, transaction_hash)
        """
        start_time = datetime.now()
        check_interval = 10  # Check every 10 seconds
        
        logger.info(f"Starting payment verification for {expected_amount} TON with comment: {comment}")
        
        while datetime.now() - start_time < timedelta(seconds=timeout):
            try:
                transactions = await self.get_transaction_history(limit=50)
                
                for tx in transactions:
                    # Check if transaction is incoming
                    if not self._is_incoming_transaction(tx):
                        continue
                    
                    # Get transaction details
                    tx_amount = self._get_transaction_amount(tx)
                    tx_comment = self._get_transaction_comment(tx)
                    tx_hash = tx.get('transaction_id', {}).get('hash', '')
                    
                    # Verify amount and comment match
                    if (abs(tx_amount - expected_amount) < 0.001 and  # Allow small precision errors
                        tx_comment == comment):
                        logger.info(f"Payment verified! Hash: {tx_hash}, Amount: {tx_amount}")
                        return True, tx_hash
                
                # Wait before checking again
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error during payment verification: {e}")
                await asyncio.sleep(check_interval)
        
        logger.warning(f"Payment verification timeout for amount {expected_amount} with comment {comment}")
        return False, None
    
    def _is_incoming_transaction(self, tx: Dict) -> bool:
        """Check if transaction is incoming to our wallet"""
        try:
            in_msg = tx.get('in_msg', {})
            if not in_msg:
                return False
            
            destination = in_msg.get('destination')
            return destination == self.wallet_address
        except Exception:
            return False
    
    def _get_transaction_amount(self, tx: Dict) -> float:
        """Extract transaction amount in TON"""
        try:
            in_msg = tx.get('in_msg', {})
            value = int(in_msg.get('value', '0'))
            # Convert from nanoTON to TON
            return value / 1_000_000_000
        except Exception:
            return 0.0
    
    def _get_transaction_comment(self, tx: Dict) -> str:
        """Extract transaction comment/memo"""
        try:
            in_msg = tx.get('in_msg', {})
            msg_data = in_msg.get('msg_data', {})
            
            # Try to decode comment from different possible fields
            if msg_data.get('@type') == 'msg.dataText':
                text = msg_data.get('text', '')
                if text:
                    return text
            
            # Try to get comment from message body
            body = in_msg.get('message', '')
            if body:
                return body
            
            return ''
        except Exception:
            return ''
    
    def generate_payment_link(self, amount: float, comment: str) -> str:
        """Generate TON payment link for wallets"""
        # Format amount to avoid scientific notation
        amount_str = f"{amount:.9f}".rstrip('0').rstrip('.')
        
        # Generate payment link for popular TON wallets
        payment_url = f"ton://transfer/{self.wallet_address}?amount={int(amount * 1_000_000_000)}&text={comment}"
        
        return payment_url
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information for display"""
        return {
            'address': self.wallet_address,
            'testnet': self.testnet,
            'network': 'Testnet' if self.testnet else 'Mainnet'
        }
    
    async def get_wallet_balance(self) -> float:
        """Get current wallet balance"""
        try:
            url = f"{self.api_base}/getAddressBalance"
            params = {
                'address': self.wallet_address,
                'api_key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            balance_nano = int(data.get('result', '0'))
                            return balance_nano / 1_000_000_000
            
            return 0.0
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return 0.0
    
    def format_payment_message(self, amount: float, order_id: int, user_id: int) -> str:
        """Format payment instructions message"""
        comment = f"ORDER_{order_id}_{user_id}"
        payment_link = self.generate_payment_link(amount, comment)
        
        wallet_info = self.get_wallet_info()
        network_text = f"📱 **{wallet_info['network']} Network**"
        
        message = f"""
💰 **Payment Instructions**

{network_text}

**Amount to Pay:** `{amount:.6f} TON`
**Wallet Address:** `{self.wallet_address}`
**Payment Comment:** `{comment}`

🔗 **Quick Payment Links:**
• [Open in Tonkeeper](tonkeeper://transfer/{self.wallet_address}?amount={int(amount * 1_000_000_000)}&text={comment})
• [Open in @wallet]({payment_link})

⚠️ **Important:**
1. Send EXACTLY `{amount:.6f} TON`
2. Include the comment: `{comment}`
3. Payment will be verified automatically
4. Do not send from exchanges

⏰ Payment timeout: {PAYMENT_TIMEOUT // 60} minutes

After sending, your payment will be automatically verified within 1-2 minutes.
"""
        return message
    
    def validate_amount(self, amount: float) -> Tuple[bool, str]:
        """Validate payment amount"""
        if amount < MIN_TON_AMOUNT:
            return False, f"Minimum payment amount is {MIN_TON_AMOUNT} TON"
        
        if amount > 1000:  # Reasonable maximum
            return False, "Payment amount too large"
        
        return True, "Valid amount"

# Global payment processor instance
ton_processor = TONPaymentProcessor()
