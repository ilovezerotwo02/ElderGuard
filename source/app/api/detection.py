"""Detection-related API"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from loguru import logger

from app.api.schemas import (
    URLCheckRequest, URLCheckResponse,
    ContentCheckRequest, ContentCheckResponse,
    VoiceCheckRequest, VoiceCheckResponse,
    ComprehensiveCheckRequest, ComprehensiveCheckResponse
)
from app.services.url_detector import url_detector
from app.services.content_analyzer import content_analyzer
from app.services.voice_detector import voice_detector
from app.services.risk_assessor import risk_assessor
from app.llm.service import llm_service
from app.database.session import get_db

router = APIRouter(prefix="/detect", tags=["Detection"])


@router.post("/url", response_model=URLCheckResponse)
async def check_url(request: URLCheckRequest):
    """
    Check URL safety

    - **url**: The URL to check
    - **user_id**: User ID (optional)
    """
    try:
        # Detect URL
        result = await url_detector.analyze_url(request.url)

        # Generate recommendations
        risk_level = risk_assessor._get_risk_level(result["risk_score"])
        recommendations = risk_assessor._generate_recommendations(
            risk_level,
            {"url": {"score": result["risk_score"]}}
        )

        return URLCheckResponse(
            url=result["url"],
            risk_score=result["risk_score"],
            risk_level=risk_level,
            is_suspicious=result["is_suspicious"],
            risk_factors=result["risk_factors"],
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"URL detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/content", response_model=ContentCheckResponse)
async def check_content(request: ContentCheckRequest):
    """
    Check SMS or call content

    - **content**: The content to check
    - **content_type**: Content type (sms/call)
    - **user_id**: User ID (optional)
    """
    try:
        # Rule-based analysis
        result = content_analyzer.analyze_content(request.content, request.content_type)

        # LLM deep analysis (non-blocking, 30 second timeout)
        llm_intent = None
        try:
            llm_intent = await asyncio.wait_for(
                llm_service.analyze_intent(request.content),
                timeout=30.0
            )
            if llm_intent and llm_intent.get("intent") != "unknown":
                logger.info(f"LLM analysis completed: {llm_intent.get('intent')} (confidence: {llm_intent.get('confidence')})")
                # Fuse LLM results: if LLM detects fraud, boost risk score
                if llm_intent.get("intent") == "fraud" and llm_intent.get("confidence", 0) > 0.6:
                    boost = int(llm_intent["confidence"] * 30)
                    result["risk_score"] = min(100, result["risk_score"] + boost)
                    # Add LLM-discovered risk factors
                    llm_factors = llm_intent.get("risk_factors", [])
                    for f in llm_factors:
                        if f not in result["risk_factors"]:
                            result["risk_factors"].append(f"[LLM] {f}")
                    result["risk_level"] = content_analyzer._get_risk_level(result["risk_score"])
                # Update intent analysis
                result["intent_analysis"]["llm"] = llm_intent
        except asyncio.TimeoutError:
            logger.warning("LLM analysis timed out (30s), using rules-only result")
        except Exception as e:
            logger.warning(f"LLM analysis exception, using rules-only result: {e}")

        # Generate recommendations
        recommendations = risk_assessor._generate_recommendations(
            result["risk_level"],
            {"content": {"score": result["risk_score"]}}
        )

        return ContentCheckResponse(
            content=result["content"],
            content_type=result["content_type"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            fraud_category=result["fraud_category"],
            risk_factors=result["risk_factors"],
            key_entities=result["key_entities"],
            intent_analysis=result["intent_analysis"],
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Content detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/voice", response_model=VoiceCheckResponse)
async def check_voice(request: VoiceCheckRequest):
    """
    Check if an audio file is AI-synthesized

    - **audio_path**: Path to the audio file
    - **user_id**: User ID (optional)
    """
    try:
        # Detect audio
        result = await voice_detector.analyze_audio_file(request.audio_path)

        # Generate recommendations
        risk_level = risk_assessor._get_risk_level(result["risk_score"])
        recommendations = risk_assessor._generate_recommendations(
            risk_level,
            {"voice": {"score": result["risk_score"]}}
        )

        return VoiceCheckResponse(
            audio_path=result["audio_path"],
            risk_score=result["risk_score"],
            is_synthetic=result["is_synthetic"],
            confidence=result["confidence"],
            risk_factors=result["risk_factors"],
            recommendations=recommendations
        )
    except Exception as e:
        logger.error(f"Voice detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/comprehensive", response_model=ComprehensiveCheckResponse)
async def comprehensive_check(request: ComprehensiveCheckRequest):
    """
    Comprehensive detection (supports multiple types simultaneously)

    Can simultaneously detect URLs, SMS, calls, audio, and other content
    """
    try:
        url_result = None
        content_result = None
        voice_result = None

        # Run detections in parallel
        if request.url:
            url_data = await url_detector.analyze_url(request.url)
            url_risk_level = risk_assessor._get_risk_level(url_data["risk_score"])
            url_result = URLCheckResponse(
                url=url_data["url"],
                risk_score=url_data["risk_score"],
                risk_level=url_risk_level,
                is_suspicious=url_data["is_suspicious"],
                risk_factors=url_data["risk_factors"],
                recommendations=[]
            )

        if request.content:
            content_data = content_analyzer.analyze_content(request.content, request.content_type)
            # LLM deep analysis of content
            try:
                llm_intent = await asyncio.wait_for(
                    llm_service.analyze_intent(request.content),
                    timeout=30.0
                )
                if llm_intent and llm_intent.get("intent") != "unknown":
                    if llm_intent.get("intent") == "fraud" and llm_intent.get("confidence", 0) > 0.6:
                        boost = int(llm_intent["confidence"] * 30)
                        content_data["risk_score"] = min(100, content_data["risk_score"] + boost)
                        llm_factors = llm_intent.get("risk_factors", [])
                        for f in llm_factors:
                            if f"[LLM]" not in str(content_data.get("risk_factors", [])) and f not in content_data["risk_factors"]:
                                content_data["risk_factors"].append(f"[LLM] {f}")
                    content_data["intent_analysis"]["llm"] = llm_intent
            except Exception as e:
                logger.warning(f"Comprehensive detection LLM analysis exception: {e}")

            content_result = ContentCheckResponse(
                content=content_data["content"],
                content_type=content_data["content_type"],
                risk_score=content_data["risk_score"],
                risk_level=content_data["risk_level"],
                fraud_category=content_data["fraud_category"],
                risk_factors=content_data["risk_factors"],
                key_entities=content_data["key_entities"],
                intent_analysis=content_data["intent_analysis"],
                recommendations=[]
            )

        if request.audio_path:
            voice_data = await voice_detector.analyze_audio_file(request.audio_path)
            voice_risk_level = risk_assessor._get_risk_level(voice_data["risk_score"])
            voice_result = VoiceCheckResponse(
                audio_path=voice_data["audio_path"],
                risk_score=voice_data["risk_score"],
                is_synthetic=voice_data["is_synthetic"],
                confidence=voice_data["confidence"],
                risk_factors=voice_data["risk_factors"],
                recommendations=[]
            )

        # Comprehensive assessment
        assessment = await risk_assessor.assess_risk(
            url_result=url_result.model_dump() if url_result else None,
            content_result=content_result.model_dump() if content_result else None,
            voice_result=voice_result.model_dump() if voice_result else None,
            user_profile={"age": request.user_age} if request.user_age else None
        )

        # Generate explanation
        explanation = await llm_service.generate_explanation(
            {"risk_score": assessment["overall_risk_score"],
             "risk_factors": assessment.get("recommendations", [])},
            user_age=request.user_age
        )

        return ComprehensiveCheckResponse(
            overall_risk_score=assessment["overall_risk_score"],
            overall_risk_level=assessment["overall_risk_level"],
            url_result=url_result,
            content_result=content_result,
            voice_result=voice_result,
            recommendations=assessment["recommendations"],
            alert_message=assessment["alert_message"],
            explanation=explanation
        )
    except Exception as e:
        logger.error(f"Comprehensive detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
