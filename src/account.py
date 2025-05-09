from src.database import Database


class AccountManager:
    """Handle operations related to bank accounts"""
    
    def __init__(self, db=None):
        """Initialize with a database connection"""
        self.db = db if db else Database()
    
    def create_account(self, owner_name, account_type, email=None, phone_number=None, initial_balance=0.0):
        """Create a new bank account"""
        # Validate input
        if not owner_name:
            raise ValueError("Owner name is required")
        
        valid_account_types = ['checking', 'savings', 'business', 'loan', 'money_market', 'certificate_of_deposit']
        if account_type not in valid_account_types:
            raise ValueError(f"Invalid account type. Must be one of: {', '.join(valid_account_types)}")
        
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        
        # Generate account number
        account_number = self.db.generate_account_number()
        
        # Get current timestamp
        current_time = self.db.get_current_timestamp()
        
        # Insert account record
        query = """
            INSERT INTO accounts (
                account_number, owner_name, account_type, 
                email, phone_number, balance, created_at, updated_at
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            account_number, owner_name, account_type,
            email, phone_number, initial_balance, current_time, current_time
        )
        
        try:
            account_id = self.db.execute_query(query, params)
            
            # Return the newly created account
            return self.get_account(account_id)
        except Exception as e:
            raise Exception(f"Error creating account: {e}")
    
    def get_account(self, account_id):
        """Get account by ID"""
        query = "SELECT * FROM accounts WHERE account_id = ?"
        account = self.db.execute_query(query, (account_id,), 'one')
        
        if account:
            return dict(account)
        return None
    
    def get_account_by_number(self, account_number):
        """Get account by account number"""
        query = "SELECT * FROM accounts WHERE account_number = ?"
        account = self.db.execute_query(query, (account_number,), 'one')
        
        if account:
            return dict(account)
        return None
    
    def get_all_accounts(self):
        """Get all accounts in the system"""
        query = "SELECT * FROM accounts ORDER BY created_at DESC"
        accounts = self.db.execute_query(query, fetch_mode='all')
        
        return [dict(account) for account in accounts] if accounts else []
    
    def search_accounts(self, **kwargs):
        """Search for accounts with various filters"""
        # Start with base query
        query = "SELECT * FROM accounts WHERE 1=1"
        params = []
        
        # Add filters based on provided kwargs
        if 'owner_name_contains' in kwargs:
            query += " AND owner_name LIKE ?"
            params.append(f"%{kwargs['owner_name_contains']}%")
        
        if 'account_type' in kwargs:
            query += " AND account_type = ?"
            params.append(kwargs['account_type'])
        
        if 'email_contains' in kwargs:
            query += " AND email LIKE ?"
            params.append(f"%{kwargs['email_contains']}%")
        
        if 'min_balance' in kwargs:
            query += " AND balance >= ?"
            params.append(kwargs['min_balance'])
        
        if 'max_balance' in kwargs:
            query += " AND balance <= ?"
            params.append(kwargs['max_balance'])
        
        if 'created_after' in kwargs:
            query += " AND created_at >= ?"
            params.append(kwargs['created_after'])
        
        if 'created_before' in kwargs:
            query += " AND created_at <= ?"
            params.append(kwargs['created_before'])
        
        # Add ordering
        query += " ORDER BY created_at DESC"
        
        # Execute the query
        accounts = self.db.execute_query(query, tuple(params), 'all')
        
        return [dict(account) for account in accounts] if accounts else []
    
    def update_account(self, account_id, **kwargs):
        """Update account details"""
        # Check if account exists
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Fields that can be updated
        valid_fields = ['owner_name', 'email', 'phone_number', 'account_type']
        
        # Prepare update query
        update_fields = []
        params = []
        
        for field, value in kwargs.items():
            if field in valid_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        # If no valid fields to update
        if not update_fields:
            return account
        
        # Add updated_at timestamp
        update_fields.append("updated_at = ?")
        params.append(self.db.get_current_timestamp())
        
        # Add account_id to params
        params.append(account_id)
        
        # Execute update query
        query = f"UPDATE accounts SET {', '.join(update_fields)} WHERE account_id = ?"
        self.db.execute_query(query, tuple(params))
        
        # Return updated account
        return self.get_account(account_id)
    
    def update_balance(self, account_id, new_balance):
        """Update account balance"""
        # Validate input
        if new_balance < 0:
            raise ValueError("Account balance cannot be negative")
        
        # Check if account exists
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Update balance
        query = "UPDATE accounts SET balance = ?, updated_at = ? WHERE account_id = ?"
        params = (new_balance, self.db.get_current_timestamp(), account_id)
        
        self.db.execute_query(query, params)
        
        # Return updated account
        return self.get_account(account_id)
    
    def close_account(self, account_id):
        """Close and delete an account"""
        # Check if account exists
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Check if account has zero balance
        if account['balance'] != 0:
            raise ValueError("Account must have zero balance before closing")
        
        # Check if account has any active loans
        query = "SELECT COUNT(*) as count FROM loans WHERE account_id = ? AND status IN ('pending', 'active')"
        result = self.db.execute_query(query, (account_id,), 'one')
        
        if result and result['count'] > 0:
            raise ValueError("Cannot close account with active loans")
        
        # Delete account (cascade will delete related transactions)
        query = "DELETE FROM accounts WHERE account_id = ?"
        self.db.execute_query(query, (account_id,))
        
        return True
    
    def get_account_summary(self, account_id):
        """Get a summary of account activity"""
        # Check if account exists
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")
        
        # Get transaction summary by type
        query = """
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM transactions
            WHERE account_id = ?
            GROUP BY transaction_type
        """
        transaction_summary = self.db.execute_query(query, (account_id,), 'all')
        
        # Get recent transactions
        query = """
            SELECT * FROM transactions
            WHERE account_id = ?
            ORDER BY transaction_date DESC
            LIMIT 10
        """
        recent_transactions = self.db.execute_query(query, (account_id,), 'all')
        
        # Get loan summary
        query = """
            SELECT COUNT(*) as count, SUM(remaining_amount) as total_remaining
            FROM loans
            WHERE account_id = ? AND status = 'active'
        """
        loan_summary = self.db.execute_query(query, (account_id,), 'one')
        
        return {
            'account': account,
            'transaction_summary': [dict(t) for t in transaction_summary] if transaction_summary else [],
            'recent_transactions': [dict(t) for t in recent_transactions] if recent_transactions else [],
            'loan_summary': dict(loan_summary) if loan_summary else {'count': 0, 'total_remaining': 0}
        }