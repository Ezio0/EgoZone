"""
Enhanced Device Fingerprint Generation Module
Provides more secure device identification mechanism
"""

import hashlib
import json
from typing import Dict, Optional
from datetime import datetime
import re


class DeviceFingerprint:
    """Enhanced device fingerprint generator"""

    @staticmethod
    def generate_enhanced_fingerprint(
        user_agent: str,
        ip_address: str,
        accept_language: Optional[str] = None,
        accept_encoding: Optional[str] = None,
        dnt: Optional[str] = None,
    ) -> str:
        """
        Generate enhanced device fingerprint

        Args:
            user_agent: User agent string
            ip_address: IP address
            accept_language: Accept language
            accept_encoding: Accept encoding
            dnt: Do Not Track flag

        Returns:
            Device fingerprint hash value
        """
        # Parse User-Agent to get device info
        device_info = DeviceFingerprint._parse_user_agent(user_agent)

        # Build device feature vector
        features = {
            "user_agent": user_agent,
            "ip_address": ip_address,
            "browser": device_info.get("browser", "unknown"),
            "browser_version": device_info.get("browser_version", "unknown"),
            "os": device_info.get("os", "unknown"),
            "os_version": device_info.get("os_version", "unknown"),
            "device_type": device_info.get("device_type", "unknown"),
            "accept_language": accept_language or "unknown",
            "accept_encoding": accept_encoding or "unknown",
            "dnt": dnt or "unknown",
        }

        # Sort alphabetically to ensure consistency
        sorted_features = json.dumps(features, sort_keys=True)

        # Generate fingerprint using SHA-256
        fingerprint = hashlib.sha256(sorted_features.encode("utf-8")).hexdigest()

        return fingerprint

    @staticmethod
    def _parse_user_agent(user_agent: str) -> Dict[str, str]:
        """Parse User-Agent string"""
        info = {
            "browser": "unknown",
            "browser_version": "unknown",
            "os": "unknown",
            "os_version": "unknown",
            "device_type": "desktop",
        }

        if not user_agent:
            return info

        user_agent_lower = user_agent.lower()

        # Browser detection
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            info["browser"] = "chrome"
            version_match = re.search(r"chrome/(\d+\.\d+)", user_agent_lower)
            if version_match:
                info["browser_version"] = version_match.group(1)
        elif "firefox" in user_agent_lower:
            info["browser"] = "firefox"
            version_match = re.search(r"firefox/(\d+\.\d+)", user_agent_lower)
            if version_match:
                info["browser_version"] = version_match.group(1)
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            info["browser"] = "safari"
            version_match = re.search(r"version/(\d+\.\d+)", user_agent_lower)
            if version_match:
                info["browser_version"] = version_match.group(1)
        elif "edg" in user_agent_lower:
            info["browser"] = "edge"
            version_match = re.search(r"edg/(\d+\.\d+)", user_agent_lower)
            if version_match:
                info["browser_version"] = version_match.group(1)

        # Operating system detection
        if "windows nt 10.0" in user_agent_lower:
            info["os"] = "windows"
            info["os_version"] = "10"
        elif "windows nt 6.3" in user_agent_lower:
            info["os"] = "windows"
            info["os_version"] = "8.1"
        elif "windows nt 6.1" in user_agent_lower:
            info["os"] = "windows"
            info["os_version"] = "7"
        elif "mac os x" in user_agent_lower:
            info["os"] = "macos"
            version_match = re.search(r"mac os x (\d+[_\.]\d+)", user_agent_lower)
            if version_match:
                info["os_version"] = version_match.group(1).replace("_", ".")
        elif "linux" in user_agent_lower:
            info["os"] = "linux"
        elif "android" in user_agent_lower:
            info["os"] = "android"
            version_match = re.search(r"android (\d+\.\d+)", user_agent_lower)
            if version_match:
                info["os_version"] = version_match.group(1)
        elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            info["os"] = "ios"
            version_match = re.search(r"os (\d+[_\.]\d+)", user_agent_lower)
            if version_match:
                info["os_version"] = version_match.group(1).replace("_", ".")

        # Device type detection
        if "mobile" in user_agent_lower:
            info["device_type"] = "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            info["device_type"] = "tablet"
        elif "android" in user_agent_lower and "mobile" not in user_agent_lower:
            info["device_type"] = "tablet"

        return info

    @staticmethod
    def get_device_risk_score(fingerprint_data: Dict) -> float:
        """
        Calculate device risk score

        Returns:
            Risk score (0.0 - 1.0), higher means higher risk
        """
        risk_score = 0.0

        # Base risk score
        user_agent = fingerprint_data.get("user_agent", "")

        # Empty or very short User-Agent is high risk
        if not user_agent or len(user_agent) < 20:
            risk_score += 0.3

        # Missing key information increases risk
        if "unknown" in str(fingerprint_data.values()):
            risk_score += 0.2

        # Automation tool features
        suspicious_patterns = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "curl",
            "wget",
            "python",
            "java",
            "httpclient",
            "okhttp",
            "axios",
        ]

        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                risk_score += 0.4
                break

        # Ensure score is within reasonable range
        return min(risk_score, 1.0)

    @staticmethod
    def is_suspicious_device(user_agent: str, ip_address: str) -> bool:
        """Quick check if device is suspicious"""
        if not user_agent:
            return True

        user_agent_lower = user_agent.lower()

        # Automation tool blacklist (reduced sensitivity, only block obvious bots)
        automation_signatures = [
            "bot",
            "crawler",
            "spider",
            "scraper",
            "selenium",
            "phantomjs",
            "headless",
            "puppeteer",
            "python-requests",
            "httpclient",
            "okhttp",
        ]

        for signature in automation_signatures:
            if signature in user_agent_lower:
                return True

        # Check if User-Agent format is abnormal
        if len(user_agent) < 10 or len(user_agent) > 500:
            return True

        # Check if missing common browser features (relaxed, allow dev tools)
        common_browsers = ["chrome", "firefox", "safari", "edge", "curl", "wget"]
        has_browser = any(browser in user_agent_lower for browser in common_browsers)

        # More relaxed condition: only very short without common features is suspicious
        if not has_browser and len(user_agent) < 20:
            return True

        return False


def generate_device_fingerprint(
    user_agent: str,
    ip_address: str,
    accept_language: Optional[str] = None,
    accept_encoding: Optional[str] = None,
    dnt: Optional[str] = None,
) -> str:
    """Device fingerprint generation function compatible with old interface"""
    return DeviceFingerprint.generate_enhanced_fingerprint(
        user_agent, ip_address, accept_language, accept_encoding, dnt
    )
