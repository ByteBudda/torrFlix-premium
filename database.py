import sqlite3, os
from datetime import datetime, timedelta
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data.db')
CACHE_DIR = os.path.join(BASE_DIR, 'cache_img')
os.makedirs(CACHE_DIR, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tmdb_cache (
                url_hash TEXT PRIMARY KEY,
                url TEXT,
                response_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_tmdb_expires ON tmdb_cache(expires_at)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS magnet_cache (
                url TEXT PRIMARY KEY,
                magnet TEXT,
                expires_at TIMESTAMP
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_magnet_expires ON magnet_cache(expires_at)')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                approved BOOLEAN DEFAULT 0,
                email_verified BOOLEAN DEFAULT 0,
                avatar_url TEXT,
                reset_token TEXT,
                reset_token_expires TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tmdb_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                title TEXT NOT NULL,
                poster_path TEXT,
                vote_average REAL,
                year TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, tmdb_id, media_type),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        try:
            conn.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0')
        except: pass
        try:
            conn.execute('ALTER TABLE users ADD COLUMN avatar_url TEXT')
        except: pass
        try:
            conn.execute('ALTER TABLE users ADD COLUMN reset_token TEXT')
        except: pass
        try:
            conn.execute('ALTER TABLE users ADD COLUMN reset_token_expires TIMESTAMP')
        except: pass
        
        conn.execute('DELETE FROM tmdb_cache WHERE expires_at IS NOT NULL AND expires_at < datetime("now")')
        conn.execute('DELETE FROM magnet_cache WHERE expires_at IS NOT NULL AND expires_at < datetime("now")')
        conn.commit()

def get_db():
    return sqlite3.connect(DB_PATH)

def get_user_by_username(username: str):
    with get_db() as conn:
        try:
            cur = conn.execute('SELECT id, email, username, hashed_password, approved, email_verified, avatar_url, created_at FROM users WHERE username = ?', (username,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "hashed_password": row[3], "approved": bool(row[4]),
                    "email_verified": bool(row[5]) if len(row) > 5 else True,
                    "avatar_url": row[6] if len(row) > 6 else None,
                    "created_at": row[7] if len(row) > 7 else None
                }
        except:
            cur = conn.execute('SELECT id, email, username, hashed_password, approved, created_at FROM users WHERE username = ?', (username,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "hashed_password": row[3], "approved": bool(row[4]),
                    "email_verified": True, "avatar_url": None,
                    "created_at": row[5] if len(row) > 5 else None
                }
    return None

def get_user_by_id(user_id: int):
    with get_db() as conn:
        try:
            cur = conn.execute('SELECT id, email, username, approved, email_verified, avatar_url, created_at FROM users WHERE id = ?', (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "approved": bool(row[3]), "email_verified": bool(row[4]) if len(row) > 4 else True,
                    "avatar_url": row[5] if len(row) > 5 else None,
                    "created_at": row[6] if len(row) > 6 else None
                }
        except:
            cur = conn.execute('SELECT id, email, username, approved, created_at FROM users WHERE id = ?', (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "username": row[2],
                    "approved": bool(row[3]), "email_verified": True,
                    "avatar_url": None, "created_at": row[4] if len(row) > 4 else None
                }
    return None

def create_user(email: str, username: str, password: str) -> int:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    hashed = pwd_context.hash(password)
    
    with get_db() as conn:
        try:
            try:
                conn.execute('INSERT INTO users (email, username, hashed_password, email_verified) VALUES (?, ?, ?, 0)',
                             (email, username, hashed))
            except:
                conn.execute('INSERT INTO users (email, username, hashed_password) VALUES (?, ?, ?)',
                             (email, username, hashed))
            conn.commit()
            cursor = conn.execute('SELECT id FROM users WHERE username = ?', (username,))
            return cursor.fetchone()[0]
        except sqlite3.IntegrityError:
            return None

def verify_user_password(user_id: int, password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    with get_db() as conn:
        row = conn.execute('SELECT hashed_password FROM users WHERE id = ?', (user_id,)).fetchone()
        if not row: return False
        return pwd_context.verify(password, row[0])

def update_user_profile(user_id: int, email: str = None, avatar_url: str = None):
    with get_db() as conn:
        if email: conn.execute('UPDATE users SET email = ? WHERE id = ?', (email, user_id))
        if avatar_url: conn.execute('UPDATE users SET avatar_url = ? WHERE id = ?', (avatar_url, user_id))
        conn.commit()
        return True

def change_user_password(user_id: int, new_password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    with get_db() as conn:
        hashed = pwd_context.hash(new_password)
        conn.execute('UPDATE users SET hashed_password = ? WHERE id = ?', (hashed, user_id))
        conn.commit()
        return True

def create_verification_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=24)
    with get_db() as conn:
        conn.execute('DELETE FROM email_verifications WHERE user_id = ?', (user_id,))
        conn.execute('INSERT INTO email_verifications (user_id, token, expires_at) VALUES (?, ?, ?)', (user_id, token, expires_at.isoformat()))
        conn.commit()
    return token

def verify_email_token(token: str):
    with get_db() as conn:
        row = conn.execute('SELECT user_id, expires_at FROM email_verifications WHERE token = ?', (token,)).fetchone()
        if not row: return None
        user_id, expires_at = row
        if datetime.now() > datetime.fromisoformat(expires_at): return None
        conn.execute('UPDATE users SET email_verified = 1 WHERE id = ?', (user_id,))
        conn.execute('DELETE FROM email_verifications WHERE token = ?', (token,))
        conn.commit()
        return user_id

def create_reset_token(email: str):
    with get_db() as conn:
        row = conn.execute('SELECT id, username FROM users WHERE email = ?', (email,)).fetchone()
        if not row: return None
        user_id, username = row
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        conn.execute('UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?', (token, expires_at.isoformat(), user_id))
        conn.commit()
        return token, username

def reset_password_with_token(token: str, new_password: str) -> bool:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
    with get_db() as conn:
        row = conn.execute('SELECT id, reset_token_expires FROM users WHERE reset_token = ?', (token,)).fetchone()
        if not row: return False
        user_id, expires_at = row
        if datetime.now() > datetime.fromisoformat(expires_at): return False
        hashed = pwd_context.hash(new_password)
        conn.execute('UPDATE users SET hashed_password = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?', (hashed, user_id))
        conn.commit()
        return True

def add_favorite(user_id: int, tmdb_id: int, media_type: str, title: str, poster_path: str, vote_average: float, year: str):
    with get_db() as conn:
        try:
            conn.execute('INSERT INTO favorites (user_id, tmdb_id, media_type, title, poster_path, vote_average, year) VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, tmdb_id, media_type, title, poster_path, vote_average, year))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_favorite(user_id: int, tmdb_id: int, media_type: str):
    with get_db() as conn:
        conn.execute('DELETE FROM favorites WHERE user_id = ? AND tmdb_id = ? AND media_type = ?', (user_id, tmdb_id, media_type))
        conn.commit()
        return conn.total_changes > 0

def get_favorites(user_id: int):
    with get_db() as conn:
        rows = conn.execute('SELECT tmdb_id, media_type, title, poster_path, vote_average, year, added_at FROM favorites WHERE user_id = ? ORDER BY added_at DESC', (user_id,)).fetchall()
        return [{"tmdb_id": r[0], "media_type": r[1], "title": r[2], "poster_path": r[3], "vote_average": r[4], "year": r[5], "added_at": r[6]} for r in rows]

def check_favorite(user_id: int, tmdb_id: int, media_type: str):
    with get_db() as conn:
        row = conn.execute('SELECT id FROM favorites WHERE user_id = ? AND tmdb_id = ? AND media_type = ?', (user_id, tmdb_id, media_type)).fetchone()
        return row is not None