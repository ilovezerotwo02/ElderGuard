"""LLM Service Module"""
from typing import Dict, Any, List, Optional
from app.core.config import settings
from loguru import logger

# Optional AI library imports for packaging compatibility
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class LLMService:
    """Large Language Model Service"""

    def __init__(self):
        # Rules-only mode: no AI models loaded
        if settings.USE_RULES_ONLY:
            self.use_ollama = False
            self.use_openai = False
            self.use_local = False
        else:
            self.use_ollama = settings.USE_OLLAMA and OLLAMA_AVAILABLE
            self.use_openai = not self.use_ollama and settings.OPENAI_API_KEY and OPENAI_AVAILABLE
            self.use_local = not self.use_ollama and not self.use_openai and settings.USE_LOCAL_MODEL

        if self.use_ollama:
            logger.info(f"Using Ollama mode, model: {settings.OLLAMA_MODEL_NAME}")
            logger.info(f"Ollama address: {settings.OLLAMA_BASE_URL}")
            # Create client instance with explicit address (avoid default 0.0.0.0 connection issue on Windows)
            self.ollama_client = ollama.Client(host=settings.OLLAMA_BASE_URL)
            # Test connection
            try:
                models = self.ollama_client.list()
                logger.info(f"Ollama available models: {[m['model'] for m in models.get('models', [])]}")
            except Exception as e:
                logger.warning(f"Ollama connection failed: {str(e)}")
                logger.warning("Degrading to local rules mode")
                self.use_ollama = False
                self.use_local = True
        elif self.use_openai:
            logger.info("Using OpenAI API mode")
            # Initialize OpenAI client
            if OPENAI_AVAILABLE:
                self.client = openai.AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
            else:
                logger.warning("OpenAI library not available, degrading to local rules mode")
                self.use_openai = False
                self.use_local = True
        else:
            logger.info("Using local rules mode")

    async def analyze_intent(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze text intent

        Args:
            text: Text to analyze
            context: Context information

        Returns:
            Intent analysis result
        """
        try:
            if self.use_ollama:
                return await self._analyze_with_ollama(text, context)
            elif self.use_openai:
                return await self._analyze_with_openai(text, context)
            else:
                return self._analyze_with_rules(text, context)

        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return {
                "intent": "unknown",
                "confidence": 0,
                "categories": [],
                "error": str(e)
            }

    async def _analyze_with_ollama(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze using Ollama"""
        prompt = f"""
Please analyze the intent of the following text and determine whether it is likely fraudulent.

Text: {text}
{f'Context: {context}' if context else ''}

Return the result in JSON format with the following fields (no additional content):
{{
  "intent": "Primary intent (e.g., fraud, normal inquiry, marketing, etc.)",
  "confidence": 0.85,
  "categories": ["List of likely categories"],
  "risk_factors": ["List of risk factors"],
  "explanation": "Brief explanation"
}}
"""

        try:
            response = self.ollama_client.chat(
                model=settings.OLLAMA_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a professional anti-fraud analysis expert skilled at identifying various fraud techniques."},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.3}
            )

            content = response.get("message", {}).get("content", "{}")
            # Attempt to parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result

            return {
                "intent": "fraud",
                "confidence": 0.8,
                "categories": ["Suspected fraud"],
                "risk_factors": ["Abnormal LLM analysis"],
                "explanation": content
            }
        except Exception as e:
            logger.error(f"Ollama analysis failed: {str(e)}")
            # Degrade to rules mode
            return self._analyze_with_rules(text, context)

    async def _analyze_with_openai(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze using OpenAI API"""
        prompt = f"""
        Please analyze the intent of the following text and determine whether it is likely fraudulent.

        Text: {text}
        {f'Context: {context}' if context else ''}

        Return the result as JSON with the following fields:
        - intent: Primary intent (e.g., fraud, normal inquiry, marketing, etc.)
        - confidence: Confidence level (0-1)
        - categories: List of likely categories
        - risk_factors: List of risk factors
        - explanation: Brief explanation
        """

        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional anti-fraud analysis expert skilled at identifying various fraud techniques."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        # Parse response
        content = response.choices[0].message.content
        # TODO: Parse JSON response

        return {
            "intent": "fraud",
            "confidence": 0.85,
            "categories": ["Impersonating Law Enforcement"],
            "risk_factors": ["Threat", "Requesting transfer"],
            "explanation": content
        }

    def _analyze_with_rules(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze using rules (local mode)"""
        # Simplified rule analysis
        # NOTE: Keywords remain in Chinese as they target Chinese-language content
        fraud_indicators = [
            "转账", "汇款", "安全账户", "验证码",
            "公安", "法院", "涉案", "通缉",
            "立即", "马上", "紧急", "限时"
        ]

        matched = [word for word in fraud_indicators if word in text]
        confidence = min(1.0, len(matched) / 5.0)

        return {
            "intent": "fraud" if confidence > 0.5 else "unknown",
            "confidence": confidence,
            "categories": ["Suspected fraud"] if confidence > 0.5 else [],
            "risk_factors": matched,
            "explanation": f"Detected {len(matched)} fraud indicator keywords"
        }

    async def generate_explanation(
        self,
        detection_result: Dict[str, Any],
        user_age: Optional[int] = None
    ) -> str:
        """
        Generate a user-appropriate explanation

        Args:
            detection_result: Detection result
            user_age: User age

        Returns:
            Explanation text
        """
        try:
            if self.use_ollama:
                return await self._generate_with_ollama(detection_result, user_age)
            elif self.use_openai:
                return await self._generate_with_openai(detection_result, user_age)
            else:
                return self._generate_simple_explanation(detection_result)

        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return "System analysis completed, please stay safe"

    async def _generate_with_ollama(
        self,
        detection_result: Dict[str, Any],
        user_age: Optional[int] = None
    ) -> str:
        """Generate explanation using Ollama"""
        age_context = f"The user is {user_age} years old. Please use simple, easy-to-understand language suitable for elderly users." if user_age else ""

        prompt = f"""
Please explain the following detection results to a regular user so they can understand why this is fraudulent.
{age_context}

Detection results: {detection_result}

Requirements:
1. Use simple and easy-to-understand language
2. Point out specific risk points
3. Give clear advice
4. Tone should be friendly but serious
5. Keep it under 200 characters
"""

        try:
            response = self.ollama_client.chat(
                model=settings.OLLAMA_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a patient anti-fraud educator who specializes in helping elderly users identify scams."},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.7}
            )

            return response.get("message", {}).get("content", "System analysis completed, please stay safe")
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            return self._generate_simple_explanation(detection_result)

    async def _generate_with_openai(
        self,
        detection_result: Dict[str, Any],
        user_age: Optional[int] = None
    ) -> str:
        """Generate explanation using OpenAI"""
        age_context = f"The user is {user_age} years old. Please use simple and easy-to-understand language." if user_age else ""

        prompt = f"""
        Please explain the following detection results to a regular user so they can understand why this is fraudulent.
        {age_context}

        Detection results: {detection_result}

        Requirements:
        1. Use simple and easy-to-understand language
        2. Point out specific risk points
        3. Give clear advice
        4. Tone should be friendly but serious
        5. Keep it under 200 characters
        """

        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a patient anti-fraud educator who specializes in helping elderly users identify scams."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content

    def _generate_simple_explanation(self, detection_result: Dict[str, Any]) -> str:
        """Generate simple explanation (local mode)"""
        risk_score = detection_result.get("risk_score", 0)
        risk_factors = detection_result.get("risk_factors", [])

        if risk_score >= 80:
            level = "Critical Risk"
            advice = "This is clearly a scam. Please stop all operations immediately and call the police."
        elif risk_score >= 60:
            level = "High Risk"
            advice = "This is very likely a scam. Do not provide any information and hang up the phone."
        elif risk_score >= 40:
            level = "Medium Risk"
            advice = "Suspicious characteristics detected. Please be cautious and verify the other party's identity."
        elif risk_score >= 20:
            level = "Low Risk"
            advice = "Some suspicious elements found. Please stay alert."
        else:
            level = "Safe"
            advice = "The current operation appears to be safe."

        explanation = f"Risk Level: {level} ({risk_score} points)\n"
        if risk_factors:
            explanation += f"Suspicious characteristics found: {', '.join(risk_factors)}\n"
        explanation += f"Recommendation: {advice}"

        return explanation


# Create global instance
llm_service = LLMService()
