from src.database import Database
from src.account import AccountManager


class TransactionManager:
    """Handle all types of financial transactions in the banking system"""
    
    def __init__(self, db=None):
        """Initialize with database connection"""
        self.db = db if db else Database()
        self.account_manager = AccountManager(self.db)
    
    def deposit(self, account_id, amount, description=None):
        """Make a deposit to an account"""
        # Validate input
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Get account
        account = self.account_manager.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Update account balance
        new_balance = account["balance"] + amount
        self.account_manager.update_balance(account_id, new_balance)
        
        # Record transaction
        transaction_data = {
            "account_id": account_id,
            "transaction_type": "deposit",
            "amount": amount,
            "description": description or "Deposit",
            "related_account_id": None
        }
        
        transaction_id = self.record_transaction(**transaction_data)
        
        return {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "type": "deposit",
            "amount": amount,
            "new_balance": new_balance,
            "timestamp": self.db.get_current_timestamp()
        }
    
    def withdraw(self, account_id, amount, description=None):
        """Make a withdrawal from an account"""
        # Validate input
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        # Get account
        account = self.account_manager.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Check sufficient balance
        if account["balance"] < amount:
            raise ValueError("Insufficient funds for withdrawal")
        
        # Update account balance
        new_balance = account["balance"] - amount
        self.account_manager.update_balance(account_id, new_balance)
        
        # Record transaction
        transaction_data = {
            "account_id": account_id,
            "transaction_type": "withdrawal",
            "amount": amount,
            "description": description or "Withdrawal",
            "related_account_id": None
        }
        
        transaction_id = self.record_transaction(**transaction_data)
        
        return {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "type": "withdrawal",
            "amount": amount,
            "new_balance": new_balance,
            "timestamp": self.db.get_current_timestamp()
        }
    
    def transfer(self, from_account_id, to_account_id, amount, description=None):
        """Transfer funds between accounts"""
        # Validate input
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")
        
        # Get accounts
        from_account = self.account_manager.get_account(from_account_id)
        if not from_account:
            raise ValueError(f"Source account with ID {from_account_id} not found")
        
        to_account = self.account_manager.get_account(to_account_id)
        if not to_account:
            raise ValueError(f"Destination account with ID {to_account_id} not found")
        
        # Check sufficient balance
        if from_account["balance"] < amount:
            raise ValueError("Insufficient funds for transfer")
        
        # Use a transaction to ensure atomicity
        conn = self.db.begin_transaction()
        try:
            # Update source account balance
            new_from_balance = from_account["balance"] - amount
            self.account_manager.update_balance(from_account_id, new_from_balance)
            
            # Update destination account balance
            new_to_balance = to_account["balance"] + amount
            self.account_manager.update_balance(to_account_id, new_to_balance)
            
            # Record outgoing transaction
            outgoing_data = {
                "account_id": from_account_id,
                "transaction_type": "transfer_out",
                "amount": amount,
                "description": description or f"Transfer to account {to_account_id}",
                "related_account_id": to_account_id
            }
            outgoing_id = self.record_transaction(**outgoing_data)
            
            # Record incoming transaction
            incoming_data = {
                "account_id": to_account_id,
                "transaction_type": "transfer_in",
                "amount": amount,
                "description": description or f"Transfer from account {from_account_id}",
                "related_account_id": from_account_id
            }
            incoming_id = self.record_transaction(**incoming_data)
            
            self.db.commit_transaction()
            
            return {
                "outgoing_transaction_id": outgoing_id,
                "incoming_transaction_id": incoming_id,
                "from_account_id": from_account_id,
                "to_account_id": to_account_id,
                "amount": amount,
                "from_new_balance": new_from_balance,
                "to_new_balance": new_to_balance,
                "timestamp": self.db.get_current_timestamp()
            }
        except Exception as e:
            self.db.rollback_transaction()
            raise Exception(f"Transfer failed: {e}")
    
    def record_transaction(self, account_id, transaction_type, amount, description=None, related_account_id=None):
        """Record a transaction in the database"""
        valid_types = ["deposit", "withdrawal", "transfer_in", "transfer_out", "loan_disbursement", "loan_payment"]
        
        if transaction_type not in valid_types:
            raise ValueError(f"Invalid transaction type. Must be one of: {", ".join(valid_types)}")
        
        timestamp = self.db.get_current_timestamp()
        
        query = """
            INSERT INTO transactions (
                account_id, transaction_type, amount, 
                description, related_account_id, transaction_date
            ) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            account_id,
            transaction_type,
            amount,
            description or transaction_type.replace("_", " ").capitalize(),
            related_account_id,
            timestamp
        )
        
        transaction_id = self.db.execute_query(query, params)
        
        return transaction_id
    
    def get_transaction(self, transaction_id):
        """Get a specific transaction by ID"""
        query = "SELECT * FROM transactions WHERE transaction_id = ?"
        transaction = self.db.execute_query(query, (transaction_id,), "one")
        
        return dict(transaction) if transaction else None
    
    def get_account_transactions(self, account_id, limit=50, offset=0, transaction_type=None):
        """Get all transactions for a specific account"""
        # Build query
        query = "SELECT * FROM transactions WHERE account_id = ?"
        params = [account_id]
        
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type)
        
        query += " ORDER BY transaction_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        transactions = self.db.execute_query(query, tuple(params), "all")
        
        return [dict(t) for t in transactions] if transactions else []
    
    def get_transaction_stats(self, account_id=None, start_date=None, end_date=None):
        """Get statistics on transactions for reporting"""
        # Build query
        query = """
            SELECT 
                transaction_type,
                COUNT(*) as count, 
                SUM(amount) as total,
                AVG(amount) as average,
                MIN(amount) as minimum,
                MAX(amount) as maximum
            FROM transactions
            WHERE 1=1
        """
        params = []
        
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        
        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date)
        
        query += " GROUP BY transaction_type"
        
        # Execute query
        stats = self.db.execute_query(query, tuple(params), "all")
        
        return [dict(s) for s in stats] if stats else []
    
    def search_transactions(self, account_id=None, transaction_type=None, min_amount=None, 
                          max_amount=None, start_date=None, end_date=None, 
                          description_contains=None, limit=50, offset=0):
        """Search for transactions with various filters"""
        # Build query
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type)
        
        if min_amount is not None:
            query += " AND amount >= ?"
            params.append(min_amount)
        
        if max_amount is not None:
            query += " AND amount <= ?"
            params.append(max_amount)
        
        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date)
        
        if description_contains:
            query += " AND description LIKE ?"
            params.append(f"%{description_contains}%")
        
        query += " ORDER BY transaction_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        transactions = self.db.execute_query(query, tuple(params), "all")
        
        return [dict(t) for t in transactions] if transactions else []
