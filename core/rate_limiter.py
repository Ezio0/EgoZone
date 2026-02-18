"""
登录限流器 - 防止暴力破解攻击
"""

import time
import sqlite3
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json


class LoginAttempt:
    """登录尝试记录"""
    
    def __init__(self, identifier: str, ip_address: str, success: bool = False):
        self.identifier = identifier  # 用户名或设备指纹
        self.ip_address = ip_address
        self.timestamp = datetime.now()
        self.success = success
        self.count = 1


class RateLimiter:
    """登录限流器"""
    
    def __init__(self, db_path: str = "./data/rate_limiter.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 限流配置
        self.config = {
            'max_attempts_per_ip': 10,      # 每IP最大尝试次数
            'max_attempts_per_user': 5,     # 每用户最大尝试次数
            'time_window_minutes': 15,      # 时间窗口（分钟）
            'lockout_duration_minutes': 30, # 锁定时间（分钟）
            'max_global_attempts': 100,     # 全局最大尝试次数
            'global_time_window_minutes': 5 # 全局时间窗口
        }
        
        self._init_database()
        self._memory_cache: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 登录尝试记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                success BOOLEAN NOT NULL DEFAULT FALSE,
                user_agent TEXT,
                device_fingerprint TEXT
            )
        ''')
        
        # 锁定记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lockouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                locked_until DATETIME NOT NULL,
                reason TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attempts_identifier ON login_attempts(identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attempts_ip ON login_attempts(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_attempts_timestamp ON login_attempts(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lockouts_identifier ON lockouts(identifier)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lockouts_ip ON lockouts(ip_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lockouts_locked_until ON lockouts(locked_until)')
        
        conn.commit()
        conn.close()
    
    def record_attempt(self, identifier: str, ip_address: str, success: bool = False,
                      user_agent: str = None, device_fingerprint: str = None):
        """记录登录尝试"""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO login_attempts 
                    (identifier, ip_address, timestamp, success, user_agent, device_fingerprint)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (identifier, ip_address, datetime.now(), success, user_agent, device_fingerprint))
                
                conn.commit()
                
                # 清理过期记录（保留7天）
                cutoff_date = datetime.now() - timedelta(days=7)
                cursor.execute('DELETE FROM login_attempts WHERE timestamp < ?', (cutoff_date,))
                conn.commit()
                
            finally:
                conn.close()
    
    def is_locked(self, identifier: str, ip_address: str) -> Tuple[bool, Optional[str]]:
        """检查是否被锁定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            
            # 检查用户锁定
            cursor.execute('''
                SELECT locked_until, reason FROM lockouts 
                WHERE identifier = ? AND locked_until > ?
                ORDER BY locked_until DESC LIMIT 1
            ''', (identifier, now))
            
            user_lock = cursor.fetchone()
            if user_lock:
                return True, f"用户被锁定: {user_lock[1]}"
            
            # 检查IP锁定
            cursor.execute('''
                SELECT locked_until, reason FROM lockouts 
                WHERE ip_address = ? AND locked_until > ?
                ORDER BY locked_until DESC LIMIT 1
            ''', (ip_address, now))
            
            ip_lock = cursor.fetchone()
            if ip_lock:
                return True, f"IP被锁定: {ip_lock[1]}"
            
            return False, None
            
        finally:
            conn.close()
    
    def check_rate_limit(self, identifier: str, ip_address: str) -> Tuple[bool, str]:
        """检查是否超过速率限制"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            time_window_start = now - timedelta(minutes=self.config['time_window_minutes'])
            
            # 检查用户尝试次数
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE identifier = ? AND timestamp > ? AND success = FALSE
            ''', (identifier, time_window_start))
            
            user_attempts = cursor.fetchone()[0]
            
            # 检查IP尝试次数
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE ip_address = ? AND timestamp > ? AND success = FALSE
            ''', (ip_address, time_window_start))
            
            ip_attempts = cursor.fetchone()[0]
            
            # 检查全局尝试次数
            global_window_start = now - timedelta(minutes=self.config['global_time_window_minutes'])
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE timestamp > ? AND success = FALSE
            ''', (global_window_start,))
            
            global_attempts = cursor.fetchone()[0]
            
            # 判断是否需要锁定
            if user_attempts >= self.config['max_attempts_per_user']:
                self._lock_identifier(identifier, ip_address, "用户尝试次数过多")
                return False, f"用户尝试次数过多（{user_attempts}次），已锁定{self.config['lockout_duration_minutes']}分钟"
            
            if ip_attempts >= self.config['max_attempts_per_ip']:
                self._lock_ip(identifier, ip_address, "IP尝试次数过多")
                return False, f"IP尝试次数过多（{ip_attempts}次），已锁定{self.config['lockout_duration_minutes']}分钟"
            
            if global_attempts >= self.config['max_global_attempts']:
                return False, f"系统繁忙，请稍后再试"
            
            # 返回剩余尝试次数
            remaining_user = self.config['max_attempts_per_user'] - user_attempts
            remaining_ip = self.config['max_attempts_per_ip'] - ip_attempts
            remaining = min(remaining_user, remaining_ip)
            
            if remaining <= 3:
                return True, f"警告：剩余尝试次数 {remaining}次"
            
            return True, "允许登录"
            
        finally:
            conn.close()
    
    def _lock_identifier(self, identifier: str, ip_address: str, reason: str):
        """锁定用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            locked_until = datetime.now() + timedelta(minutes=self.config['lockout_duration_minutes'])
            
            cursor.execute('''
                INSERT INTO lockouts (identifier, ip_address, locked_until, reason)
                VALUES (?, ?, ?, ?)
            ''', (identifier, ip_address, locked_until, reason))
            
            conn.commit()
            print(f"用户 {identifier} 被锁定至 {locked_until}，原因：{reason}")
            
        finally:
            conn.close()
    
    def _lock_ip(self, identifier: str, ip_address: str, reason: str):
        """锁定IP"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            locked_until = datetime.now() + timedelta(minutes=self.config['lockout_duration_minutes'])
            
            cursor.execute('''
                INSERT INTO lockouts (identifier, ip_address, locked_until, reason)
                VALUES (?, ?, ?, ?)
            ''', (identifier, ip_address, locked_until, reason))
            
            conn.commit()
            print(f"IP {ip_address} 被锁定至 {locked_until}，原因：{reason}")
            
        finally:
            conn.close()
    
    def get_attempt_stats(self, identifier: str, ip_address: str) -> Dict:
        """获取尝试统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            time_window_start = now - timedelta(minutes=self.config['time_window_minutes'])
            
            # 用户统计
            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END)
                FROM login_attempts 
                WHERE identifier = ? AND timestamp > ?
            ''', (identifier, time_window_start))
            
            user_stats = cursor.fetchone()
            
            # IP统计
            cursor.execute('''
                SELECT COUNT(*), SUM(CASE WHEN success = TRUE THEN 1 ELSE 0 END)
                FROM login_attempts 
                WHERE ip_address = ? AND timestamp > ?
            ''', (ip_address, time_window_start))
            
            ip_stats = cursor.fetchone()
            
            # 检查锁定状态
            is_locked, lock_reason = self.is_locked(identifier, ip_address)
            
            return {
                'user_attempts': user_stats[0] if user_stats else 0,
                'user_successes': user_stats[1] if user_stats and user_stats[1] else 0,
                'ip_attempts': ip_stats[0] if ip_stats else 0,
                'ip_successes': ip_stats[1] if ip_stats and ip_stats[1] else 0,
                'is_locked': is_locked,
                'lock_reason': lock_reason,
                'max_attempts_per_user': self.config['max_attempts_per_user'],
                'max_attempts_per_ip': self.config['max_attempts_per_ip'],
                'time_window_minutes': self.config['time_window_minutes']
            }
            
        finally:
            conn.close()
    
    def cleanup_old_records(self):
        """清理旧记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 清理过期锁定记录
            now = datetime.now()
            cursor.execute('DELETE FROM lockouts WHERE locked_until < ?', (now,))
            deleted_lockouts = cursor.rowcount
            
            # 清理过期尝试记录（保留30天）
            cutoff_date = now - timedelta(days=30)
            cursor.execute('DELETE FROM login_attempts WHERE timestamp < ?', (cutoff_date,))
            deleted_attempts = cursor.rowcount
            
            conn.commit()
            
            print(f"清理完成：删除 {deleted_lockouts} 个过期锁定记录，{deleted_attempts} 个过期尝试记录")
            
        finally:
            conn.close()


# 全局限流器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def check_login_rate_limit(identifier: str, ip_address: str) -> Tuple[bool, str]:
    """检查登录速率限制"""
    limiter = get_rate_limiter()
    
    # 检查是否被锁定
    is_locked, lock_reason = limiter.is_locked(identifier, ip_address)
    if is_locked:
        return False, lock_reason
    
    # 检查速率限制
    allowed, message = limiter.check_rate_limit(identifier, ip_address)
    return allowed, message


def record_login_attempt(identifier: str, ip_address: str, success: bool = False,
                        user_agent: str = None, device_fingerprint: str = None):
    """记录登录尝试"""
    limiter = get_rate_limiter()
    limiter.record_attempt(identifier, ip_address, success, user_agent, device_fingerprint)


def get_login_stats(identifier: str, ip_address: str) -> Dict:
    """获取登录统计"""
    limiter = get_rate_limiter()
    return limiter.get_attempt_stats(identifier, ip_address)


def cleanup_rate_limit_data():
    """清理限流数据"""
    limiter = get_rate_limiter()
    limiter.cleanup_old_records()


if __name__ == "__main__":
    # 测试限流器
    limiter = RateLimiter()
    
    # 模拟一些登录尝试
    test_ip = "192.168.1.100"
    test_user = "test_user"
    
    print("测试限流器...")
    
    # 成功登录
    allowed, message = check_login_rate_limit(test_user, test_ip)
    print(f"第一次尝试: {allowed}, {message}")
    record_login_attempt(test_user, test_ip, success=True)
    
    # 多次失败尝试
    for i in range(6):
        allowed, message = check_login_rate_limit(test_user, test_ip)
        print(f"失败尝试 {i+1}: {allowed}, {message}")
        if allowed:
            record_login_attempt(test_user, test_ip, success=False)
    
    # 检查统计
    stats = get_login_stats(test_user, test_ip)
    print(f"统计信息: {json.dumps(stats, indent=2, default=str)}")
    
    # 清理数据
    cleanup_rate_limit_data()