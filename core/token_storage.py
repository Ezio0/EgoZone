"""
令牌存储管理
提供安全的令牌持久化存储，支持过期机制和限流
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json


class TokenStorage:
    """安全的令牌存储系统"""
    
    def __init__(self, db_path: str = "data/tokens.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
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
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    device_fingerprint TEXT,
                    attempt_type TEXT NOT NULL,  -- 'admin' or 'access'
                    success INTEGER DEFAULT 0,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_expires ON tokens(expires_at);
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address, attempted_at);
            ''')
    
    def create_token(self, token_type: str, device_fingerprint: Optional[str] = None,
                    user_agent: Optional[str] = None, ip_address: Optional[str] = None,
                    expires_in_hours: int = 24) -> str:
        """创建新令牌"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO tokens (token_hash, token_type, expires_at, 
                                  device_fingerprint, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (token_hash, token_type, expires_at, device_fingerprint, 
                  user_agent, ip_address))
        
        return token
    
    def validate_token(self, token: str, token_type: Optional[str] = None) -> bool:
        """验证令牌有效性"""
        if not token:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT expires_at, is_active FROM tokens 
                WHERE token_hash = ? AND is_active = 1
            ''', (token_hash,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            expires_at_str, is_active = result
            if not is_active:
                return False
            
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # 令牌已过期，标记为无效
                conn.execute('UPDATE tokens SET is_active = 0 WHERE token_hash = ?', (token_hash,))
                return False
            
            # 更新最后使用时间
            conn.execute('''
                UPDATE tokens SET last_used = CURRENT_TIMESTAMP 
                WHERE token_hash = ?
            ''', (token_hash,))
            
            return True
    
    def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        if not token:
            return False
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE tokens SET is_active = 0 
                WHERE token_hash = ? AND is_active = 1
            ''', (token_hash,))
            return cursor.rowcount > 0
    
    def revoke_all_tokens(self, token_type: Optional[str] = None) -> int:
        """撤销所有令牌或特定类型的令牌"""
        with sqlite3.connect(self.db_path) as conn:
            if token_type:
                cursor = conn.execute('''
                    UPDATE tokens SET is_active = 0 
                    WHERE token_type = ? AND is_active = 1
                ''', (token_type,))
            else:
                cursor = conn.execute('UPDATE tokens SET is_active = 0 WHERE is_active = 1')
            return cursor.rowcount
    
    def cleanup_expired_tokens(self) -> int:
        """清理过期令牌"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE tokens SET is_active = 0 
                WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1
            ''')
            return cursor.rowcount
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """获取令牌信息"""
        if not token:
            return None
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT token_type, created_at, expires_at, last_used,
                       device_fingerprint, user_agent, ip_address, is_active
                FROM tokens WHERE token_hash = ?
            ''', (token_hash,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            return {
                'token_type': result[0],
                'created_at': result[1],
                'expires_at': result[2],
                'last_used': result[3],
                'device_fingerprint': result[4],
                'user_agent': result[5],
                'ip_address': result[6],
                'is_active': bool(result[7])
            }
    
    def record_login_attempt(self, ip_address: str, device_fingerprint: Optional[str],
                           attempt_type: str, success: bool, user_agent: Optional[str] = None):
        """记录登录尝试"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO login_attempts 
                (ip_address, device_fingerprint, attempt_type, success, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (ip_address, device_fingerprint, attempt_type, int(success), user_agent))
    
    def check_rate_limit(self, ip_address: str, attempt_type: str, 
                        max_attempts: int = 5, time_window_minutes: int = 15) -> bool:
        """检查是否超过登录尝试限制"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = ? AND attempt_type = ? AND success = 0
                AND attempted_at > datetime('now', '-' || ? || ' minutes')
            ''', (ip_address, attempt_type, time_window_minutes))
            
            failed_attempts = cursor.fetchone()[0]
            return failed_attempts < max_attempts
    
    def get_login_stats(self, ip_address: str, attempt_type: str, 
                       time_window_hours: int = 24) -> Dict:
        """获取登录统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(success) as successful_attempts,
                    COUNT(*) - SUM(success) as failed_attempts,
                    MAX(attempted_at) as last_attempt
                FROM login_attempts 
                WHERE ip_address = ? AND attempt_type = ?
                AND attempted_at > datetime('now', '-' || ? || ' hours')
            ''', (ip_address, attempt_type, time_window_hours))
            
            result = cursor.fetchone()
            return {
                'total_attempts': result[0] or 0,
                'successful_attempts': result[1] or 0,
                'failed_attempts': result[2] or 0,
                'last_attempt': result[3]
            }


# 全局令牌存储实例
token_storage = TokenStorage()


def get_token_storage() -> TokenStorage:
    """获取令牌存储实例"""
    return token_storage