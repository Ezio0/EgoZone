"""
Login Rate Limiter - Prevents brute force attacks
"""

import time
import sqlite3
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json


class LoginAttempt:
    """Login attempt record"""

    def __init__(self, identifier: str, ip_address: str, success: bool = False):
        self.identifier = identifier  # Username or device fingerprint
        self.ip_address = ip_address
        self.timestamp = datetime.now()
        self.success = success
        self.count = 1


class RateLimiter:
    """Login rate limiter"""

    def __init__(self, db_path: str = "./data/rate_limiter.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Rate limiting configuration
        self.config = {
            "max_attempts_per_ip": 10,  # Max attempts per IP
            "max_attempts_per_user": 5,  # Max attempts per user
            "time_window_minutes": 15,  # Time window (minutes)
            "lockout_duration_minutes": 30,  # Lockout duration (minutes)
            "max_global_attempts": 100,  # Global max attempts
            "global_time_window_minutes": 5,  # Global time window
        }

        self._init_database()
        self._memory_cache: Dict[str, list] = {}
        self._lock = threading.Lock()

    def _init_database(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Login attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                success BOOLEAN NOT NULL DEFAULT FALSE,
                user_agent TEXT,
                device_fingerprint TEXT
            )
        """)

        # Lockouts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                locked_until DATETIME NOT NULL,
                reason TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_identifier ON login_attempts(identifier)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_ip ON login_attempts(ip_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON login_attempts(timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lockouts_identifier ON lockouts(identifier)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lockouts_ip ON lockouts(ip_address)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_lockouts_locked_until ON lockouts(locked_until)"
        )

        conn.commit()
        conn.close()

    def record_attempt(
        self,
        identifier: str,
        ip_address: str,
        success: bool = False,
        user_agent: str = None,
        device_fingerprint: str = None,
    ):
        """Record login attempt"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO login_attempts 
                    (identifier, ip_address, timestamp, success, user_agent, device_fingerprint)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        identifier,
                        ip_address,
                        datetime.now(),
                        success,
                        user_agent,
                        device_fingerprint,
                    ),
                )

                conn.commit()

                # Clean up expired records (keep 7 days)
                cutoff_date = datetime.now() - timedelta(days=7)
                cursor.execute(
                    "DELETE FROM login_attempts WHERE timestamp < ?", (cutoff_date,)
                )
                conn.commit()

            finally:
                conn.close()

    def is_locked(self, identifier: str, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Check if locked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()

            # Check user lockout
            cursor.execute(
                """
                SELECT locked_until, reason FROM lockouts 
                WHERE identifier = ? AND locked_until > ?
                ORDER BY locked_until DESC LIMIT 1
            """,
                (identifier, now),
            )

            user_lock = cursor.fetchone()
            if user_lock:
                return True, f"User locked: {user_lock[1]}"

            # Check IP lockout
            cursor.execute(
                """
                SELECT locked_until, reason FROM lockouts 
                WHERE ip_address = ? AND locked_until > ?
                ORDER BY locked_until DESC LIMIT 1
            """,
                (ip_address, now),
            )

            ip_lock = cursor.fetchone()
            if ip_lock:
                return True, f"IP locked: {ip_lock[1]}"

            return False, None

        finally:
            conn.close()

    def check_rate_limit(self, identifier: str, ip_address: str) -> Tuple[bool, str]:
        """Check if rate limit exceeded"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            time_window_start = now - timedelta(
                minutes=self.config["time_window_minutes"]
            )

            # Check user attempt count
            cursor.execute(
                """
                SELECT COUNT(*) FROM login_attempts 
                WHERE identifier = ? AND timestamp > ? AND success = FALSE
            """,
                (identifier, time_window_start),
            )

            user_attempts = cursor.fetchone()[0]

            # Check IP attempt count
            cursor.execute(
                """
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = ? AND timestamp > ? AND success = FALSE
            """,
                (ip_address, time_window_start),
            )

            ip_attempts = cursor.fetchone()[0]

            # Check global attempt count
            global_window_start = now - timedelta(
                minutes=self.config["global_time_window_minutes"]
            )
            cursor.execute(
                """
                SELECT COUNT(*) FROM login_attempts 
                WHERE timestamp > ? AND success = FALSE
            """,
                (global_window_start,),
            )

            global_attempts = cursor.fetchone()[0]

            # Determine if lockout needed
            if user_attempts >= self.config["max_attempts_per_user"]:
                self._lock_identifier(identifier, ip_address, "Too many user attempts")
                return (
                    False,
                    f"Too many user attempts ({user_attempts}), locked for {self.config['lockout_duration_minutes']} minutes",
                )

            if ip_attempts >= self.config["max_attempts_per_ip"]:
                self._lock_ip(identifier, ip_address, "Too many IP attempts")
                return (
                    False,
                    f"Too many IP attempts ({ip_attempts}), locked for {self.config['lockout_duration_minutes']} minutes",
                )

            if global_attempts >= self.config["max_global_attempts"]:
                return False, f"System busy, please try again later"

            # Return remaining attempt count
            remaining_user = self.config["max_attempts_per_user"] - user_attempts
            remaining_ip = self.config["max_attempts_per_ip"] - ip_attempts
            remaining = min(remaining_user, remaining_ip)

            if remaining <= 3:
                return True, f"Warning: {remaining} attempts remaining"

            return True, "Login allowed"

        finally:
            conn.close()

    def _lock_identifier(self, identifier: str, ip_address: str, reason: str):
        """Lock user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            locked_until = datetime.now() + timedelta(
                minutes=self.config["lockout_duration_minutes"]
            )

            cursor.execute(
                """
                INSERT INTO lockouts (identifier, ip_address, locked_until, reason)
                VALUES (?, ?, ?, ?)
            """,
                (identifier, ip_address, locked_until, reason),
            )

            conn.commit()
            print(f"User {identifier} locked until {locked_until}, reason: {reason}")

        finally:
            conn.close()

    def _lock_ip(self, identifier: str, ip_address: str, reason: str):
        """Lock IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            locked_until = datetime.now() + timedelta(
                minutes=self.config["lockout_duration_minutes"]
            )

            cursor.execute(
                """
                INSERT INTO lockouts (identifier, ip_address, locked_until, reason)
                VALUES (?, ?, ?, ?)
            """,
                (identifier, ip_address, locked_until, reason),
            )

            conn.commit()
            print(f"IP {ip_address} locked until {locked_until}, reason: {reason}")

        finally:
            conn.close()

    def get_attempt_stats(self, identifier: str, ip_address: str) -> Dict:
        """Get attempt statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()
            time_window_start = now - timedelta(
                minutes=self.config["time_window_minutes"]
            )

            # User statistics
            cursor.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END)
                FROM login_attempts 
                WHERE identifier = ? AND timestamp > ?
            """,
                (identifier, time_window_start),
            )

            user_stats = cursor.fetchone()

            # IP statistics
            cursor.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END)
                FROM login_attempts 
                WHERE ip_address = ? AND timestamp > ?
            """,
                (ip_address, time_window_start),
            )

            ip_stats = cursor.fetchone()

            # Check lockout status
            is_locked, lock_reason = self.is_locked(identifier, ip_address)

            return {
                "user_attempts": user_stats[0] if user_stats else 0,
                "user_successes": user_stats[1] if user_stats and user_stats[1] else 0,
                "ip_attempts": ip_stats[0] if ip_stats else 0,
                "ip_successes": ip_stats[1] if ip_stats and ip_stats[1] else 0,
                "is_locked": is_locked,
                "lock_reason": lock_reason,
                "max_attempts_per_user": self.config["max_attempts_per_user"],
                "max_attempts_per_ip": self.config["max_attempts_per_ip"],
                "time_window_minutes": self.config["time_window_minutes"],
            }

        finally:
            conn.close()

    def cleanup_old_records(self):
        """Clean up old records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clean up expired lockout records
            now = datetime.now()
            cursor.execute("DELETE FROM lockouts WHERE locked_until < ?", (now,))
            deleted_lockouts = cursor.rowcount

            # Clean up expired attempt records (keep 30 days)
            cutoff_date = now - timedelta(days=30)
            cursor.execute(
                "DELETE FROM login_attempts WHERE timestamp < ?", (cutoff_date,)
            )
            deleted_attempts = cursor.rowcount

            conn.commit()

            print(
                f"Cleanup complete: deleted {deleted_lockouts} expired lockout records, {deleted_attempts} expired attempt records"
            )

        finally:
            conn.close()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_login_rate_limit(identifier: str, ip_address: str) -> Tuple[bool, str]:
    """Check login rate limit"""
    limiter = get_rate_limiter()

    # Check if locked
    is_locked, lock_reason = limiter.is_locked(identifier, ip_address)
    if is_locked:
        return False, lock_reason

    # Check rate limit
    allowed, message = limiter.check_rate_limit(identifier, ip_address)
    return allowed, message


def record_login_attempt(
    identifier: str,
    ip_address: str,
    success: bool = False,
    user_agent: str = None,
    device_fingerprint: str = None,
):
    """Record login attempt"""
    limiter = get_rate_limiter()
    limiter.record_attempt(
        identifier, ip_address, success, user_agent, device_fingerprint
    )


def get_login_stats(identifier: str, ip_address: str) -> Dict:
    """Get login statistics"""
    limiter = get_rate_limiter()
    return limiter.get_attempt_stats(identifier, ip_address)


def cleanup_rate_limit_data():
    """Clean up rate limit data"""
    limiter = get_rate_limiter()
    limiter.cleanup_old_records()


if __name__ == "__main__":
    # Test rate limiter
    limiter = RateLimiter()

    # Simulate some login attempts
    test_ip = "192.168.1.100"
    test_user = "test_user"

    print("Testing rate limiter...")

    # Successful login
    allowed, message = check_login_rate_limit(test_user, test_ip)
    print(f"First attempt: {allowed}, {message}")
    record_login_attempt(test_user, test_ip, success=True)

    # Multiple failed attempts
    for i in range(6):
        allowed, message = check_login_rate_limit(test_user, test_ip)
        print(f"Failed attempt {i + 1}: {allowed}, {message}")
        if allowed:
            record_login_attempt(test_user, test_ip, success=False)

    # Check statistics
    stats = get_login_stats(test_user, test_ip)
    print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")

    # Cleanup data
    cleanup_rate_limit_data()
