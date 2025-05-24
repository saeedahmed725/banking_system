import os
import tempfile
import sqlite3
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database


class DatabaseHelper(Database):
    """Test database class that uses a temporary database for testing"""
    
    def __init__(self, db_path=None):
        """Initialize test database with a temporary file"""
        if db_path is None:
            # Create a temporary database file
            fd, self._test_db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)  # Close the file descriptor
            db_path = self._test_db_path
        
        # Initialize counter for this specific database instance
        self._account_counter = 10000 + hash(db_path) % 100000  # Unique starting point
        
        super().__init__(db_path)
        
    def generate_account_number(self):
        """Generate a unique account number for testing"""
        self._account_counter += 1
        return f"TEST{self._account_counter:06d}"
    
    def cleanup_test_db(self):
        """Clean up the test database file"""
        if hasattr(self, '_test_db_path') and os.path.exists(self._test_db_path):
            try:
                os.unlink(self._test_db_path)
            except Exception:
                pass  # Ignore cleanup errors


def setup_test_database():
    """Set up a fresh test database"""
    test_db = DatabaseHelper()
    test_db.initialize_database()
    return test_db


def cleanup_test_database():
    """Clean up test database"""
    # This is now handled by individual DatabaseHelper instances
    pass
