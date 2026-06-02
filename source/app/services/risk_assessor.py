"""Comprehensive Risk Assessment and Alert Module"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class RiskAssessor:
    """Comprehensive risk assessor"""

    def __init__(self):
        # Risk weight configuration
        self.weights = {
            "url": 0.25,
            "content": 0.35,
            "voice": 0.25,
            "threat_intel": 0.15
        }

        # Risk level mapping
        self.risk_levels = {
            "safe": {"label": "Safe", "color": "green", "action": "No action needed"},
            "low": {"label": "Low Risk", "color": "yellow", "action": "Stay vigilant"},
            "medium": {"label": "Medium Risk", "color": "orange", "action": "Proceed with caution"},
            "high": {"label": "High Risk", "color": "red", "action": "Stop immediately"},
            "critical": {"label": "Critical Risk", "color": "darkred", "action": "Call police immediately"}
        }

    async def assess_risk(
        self,
        url_result: Optional[Dict[str, Any]] = None,
        content_result: Optional[Dict[str, Any]] = None,
        voice_result: Optional[Dict[str, Any]] = None,
        threat_intel_result: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive risk assessment

        Args:
            url_result: URL detection result
            content_result: Content analysis result
            voice_result: Voice detection result
            threat_intel_result: Threat intelligence result
            user_profile: User profile

        Returns:
            Comprehensive assessment result
        """
        try:
            result = {
                "overall_risk_score": 0,
                "overall_risk_level": "safe",
                "risk_details": {},
                "recommendations": [],
                "alert_message": "",
                "timestamp": datetime.now().isoformat()
            }

            # 1. Calculate weighted scores for each module
            weighted_scores = []

            if url_result:
                url_score = url_result.get("risk_score", 0)
                weighted_scores.append(url_score * self.weights["url"])
                result["risk_details"]["url"] = {
                    "score": url_score,
                    "weight": self.weights["url"],
                    "weighted_score": url_score * self.weights["url"]
                }

            if content_result:
                content_score = content_result.get("risk_score", 0)
                weighted_scores.append(content_score * self.weights["content"])
                result["risk_details"]["content"] = {
                    "score": content_score,
                    "weight": self.weights["content"],
                    "weighted_score": content_score * self.weights["content"]
                }

            if voice_result:
                voice_score = voice_result.get("risk_score", 0)
                weighted_scores.append(voice_score * self.weights["voice"])
                result["risk_details"]["voice"] = {
                    "score": voice_score,
                    "weight": self.weights["voice"],
                    "weighted_score": voice_score * self.weights["voice"]
                }

            if threat_intel_result:
                threat_score = threat_intel_result.get("risk_score", 0)
                weighted_scores.append(threat_score * self.weights["threat_intel"])
                result["risk_details"]["threat_intel"] = {
                    "score": threat_score,
                    "weight": self.weights["threat_intel"],
                    "weighted_score": threat_score * self.weights["threat_intel"]
                }

            # 2. Calculate total score
            if weighted_scores:
                total_score = sum(weighted_scores) / sum(self.weights.values())
            else:
                total_score = 0

            result["overall_risk_score"] = round(total_score, 2)

            # 3. Determine risk level
            result["overall_risk_level"] = self._get_risk_level(total_score)

            # 4. Generate recommendations
            result["recommendations"] = self._generate_recommendations(
                result["overall_risk_level"],
                result["risk_details"]
            )

            # 5. Generate alert message
            result["alert_message"] = self._generate_alert_message(
                result["overall_risk_level"],
                result["overall_risk_score"],
                result["recommendations"]
            )

            # 6. Consider user profile (if provided)
            if user_profile:
                result = self._adjust_for_user_profile(result, user_profile)

            logger.info(f"Risk assessment completed: score={result['overall_risk_score']}, level={result['overall_risk_level']}")
            return result

        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            return {
                "overall_risk_score": 50,
                "overall_risk_level": "medium",
                "risk_details": {},
                "recommendations": ["System analysis error, please handle with caution"],
                "alert_message": "System analysis error, it is recommended to handle the current operation with caution",
                "timestamp": datetime.now().isoformat()
            }

    def _get_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score < 20:
            return "safe"
        elif score < 40:
            return "low"
        elif score < 60:
            return "medium"
        elif score < 80:
            return "high"
        else:
            return "critical"

    def _generate_recommendations(
        self,
        risk_level: str,
        risk_details: Dict[str, Any]
    ) -> List[str]:
        """Generate handling recommendations"""
        recommendations = []

        if risk_level == "safe":
            recommendations.append("The current operation appears to be safe")
            recommendations.append("Stay vigilant and protect your personal information")

        elif risk_level == "low":
            recommendations.append("Some suspicious characteristics detected, please be cautious")
            recommendations.append("We recommend verifying the other party's identity and information source")

            if "url" in risk_details:
                recommendations.append("Check if the URL is correct, avoid clicking suspicious links")

        elif risk_level == "medium":
            recommendations.append("Multiple suspicious characteristics detected, please be highly vigilant")
            recommendations.append("We recommend stopping the current operation immediately")
            recommendations.append("Do not provide any personal information or make transfers")
            recommendations.append("Verify the other party's identity through other channels")

        elif risk_level == "high":
            recommendations.append("High risk detected! You are likely encountering a scam")
            recommendations.append("Stop all operations immediately")
            recommendations.append("Absolutely do not transfer money or provide verification codes")
            recommendations.append("Contact family or friends immediately to discuss")
            recommendations.append("Call 110 or 96110 for consultation")

        elif risk_level == "critical":
            recommendations.append("Emergency warning! Confirmed fraud!")
            recommendations.append("Hang up the phone or close the webpage immediately")
            recommendations.append("Absolutely do not perform any transfer operations")
            recommendations.append("Call 110 immediately to report to the police")
            recommendations.append("Call 96110 anti-fraud hotline for consultation")

        return recommendations

    def _generate_alert_message(
        self,
        risk_level: str,
        risk_score: float,
        recommendations: List[str]
    ) -> str:
        """Generate alert message"""
        level_info = self.risk_levels.get(risk_level, {})
        level_label = level_info.get("label", "Unknown")

        if risk_level in ["safe", "low"]:
            message = f"[Safety Notice] Risk Level: {level_label} ({risk_score} points)"
        elif risk_level == "medium":
            message = f"[Warning] Risk Level: {level_label} ({risk_score} points)\n{recommendations[0]}"
        elif risk_level in ["high", "critical"]:
            message = f"[Emergency Warning] Risk Level: {level_label} ({risk_score} points)\n{recommendations[0]}"
        else:
            message = f"Risk assessment completed: {level_label}"

        return message

    def _adjust_for_user_profile(
        self,
        result: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust assessment results based on user profile"""
        # Elderly users have lower risk tolerance
        age = user_profile.get("age", 60)
        if age >= 60:
            # Increase risk score by 10% for elderly users
            adjusted_score = min(100, result["overall_risk_score"] * 1.1)
            result["overall_risk_score"] = round(adjusted_score, 2)
            result["overall_risk_level"] = self._get_risk_level(adjusted_score)
            result["adjusted_for_elderly"] = True
            result["recommendations"].insert(0,
                "The system detects that you are a senior user and has automatically increased the security level"
            )

        return result

    def create_alert_record(
        self,
        user_id: str,
        detection_id: int,
        risk_level: str,
        alert_message: str
    ) -> Dict[str, Any]:
        """Create an alert record"""
        return {
            "user_id": user_id,
            "detection_id": detection_id,
            "alert_level": risk_level,
            "alert_message": alert_message,
            "is_read": False,
            "created_at": datetime.now().isoformat()
        }


# Create global instance
risk_assessor = RiskAssessor()
