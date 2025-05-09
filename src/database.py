import sqlite3
import datetime
import os
from pathlib import Path


class Database:
    """Handle database operations for the banking system"""
    
    def __init__(self, db_path=None):
        """Initialize with a database path"""
        if db_path is None:
            # Default to the data directory in the project root
            self.db_path = Path(__file__).parent.parent / 'data' / 'banking.db'
        else:
            self.db_path = Path(db_path)
        
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.conn = None
        self.initialize_database()
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # Create accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number TEXT UNIQUE NOT NULL,
                    owner_name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    email TEXT,
                    phone_number TEXT,
                    balance REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            ''')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    transaction_date TIMESTAMP NOT NULL,
                    related_transaction_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE,
                    FOREIGN KEY (related_transaction_id) REFERENCES transactions(transaction_id)
                )
            ''')
            
            # Create loans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS loans (
                    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    loan_amount REAL NOT NULL,
                    interest_rate REAL NOT NULL,
                    term_months INTEGER NOT NULL,
                    remaining_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    application_date TIMESTAMP NOT NULL,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    last_payment_date TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Database initialization error: {e}")
        finally:
            self.close()
    
    def execute_query(self, query, params=(), fetch_mode=None):
        """
        Execute a database query
        
        Parameters:
        - query: SQL query to execute
        - params: Tuple of parameters for the query
        - fetch_mode: None for INSERT/UPDATE/DELETE, 'one' for fetchone, 'all' for fetchall
        
        Returns:
        - For INSERT: The ID of the inserted row
        - For SELECT: The fetched row(s)
        - For UPDATE/DELETE: The number of affected rows
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if fetch_mode == 'one':
                result = cursor.fetchone()
            elif fetch_mode == 'all':
                result = cursor.fetchall()
            else:
                # For INSERT, return the last inserted row ID
                if query.strip().upper().startswith('INSERT'):
                    result = cursor.lastrowid
                else:
                    # For UPDATE/DELETE, return the number of affected rows
                    result = cursor.rowcount
                
                conn.commit()
            
            return result
        except Exception as e:
            if conn and not fetch_mode:
                conn.rollback()
            raise Exception(f"Database query error: {e}")
        finally:
            self.close()
    
    def get_current_timestamp(self):
        """Get the current timestamp in a consistent format"""
        return datetime.datetime.now()
    
    def generate_account_number(self):
        """Generate a unique account number"""
        # Get current timestamp for uniqueness
        timestamp = int(datetime.datetime.now().timestamp())
        
        # Generate a 10-digit account number
        account_number = f"1000{timestamp % 10000000:07d}"
        
        return account_number
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if backup_path is None:
            # Default backup path
            backup_dir = Path(__file__).parent.parent / 'data' / 'backups'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a timestamp-based filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"banking_backup_{timestamp}.db"
        
        try:
            conn = self.connect()
            
            # Create a new database connection for the backup
            backup_conn = sqlite3.connect(backup_path)
            
            # Copy database to backup
            conn.backup(backup_conn)
            
            # Close backup connection
            backup_conn.close()
            
            return str(backup_path)
        except Exception as e:
            raise Exception(f"Database backup error: {e}")
        finally:
            self.close()
    
    def restore_database(self, backup_path):
        """Restore database from a backup"""
        if not os.path.exists(backup_path):
            raise ValueError(f"Backup file not found: {backup_path}")
        
        try:
            # Close any existing connections
            self.close()
            
            # Connect to the backup database
            backup_conn = sqlite3.connect(backup_path)
            
            # Connect to the target database
            conn = sqlite3.connect(self.db_path)
            
            # Copy from backup to the target database
            backup_conn.backup(conn)
            
            # Close connections
            backup_conn.close()
            conn.close()
            
            return True
        except Exception as e:
            raise Exception(f"Database restore error: {e}")
    
    def begin_transaction(self):
        """Begin a database transaction"""
        try:
            self.conn = self.connect()
            return self.conn
        except Exception as e:
            self.close()
            raise Exception(f"Error beginning transaction: {e}")
    
    def commit_transaction(self):
        """Commit the current transaction"""
        if self.conn:
            try:
                self.conn.commit()
            finally:
                self.close()
    
    def rollback_transaction(self):
        """Rollback the current transaction"""
        if self.conn:
            try:
                self.conn.rollback()
            finally:
                self.close()