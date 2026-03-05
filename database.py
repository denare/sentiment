"""
Database connection and operations
MySQL connector for Sentiment Analysis System
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime

class Database:
    """Database connection manager"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Create database connection"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',          # Change if MySQL is on another server
                user='root',               # Your MySQL username
                password='Denis@123',  # ⚠️ CHANGE THIS to your MySQL password
                database='sentiment_analysis',
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                print("✅ Connected to MySQL database")
                return True
                
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("Database connection closed")
    
    # ═══════════════════════════════════════════════════════════════════
    #  USER OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def create_user(self, fullname, username, email, password_hash):
        """Create new user account"""
        try:
            query = """
                INSERT INTO users (fullname, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (fullname, username, email, password_hash))
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_username_or_email(self, username_or_email):
        """Find user by username or email"""
        try:
            query = """
                SELECT * FROM users 
                WHERE (username = %s OR email = %s) AND is_active = TRUE
            """
            self.cursor.execute(query, (username_or_email, username_or_email))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            query = "SELECT * FROM users WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def update_last_login(self, user_id):
        """Update user's last login timestamp"""
        try:
            query = "UPDATE users SET last_login = NOW() WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating last login: {e}")
            return False
    
    def update_user_profile(self, user_id, fullname, email):
        """Update user profile information"""
        try:
            query = """
                UPDATE users 
                SET fullname = %s, email = %s 
                WHERE user_id = %s
            """
            self.cursor.execute(query, (fullname, email, user_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating profile: {e}")
            return False
    
    def update_password(self, user_id, new_password_hash):
        """Update user password"""
        try:
            query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
            self.cursor.execute(query, (new_password_hash, user_id))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error updating password: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════
    #  ANALYSIS OPERATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    def create_analysis(self, user_id, text_content, language, sentiment_result, confidence_score):
        """Create new analysis record"""
        try:
            query = """
                INSERT INTO analysis 
                (user_id, text_content, language, sentiment_result, confidence_score)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (user_id, text_content, language, 
                                       sentiment_result, confidence_score))
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Error creating analysis: {e}")
            return None
    
    def get_user_analyses(self, user_id, sentiment_filter='All', search_query='', 
                         page=1, per_page=20):
        """Get user's analysis history with filters and pagination"""
        try:
            offset = (page - 1) * per_page
            
            # Base query
            query = """
                SELECT * FROM analysis 
                WHERE user_id = %s
            """
            params = [user_id]
            
            # Apply sentiment filter
            if sentiment_filter != 'All':
                query += " AND sentiment_result = %s"
                params.append(sentiment_filter)
            
            # Apply search filter
            if search_query:
                query += " AND text_content LIKE %s"
                params.append(f"%{search_query}%")
            
            # Order and pagination
            query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error fetching analyses: {e}")
            return []
    
    def get_user_analyses_count(self, user_id, sentiment_filter='All', search_query=''):
        """Count total analyses for pagination"""
        try:
            query = "SELECT COUNT(*) as total FROM analysis WHERE user_id = %s"
            params = [user_id]
            
            if sentiment_filter != 'All':
                query += " AND sentiment_result = %s"
                params.append(sentiment_filter)
            
            if search_query:
                query += " AND text_content LIKE %s"
                params.append(f"%{search_query}%")
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result['total'] if result else 0
        except Error as e:
            print(f"Error counting analyses: {e}")
            return 0
    
    def get_user_statistics(self, user_id):
        """Get user's analysis statistics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_analyses,
                    SUM(CASE WHEN sentiment_result = 'Positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment_result = 'Negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment_result = 'Neutral' THEN 1 ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN DATE(timestamp) = CURDATE() THEN 1 ELSE 0 END) as today_count
                FROM analysis
                WHERE user_id = %s
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching statistics: {e}")
            return {
                'total_analyses': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'today_count': 0
            }
    
    # ═══════════════════════════════════════════════════════════════════
    #  DEMO DATA
    # ═══════════════════════════════════════════════════════════════════
    
    def create_demo_data(self, password_hash):
        """Create demo user and sample analyses"""
        try:
            # Check if demo user already exists
            demo_user = self.get_user_by_username_or_email('demo')
            if demo_user:
                print("✅ Demo user already exists")
                return demo_user['user_id']
            
            # Create demo user
            user_id = self.create_user(
                fullname='Demo User',
                username='demo',
                email='demo@example.com',
                password_hash=password_hash
            )
            
            if not user_id:
                print("❌ Failed to create demo user")
                return None
            
            # Create sample analyses
            samples = [
                ("This product is amazing! I love it so much.", "English", "Positive", 0.9123),
                ("Huduma hii ni mbaya sana, sijafurahi.", "Swahili", "Negative", 0.8756),
                ("The service was okay, nothing special.", "English", "Neutral", 0.6543),
                ("Napenda sana programu hii, ni nzuri!", "Swahili", "Positive", 0.8912),
            ]
            
            for text, lang, sentiment, confidence in samples:
                self.create_analysis(user_id, text, lang, sentiment, confidence)
            
            print(f"✅ Demo data created - User ID: {user_id}")
            return user_id
            
        except Error as e:
            print(f"Error creating demo data: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def test_connection():
    """Test database connection"""
    db = Database()
    if db.connection and db.connection.is_connected():
        print("✅ Database connection successful!")
        
        # Get database info
        db.cursor.execute("SELECT DATABASE()")
        result = db.cursor.fetchone()
        print(f"📊 Connected to database: {result['DATABASE()']}")
        
        # Show tables
        db.cursor.execute("SHOW TABLES")
        tables = db.cursor.fetchall()
        print(f"📋 Tables found: {len(tables)}")
        for table in tables:
            print(f"   - {list(table.values())[0]}")
        
        db.close()
        return True
    else:
        print("❌ Database connection failed!")
        return False


if __name__ == "__main__":
    # Test the connection
    test_connection()