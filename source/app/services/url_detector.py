"""URL Safety Detection Module"""
import re
import asyncio
from typing import Dict, Any, List
from urllib.parse import urlparse
from loguru import logger


class URLDetector:
    """URL safety detector"""

    def __init__(self):
        # Suspicious keyword list
        self.suspicious_keywords = [
            "login", "verify", "account", "secure", "update",
            "confirm", "suspend", "unlock", "validate", "auth",
            "bank", "paypal", "apple", "microsoft", "amazon"
        ]

        # Common phishing domain patterns
        self.suspicious_patterns = [
            r"[-_]?(bank|pay|secure|login|verify|account)",
            r"(secure|safe|verify)-?account",
            r"update[-_]?(info|account|security)",
        ]

        # TLD blacklist
        self.tld_blacklist = [".tk", ".ml", ".ga", ".cf", ".gq"]

    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """Analyze URL safety"""
        try:
            result = {
                "url": url,
                "risk_score": 0,
                "risk_factors": [],
                "is_suspicious": False,
                "details": {}
            }

            # 1. Basic URL parsing
            parsed = self._parse_url(url)
            if not parsed:
                result["risk_score"] = 100
                result["risk_factors"].append("Invalid URL format")
                result["is_suspicious"] = True
                return result

            result["details"]["parsed_url"] = {
                "scheme": parsed.get("scheme"),
                "domain": parsed.get("domain"),
                "path": parsed.get("path")
            }

            # 2. Check HTTPS
            https_score = self._check_https(parsed.get("scheme"))
            result["risk_score"] += https_score
            if https_score > 0:
                result["risk_factors"].append("Does not use HTTPS encryption")

            # 3. Check domain
            domain_score = await self._check_domain(parsed.get("domain"))
            result["risk_score"] += domain_score

            # 4. Check suspicious patterns
            pattern_score = self._check_suspicious_patterns(url)
            result["risk_score"] += pattern_score

            # 5. Check URL length and complexity
            complexity_score = self._check_url_complexity(url)
            result["risk_score"] += complexity_score

            # 6. Check IP address direct access
            if self._is_ip_address(parsed.get("domain")):
                result["risk_score"] += 30
                result["risk_factors"].append("Uses IP address instead of domain name")

            # Normalize score to 0-100
            result["risk_score"] = min(100, result["risk_score"])
            result["is_suspicious"] = result["risk_score"] >= 50

            logger.info(f"URL analysis completed: {url}, risk_score: {result['risk_score']}")
            return result

        except Exception as e:
            logger.error(f"URL analysis failed: {str(e)}")
            return {
                "url": url,
                "risk_score": 50,
                "risk_factors": [f"Analysis error: {str(e)}"],
                "is_suspicious": True,
                "details": {}
            }

    def _parse_url(self, url: str) -> Dict[str, str]:
        """Parse URL"""
        try:
            # Add http prefix if missing
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url

            parsed = urlparse(url)
            return {
                "scheme": parsed.scheme,
                "domain": parsed.netloc.lower(),
                "path": parsed.path,
                "query": parsed.query
            }
        except Exception as e:
            logger.error(f"URL parsing failed: {str(e)}")
            return None

    def _check_https(self, scheme: str) -> int:
        """Check HTTPS usage"""
        if scheme != "https":
            return 20
        return 0

    async def _check_domain(self, domain: str) -> int:
        """Check domain safety"""
        if not domain:
            return 50

        score = 0

        # Check TLD blacklist
        for tld in self.tld_blacklist:
            if domain.endswith(tld):
                score += 40
                break

        # Check domain length
        if len(domain) > 30:
            score += 15

        # Check for excessive hyphens
        if domain.count('-') > 2:
            score += 20

        # Check for mixed letters and numbers (possible spoofed domain)
        if re.search(r'[a-z]+\d+[a-z]+', domain) or re.search(r'\d+[a-z]+\d+', domain):
            score += 15

        # Attempt DNS query (lazy load, don't crash if dnspython is not installed)
        try:
            import dns.resolver as _dns
            _dns.resolve(domain, 'A')
        except ImportError:
            pass  # dnspython not installed, skip DNS check
        except Exception:
            score += 25  # DNS resolution failed, add score

        return score

    def _check_suspicious_patterns(self, url: str) -> int:
        """Check suspicious patterns"""
        score = 0
        url_lower = url.lower()

        # Check suspicious keywords
        keyword_count = sum(1 for kw in self.suspicious_keywords if kw in url_lower)
        score += min(30, keyword_count * 10)

        # Check regex patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, url_lower):
                score += 20

        return score

    def _check_url_complexity(self, url: str) -> int:
        """Check URL complexity"""
        score = 0

        # URL too long
        if len(url) > 100:
            score += 15

        # Excessive parameters
        if url.count('?') > 0 or url.count('&') > 3:
            score += 20

        # Contains encoded characters
        if '%' in url or '+' in url:
            score += 10

        return score

    def _is_ip_address(self, domain: str) -> bool:
        """Check if domain is an IP address"""
        if not domain:
            return False
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        return bool(re.match(ip_pattern, domain))


# Create global instance
url_detector = URLDetector()
