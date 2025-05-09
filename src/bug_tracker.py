import datetime
import logging
from pathlib import Path
from src.database import Database


class BugTracker:
    """Handle operations related to bug tracking and reporting"""
    
    def __init__(self, db=None, log_file=None):
        """Initialize the bug tracker"""
        self.db = db if db else Database()
        
        # Set up logging
        if log_file is None:
            self.log_file = Path(__file__).parent.parent / 'reports' / 'bug_reports.log'
        else:
            self.log_file = Path(log_file)
        
        # Create directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger('bug_tracker')
        self.logger.setLevel(logging.INFO)
        
        # Check if handlers already exist to avoid duplicates
        if not self.logger.handlers:
            # Create file handler
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
        
        # Create bugs table if it doesn't exist
        self._create_bugs_table()
    
    def _create_bugs_table(self):
        """Create bugs table if it doesn't exist"""
        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            
            # Create bugs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    module TEXT,
                    steps_to_reproduce TEXT,
                    status TEXT NOT NULL DEFAULT 'open',
                    reported_date TIMESTAMP NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    fixed_date TIMESTAMP,
                    closed_date TIMESTAMP,
                    comments TEXT
                )
            ''')
            
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Error creating bugs table: {e}")
            raise Exception(f"Error creating bugs table: {e}")
        finally:
            self.db.close()
    
    def report_bug(self, title, description, severity, module=None, steps_to_reproduce=None):
        """Report a new bug"""
        # Validate severity
        valid_severities = ['low', 'medium', 'high', 'critical']
        if severity not in valid_severities:
            raise ValueError(f"Invalid severity level. Must be one of: {', '.join(valid_severities)}")
        
        # Get current timestamp
        current_time = self.db.get_current_timestamp()
        
        # Insert bug record
        query = """
            INSERT INTO bugs (
                title, description, severity, module, 
                steps_to_reproduce, status, reported_date, last_updated
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            title, description, severity, module,
            steps_to_reproduce, 'open', current_time, current_time
        )
        
        try:
            bug_id = self.db.execute_query(query, params)
            
            # Log the bug report
            self.logger.info(f"Bug reported: ID={bug_id}, Title='{title}', Severity={severity}")
            
            # Return the newly created bug
            return self.get_bug(bug_id)
        except Exception as e:
            self.logger.error(f"Error reporting bug: {e}")
            raise Exception(f"Error reporting bug: {e}")
    
    def get_bug(self, bug_id):
        """Get bug by ID"""
        query = "SELECT * FROM bugs WHERE id = ?"
        bug = self.db.execute_query(query, (bug_id,), 'one')
        
        if bug:
            return dict(bug)
        return None
    
    def get_all_bugs(self, status=None):
        """Get all bugs, optionally filtered by status"""
        if status:
            query = "SELECT * FROM bugs WHERE status = ? ORDER BY reported_date DESC"
            bugs = self.db.execute_query(query, (status,), 'all')
        else:
            query = "SELECT * FROM bugs ORDER BY reported_date DESC"
            bugs = self.db.execute_query(query, fetch_mode='all')
        
        return [dict(bug) for bug in bugs] if bugs else []
    
    def update_bug_status(self, bug_id, new_status, comments=None):
        """Update the status of a bug"""
        # Validate status
        valid_statuses = ['open', 'in_progress', 'fixed', 'closed', 'reopened']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid bug status. Must be one of: {', '.join(valid_statuses)}")
        
        # Get current bug to check if it exists
        bug = self.get_bug(bug_id)
        if not bug:
            raise ValueError(f"Bug with ID {bug_id} not found")
        
        # Get current timestamp
        current_time = self.db.get_current_timestamp()
        
        # Prepare update query based on new status
        query = "UPDATE bugs SET status = ?, last_updated = ?"
        params = [new_status, current_time]
        
        # Add status-specific date fields
        if new_status == 'fixed' and bug['status'] != 'fixed':
            query += ", fixed_date = ?"
            params.append(current_time)
        
        if new_status == 'closed' and bug['status'] != 'closed':
            query += ", closed_date = ?"
            params.append(current_time)
        
        # Add comments if provided
        if comments:
            existing_comments = bug.get('comments', '')
            if existing_comments:
                new_comments = f"{existing_comments}\n\n[{current_time}] Status changed to {new_status.upper()}: {comments}"
            else:
                new_comments = f"[{current_time}] Status changed to {new_status.upper()}: {comments}"
            
            query += ", comments = ?"
            params.append(new_comments)
        
        # Add WHERE clause
        query += " WHERE id = ?"
        params.append(bug_id)
        
        # Execute update
        try:
            self.db.execute_query(query, tuple(params))
            
            # Log the status update
            status_change_msg = f"Bug {bug_id} status updated: {bug['status']} -> {new_status}"
            if comments:
                status_change_msg += f" | Comments: {comments}"
            self.logger.info(status_change_msg)
            
            # Return the updated bug
            return self.get_bug(bug_id)
        except Exception as e:
            self.logger.error(f"Error updating bug status: {e}")
            raise Exception(f"Error updating bug status: {e}")
    
    def search_bugs(self, **kwargs):
        """Search for bugs with various filters"""
        # Start with base query
        query = "SELECT * FROM bugs WHERE 1=1"
        params = []
        
        # Add filters based on provided kwargs
        if 'title_contains' in kwargs:
            query += " AND title LIKE ?"
            params.append(f"%{kwargs['title_contains']}%")
        
        if 'description_contains' in kwargs:
            query += " AND description LIKE ?"
            params.append(f"%{kwargs['description_contains']}%")
        
        if 'severity' in kwargs:
            query += " AND severity = ?"
            params.append(kwargs['severity'])
        
        if 'module' in kwargs:
            query += " AND module = ?"
            params.append(kwargs['module'])
        
        if 'status' in kwargs:
            query += " AND status = ?"
            params.append(kwargs['status'])
        
        if 'reported_after' in kwargs:
            query += " AND reported_date >= ?"
            params.append(kwargs['reported_after'])
        
        if 'reported_before' in kwargs:
            query += " AND reported_date <= ?"
            params.append(kwargs['reported_before'])
        
        # Add ordering
        query += " ORDER BY reported_date DESC"
        
        # Execute the query
        bugs = self.db.execute_query(query, tuple(params), 'all')
        
        return [dict(bug) for bug in bugs] if bugs else []
    
    def generate_bug_report(self, include_closed=False):
        """Generate a report of all bugs"""
        # Get all bugs, optionally excluding closed ones
        if not include_closed:
            bugs = self.search_bugs(status_not='closed')
        else:
            bugs = self.get_all_bugs()
        
        # Count bugs by severity
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for bug in bugs:
            severity = bug.get('severity')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Count bugs by status
        status_counts = {'open': 0, 'in_progress': 0, 'fixed': 0, 'closed': 0, 'reopened': 0}
        for bug in bugs:
            status = bug.get('status')
            if status in status_counts:
                status_counts[status] += 1
        
        # Count bugs by module
        module_counts = {}
        for bug in bugs:
            module = bug.get('module') or 'unknown'
            if module in module_counts:
                module_counts[module] += 1
            else:
                module_counts[module] = 1
        
        # Create report
        report = {
            'generated_at': self.db.get_current_timestamp(),
            'total_bugs': len(bugs),
            'severity_breakdown': severity_counts,
            'status_breakdown': status_counts,
            'module_breakdown': module_counts,
            'bugs': bugs
        }
        
        # Log report generation
        self.logger.info(f"Bug report generated with {len(bugs)} bugs")
        
        return report
    
    def log_test_error(self, test_name, error_message):
        """Log a test error directly to the log file"""
        self.logger.error(f"TEST FAILURE: {test_name} - {error_message}")
        
    def log_test_success(self, test_name):
        """Log a successful test directly to the log file"""
        self.logger.info(f"TEST SUCCESS: {test_name}")
        
    def get_recent_log_entries(self, count=50):
        """Get the most recent log entries"""
        try:
            with open(self.log_file, 'r') as log:
                lines = log.readlines()
                return lines[-count:] if len(lines) > count else lines
        except Exception as e:
            return [f"Error reading log file: {str(e)}"]