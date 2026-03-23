"""
Token Storage Management
Provides secure token persistent storage with expiration and rate limiting support
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json


class TokenStorage:
    """Secure token storage system"""

    def __init__(self, db_path: str = "data/tokens.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    token_hash TEXT PRIMARY KEY,
                    token_type TEXT NOT NULL,  -- 'admin' or 'access'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    device_fingerprint TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    device_fingerprint TEXT,
                    attempt_type TEXT NOT NULL,  -- 'admin' or 'access'
                    success INTEGER DEFAULT 0,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tokens_expires ON tokens(expires_at);
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address, attempted_at);
            """)

    def create_token(
        self,
        token_type: str,
        device_fingerprint: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_in_hours: int = 24,
    ) -> str:
        """Create new token"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tokens (token_hash, token_type, expires_at, 
                                  device_fingerprint, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    token_hash,
                    token_type,
                    expires_at,
                    device_fingerprint,
                    user_agent,
                    ip_address,
                ),
            )

        return token

    def validate_token(self, token: str, token_type: Optional[str] = None) -> bool:
        """Validate token validity"""
        if not token:
            return False

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT expires_at, is_active FROM tokens 
                WHERE token_hash = ? AND is_active = 1
            """,
                (token_hash,),
            )

            result = cursor.fetchone()
            if not result:
                return False

            expires_at_str, is_active = result
            if not is_active:
                return False

            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Token expired, mark as inactive
                conn.execute(
                    "UPDATE tokens SET is_active = 0 WHERE token_hash = ?",
                    (token_hash,),
                )
                return False

            # Update last used time
            conn.execute(
                """
                UPDATE tokens SET last_used = CURRENT_TIMESTAMP 
                WHERE token_hash = ?
            """,
                (token_hash,),
            )

            return True

    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        if not token:
            return False

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE tokens SET is_active = 0 
                WHERE token_hash = ? AND is_active = 1
            """,
                (token_hash,),
            )
            return cursor.rowcount > 0

    def revoke_all_tokens(self, token_type: Optional[str] = None) -> int:
        """Revoke all tokens or tokens of specific type"""
        with sqlite3.connect(self.db_path) as conn:
            if token_type:
                cursor = conn.execute(
                    """
                    UPDATE tokens SET is_active = 0 
                    WHERE token_type = ? AND is_active = 1
                """,
                    (token_type,),
                )
            else:
                cursor = conn.execute(
                    "UPDATE tokens SET is_active = 0 WHERE is_active = 1"
                )
            return cursor.rowcount

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE tokens SET is_active = 0 
                WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
            """)
            return cursor.rowcount

    def get_token_info(self, token: str) -> Optional[Dict]:
        """Get token information"""
        if not token:
            return None

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT token_type, created_at, expires_at, last_used,
                       device_fingerprint, user_agent, ip_address, is_active
                FROM tokens WHERE token_hash = ?
            """,
                (token_hash,),
            )

            result = cursor.fetchone()
            if not result:
                return None

            return {
                "token_type": result[0],
                "created_at": result[1],
                "expires_at": result[2],
                "last_used": result[3],
                "device_fingerprint": result[4],
                "user_agent": result[5],
                "ip_address": result[6],
                "is_active": bool(result[7]),
            }

    def record_login_attempt(
        self,
        ip_address: str,
        device_fingerprint: Optional[str],
        attempt_type: str,
        success: bool,
        user_agent: Optional[str] = None,
    ):
        """Record login attempt"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO login_attempts 
                (ip_address, device_fingerprint, attempt_type, success, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    ip_address,
                    device_fingerprint,
                    attempt_type,
                    int(success),
                    user_agent,
                ),
            )

    def check_rate_limit(
        self,
        ip_address: str,
        attempt_type: str,
        max_attempts: int = 5,
        time_window_minutes: int = 15,
    ) -> bool:
        """Check if login attempt limit exceeded"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = ? AND attempt_type = ? AND success = 0
                AND attempted_at > datetime('now', '-' || ? || ' minutes')
            """,
                (ip_address, attempt_type, time_window_minutes),
            )

            failed_attempts = cursor.fetchone()[0]
            return failed_attempts < max_attempts

    def get_login_stats(
        self, ip_address: str, attempt_type: str, time_window_hours: int = 24
    ) -> Dict:
        """Get login statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(success) as successful_attempts,
                    COUNT(*) - SUM(success) as failed_attempts,
                    MAX(attempted_at) as last_attempt
                FROM login_attempts 
                WHERE ip_address = ? AND attempt_type = ?
                AND attempted_at > datetime('now', '-' || ? || ' hours')
            """,
                (ip_address, attempt_type, time_window_hours),
            )

            result = cursor.fetchone()
            return {
                "total_attempts": result[0] or 0,
                "successful_attempts": result[1] or 0,
                "failed_attempts": result[2] or 0,
                "last_attempt": result[3],
            }


# Global token storage instance
token_storage = TokenStorage()


def get_token_storage() -> TokenStorage:
    """Get token storage instance"""
    return token_storage
