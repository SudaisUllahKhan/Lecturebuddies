import sqlite3
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "lecturebuddies.db")

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # User activity table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER PRIMARY KEY,
            study_sessions INTEGER DEFAULT 0,
            quizzes_created INTEGER DEFAULT 0,
            recordings_count INTEGER DEFAULT 0,
            flashcards_created INTEGER DEFAULT 0,
            notes_count INTEGER DEFAULT 0,
            total_study_time INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Recordings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            duration INTEGER,
            transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Quizzes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            num_questions INTEGER,
            difficulty TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Password reset tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Check for schema updates (migrations)
    try:
        # Check if display_name exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'display_name' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
            print("Migrated database: Added display_name column")
    except Exception as e:
        print(f"Migration error: {e}")
    
    conn.commit()
    conn.close()

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_user(username: str, password: str, email: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new user account
    Returns: (success, message, user_id)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Username already exists", None
        
        # Check if email already exists (if provided)
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                return False, "Email already exists", None
        
        # Create user
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        
        # Initialize user activity
        cursor.execute(
            "INSERT INTO user_activity (user_id) VALUES (?)",
            (user_id,)
        )
        
        conn.commit()
        conn.close()
        
        return True, "Account created successfully", user_id
        
    except Exception as e:
        return False, f"Error creating account: {str(e)}", None

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[int]]:
    """
    Authenticate a user
    Returns: (success, message, user_id)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Invalid username or password", None
        
        user_id, password_hash = result
        
        if verify_password(password, password_hash):
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), user_id)
            )
            conn.commit()
            conn.close()
            return True, "Login successful", user_id
        else:
            conn.close()
            return False, "Invalid username or password", None
            
    except Exception as e:
        return False, f"Error during login: {str(e)}", None

def get_user_id_by_username(username: str) -> Optional[int]:
    """Get user ID from username"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result["id"] if result else None
    except Exception as e:
        print(f"Error fetching user ID: {e}")
        return None

def get_user_stats(user_id: int) -> Dict:
    """
    Get user statistics for dashboard
    Returns: dict with activity counts
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM user_activity WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "study_sessions": result["study_sessions"],
                "quizzes_created": result["quizzes_created"],
                "recordings_count": result["recordings_count"],
                "flashcards_created": result["flashcards_created"],
                "notes_count": result["notes_count"],
                "total_study_time": result["total_study_time"]
            }
        else:
            # Return zeros if no activity yet
            return {
                "study_sessions": 0,
                "quizzes_created": 0,
                "recordings_count": 0,
                "flashcards_created": 0,
                "notes_count": 0,
                "total_study_time": 0
            }
            
    except Exception as e:
        print(f"Error fetching user stats: {e}")
        return {
            "study_sessions": 0,
            "quizzes_created": 0,
            "recordings_count": 0,
            "flashcards_created": 0,
            "notes_count": 0,
            "total_study_time": 0
        }

def increment_activity(user_id: int, activity_type: str, amount: int = 1):
    """
    Increment a specific activity counter
    activity_type: 'study_sessions', 'quizzes_created', 'recordings_count', 'flashcards_created', 'notes_count'
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Validate activity type
        valid_types = ['study_sessions', 'quizzes_created', 'recordings_count', 'flashcards_created', 'notes_count', 'total_study_time']
        if activity_type not in valid_types:
            conn.close()
            return False
        
        cursor.execute(
            f"UPDATE user_activity SET {activity_type} = {activity_type} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error incrementing activity: {e}")
        return False

def save_recording(user_id: int, filename: str, transcript: str = "", duration: int = 0) -> bool:
    """Save a recording to the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO recordings (user_id, filename, duration, transcript) VALUES (?, ?, ?, ?)",
            (user_id, filename, duration, transcript)
        )
        
        conn.commit()
        conn.close()
        
        # Increment recordings count
        increment_activity(user_id, 'recordings_count')
        
        return True
        
    except Exception as e:
        print(f"Error saving recording: {e}")
        return False

def save_quiz(user_id: int, title: str, num_questions: int, difficulty: str, content: str) -> bool:
    """Save a quiz to the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO quizzes (user_id, title, num_questions, difficulty, content) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, num_questions, difficulty, content)
        )
        
        conn.commit()
        conn.close()
        
        # Increment quizzes count
        increment_activity(user_id, 'quizzes_created')
        
        return True
        
    except Exception as e:
        print(f"Error saving quiz: {e}")
        return False

def get_user_recordings(user_id: int) -> List[Dict]:
    """Get all recordings for a user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM recordings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error fetching recordings: {e}")
        return []

def get_user_quizzes(user_id: int) -> List[Dict]:
    """Get all quizzes for a user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM quizzes WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
        
    except Exception as e:
        print(f"Error fetching quizzes: {e}")
        return []

def update_user_profile(user_id: int, display_name: Optional[str] = None, new_password: Optional[str] = None) -> Tuple[bool, str]:
    """Update user profile information"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if display_name is not None:
            updates.append("display_name = ?")
            params.append(display_name)
            
        if new_password:
            password_hash = hash_password(new_password)
            updates.append("password_hash = ?")
            params.append(password_hash)
            
        if not updates:
            conn.close()
            return True, "No changes made"
            
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return True, "Profile updated successfully"
        
    except Exception as e:
        return False, f"Error updating profile: {str(e)}"

def get_full_user_data(user_id: int) -> Dict:
    """Get all data associated with a user for export"""
    data = {"exported_at": datetime.now().isoformat()}
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # User Info
        cursor.execute("SELECT username, email, display_name, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            data["profile"] = dict(user)
            
        # Stats
        data["stats"] = get_user_stats(user_id)
        
        # Recordings
        data["recordings"] = get_user_recordings(user_id)
        
        # Quizzes
        data["quizzes"] = get_user_quizzes(user_id)
        
        conn.close()
        return data
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        return {}

def delete_user_account(user_id: int) -> Tuple[bool, str]:
    """Permanently delete user account and all data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete related data first (foreign keys might enforce this, but good to be explicit)
        cursor.execute("DELETE FROM user_activity WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM recordings WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM quizzes WHERE user_id = ?", (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        return True, "Account deleted successfully"
        
    except Exception as e:
        return False, f"Error deleting account: {str(e)}"

# Initialize database on module import
init_database()
