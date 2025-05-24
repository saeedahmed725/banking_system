import hashlib
import datetime
from src.database import Database


class UserManager:
    """Manages user authentication and user accounts"""
    
    def __init__(self, db_path=None):
        self.db = Database(db_path)
        self.initialize_users_table()
        self.create_default_admin()
    
    def initialize_users_table(self):
        """Create users table if it doesn't exist"""
        query = '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                user_type TEXT NOT NULL DEFAULT 'customer',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP NOT NULL,
                last_login TIMESTAMP,
                account_id INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE SET NULL
            )
        '''
        try:
            self.db.execute_query(query)
        except Exception as e:
            print(f"Error creating users table: {e}")
    
    def create_default_admin(self):
        """Create default admin user if it doesn't exist"""
        try:
            # Check if admin already exists
            admin = self.get_user_by_username('admin')
            if not admin:
                # Create default admin with password 'admin123'
                self.create_user(
                    username='admin',
                    password='admin123',
                    email='admin@bankingsystem.com',
                    full_name='System Administrator',
                    user_type='admin'
                )
                print("Default admin user created (username: admin, password: admin123)")
        except Exception as e:
            print(f"Error creating default admin: {e}")
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, password_hash):
        """Verify password against hash"""
        return self.hash_password(password) == password_hash
    
    def create_user(self, username, password, email, full_name, user_type='customer', account_id=None):
        """Create a new user"""
        password_hash = self.hash_password(password)
        created_at = datetime.datetime.now()
        
        query = '''
            INSERT INTO users (username, password_hash, email, full_name, user_type, created_at, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (username, password_hash, email, full_name, user_type, created_at, account_id)
        
        try:
            user_id = self.db.execute_query(query, params)
            return self.get_user_by_id(user_id)
        except Exception as e:
            raise Exception(f"Error creating user: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        user = self.get_user_by_username(username)
        if user and user['is_active'] and self.verify_password(password, user['password_hash']):
            # Update last login
            self.update_last_login(user['user_id'])
            return user
        return None
    
    def get_user_by_username(self, username):
        """Get user by username"""
        query = "SELECT * FROM users WHERE username = ?"
        try:
            return self.db.execute_query(query, (username,), fetch_mode='one')
        except Exception as e:
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        query = "SELECT * FROM users WHERE user_id = ?"
        try:
            return self.db.execute_query(query, (user_id,), fetch_mode='one')
        except Exception as e:
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = ?"
        try:
            return self.db.execute_query(query, (email,), fetch_mode='one')
        except Exception as e:
            return None
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        query = "UPDATE users SET last_login = ? WHERE user_id = ?"
        last_login = datetime.datetime.now()
        try:
            self.db.execute_query(query, (last_login, user_id))
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    def link_user_to_account(self, user_id, account_id):
        """Link a user to a bank account"""
        query = "UPDATE users SET account_id = ? WHERE user_id = ?"
        try:
            self.db.execute_query(query, (account_id, user_id))
            return True
        except Exception as e:
            raise Exception(f"Error linking user to account: {e}")
    
    def get_all_users(self):
        """Get all users (admin only)"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        try:
            return self.db.execute_query(query, fetch_mode='all')
        except Exception as e:
            return []
    
    def deactivate_user(self, user_id):
        """Deactivate a user account"""
        query = "UPDATE users SET is_active = 0 WHERE user_id = ?"
        try:
            self.db.execute_query(query, (user_id,))
            return True
        except Exception as e:
            raise Exception(f"Error deactivating user: {e}")
    
    def activate_user(self, user_id):
        """Activate a user account"""
        query = "UPDATE users SET is_active = 1 WHERE user_id = ?"
        try:
            self.db.execute_query(query, (user_id,))
            return True
        except Exception as e:
            raise Exception(f"Error activating user: {e}")
