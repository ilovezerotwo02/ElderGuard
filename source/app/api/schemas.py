"""API Data Models"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class URLCheckRequest(BaseModel):
    """URL check request"""
    url: str = Field(..., description="URL to check")
    user_id: Optional[str] = Field(None, description="User ID")


class URLCheckResponse(BaseModel):
    """URL check response"""
    url: str
    risk_score: float
    risk_level: str
    is_suspicious: bool
    risk_factors: List[str]
    recommendations: List[str]


class ContentCheckRequest(BaseModel):
    """Content check request"""
    content: str = Field(..., description="SMS or call content to check")
    content_type: str = Field(default="sms", description="Content type: sms/call")
    user_id: Optional[str] = Field(None, description="User ID")


class ContentCheckResponse(BaseModel):
    """Content check response"""
    content: str
    content_type: str
    risk_score: float
    risk_level: str
    fraud_category: Optional[str]
    risk_factors: List[str]
    key_entities: List[Dict[str, str]]
    intent_analysis: Dict[str, Any]
    recommendations: List[str]


class VoiceCheckRequest(BaseModel):
    """Voice check request"""
    audio_path: str = Field(..., description="Audio file path")
    user_id: Optional[str] = Field(None, description="User ID")


class VoiceCheckResponse(BaseModel):
    """Voice check response"""
    audio_path: str
    risk_score: float
    is_synthetic: bool
    confidence: float
    risk_factors: List[str]
    recommendations: List[str]


class ComprehensiveCheckRequest(BaseModel):
    """Comprehensive check request"""
    url: Optional[str] = Field(None, description="URL")
    content: Optional[str] = Field(None, description="SMS/call content")
    content_type: Optional[str] = Field("sms", description="Content type")
    audio_path: Optional[str] = Field(None, description="Audio file path")
    user_id: Optional[str] = Field(None, description="User ID")
    user_age: Optional[int] = Field(None, description="User age")


class ComprehensiveCheckResponse(BaseModel):
    """Comprehensive check response"""
    overall_risk_score: float
    overall_risk_level: str
    url_result: Optional[URLCheckResponse] = None
    content_result: Optional[ContentCheckResponse] = None
    voice_result: Optional[VoiceCheckResponse] = None
    recommendations: List[str]
    alert_message: str
    explanation: str


class AlertResponse(BaseModel):
    """Alert response"""
    alert_id: int
    alert_level: str
    alert_message: str
    is_read: bool
    created_at: str


class KnowledgeItem(BaseModel):
    """Knowledge item"""
    id: int
    title: str
    content: str
    category: str
    tags: List[str]
    source: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    message: str
