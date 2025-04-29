import sqlite3
from datetime import datetime
import logging

class RTRSettlementProcessor:
    def __init__(self):
        self.conn = sqlite3.connect('payment_system.db')
        self.cursor = self.conn.cursor()

    def settle_transaction(self, debtor_bic, creditor_bic, amount):
        logging.info(f"Starting settlement process for {amount} from {debtor_bic} to {creditor_bic}")
        try:
            # Get user IDs and check balances
            debtor = self.get_user_by_bic(debtor_bic)
            creditor = self.get_user_by_bic(creditor_bic)
            
            if not debtor or not creditor:
                logging.error(f"Settlement Failed: Invalid BIC codes - Debtor: {debtor_bic}, Creditor: {creditor_bic}")
                return "Settlement Failed: Invalid BIC codes"

            if debtor['balance'] < amount:
                logging.error(f"Settlement Failed: Insufficient funds for {debtor_bic} (required: {amount}, available: {debtor['balance']})")
                return "Settlement Failed: Insufficient funds"

            # Start transaction
            self.cursor.execute("BEGIN EXCLUSIVE TRANSACTION")
            
            # Verify balance again after starting transaction
            self.cursor.execute("SELECT balance FROM users WHERE id = ?", (debtor['id'],))
            current_balance = self.cursor.fetchone()[0]
            
            if current_balance < amount:
                self.conn.rollback()
                logging.error(f"Settlement Failed: Insufficient funds for {debtor_bic} after transaction start (required: {amount}, available: {current_balance})")
                return "Settlement Failed: Insufficient funds"

            # Update balances
            self.update_balance(debtor['id'], -amount)
            self.update_balance(creditor['id'], amount)

            # Record payment
            self.record_payment(debtor['id'], creditor['id'], amount)
            
            self.conn.commit()
            logging.info(f"Successfully settled payment of {amount} from {debtor_bic} to {creditor_bic}")
            return "Settlement Success"
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Settlement error: {str(e)}")
            return f"Settlement Failed: {str(e)}"

    def get_user_by_bic(self, bic_code):
        self.cursor.execute("""
            SELECT u.id, u.balance 
            FROM users u 
            JOIN bic_codes b ON u.fi_code = b.fi_code 
            WHERE b.bic_code = ?
        """, (bic_code,))
        result = self.cursor.fetchone()
        return {'id': result[0], 'balance': result[1]} if result else None

    def update_balance(self, user_id, amount_change):
        logging.info(f"Updating balance for user {user_id} by {amount_change}")
        self.cursor.execute("""
            UPDATE users 
            SET balance = balance + ? 
            WHERE id = ?
        """, (amount_change, user_id))

    def record_payment(self, sender_id, recipient_id, amount):
        logging.info(f"Recording payment of {amount} from user {sender_id} to user {recipient_id}")
        self.cursor.execute("""
            INSERT INTO payments (sender_id, recipient_id, amount, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sender_id, recipient_id, amount, datetime.now().isoformat()))

    def __del__(self):
        self.conn.close()
