"""Database Model Definitions"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database.session import Base


class DetectionRecord(Base):
    """Detection record table"""
    __tablename__ = "detection_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, comment="User ID")
    detection_type = Column(String(50), index=True, comment="Detection type: url/sms/call/voice")
    content = Column(Text, comment="Detection content")
    risk_level = Column(String(20), comment="Risk level: safe/low/medium/high/critical")
    risk_score = Column(Float, comment="Risk score 0-100")
    detection_result = Column(JSON, comment="Detailed detection result")
    is_confirmed_fraud = Column(Boolean, default=False, comment="Whether confirmed as fraud")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FraudSample(Base):
    """Fraud sample library"""
    __tablename__ = "fraud_samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_type = Column(String(50), index=True, comment="Sample type: url/sms/call/voice")
    content = Column(Text, comment="Sample content")
    fraud_category = Column(String(100), comment="Fraud category")
    description = Column(Text, comment="Description")
    threat_level = Column(String(20), comment="Threat level")
    source = Column(String(200), comment="Source")
    is_active = Column(Boolean, default=True, comment="Whether active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NormalSample(Base):
    """Normal sample library"""
    __tablename__ = "normal_samples"

    id = Column(Integer, primary_key=True, index=True)
    sample_type = Column(String(50), index=True, comment="Sample type")
    content = Column(Text, comment="Sample content")
    category = Column(String(100), comment="Category")
    description = Column(Text, comment="Description")
    source = Column(String(200), comment="Source")
    is_active = Column(Boolean, default=True, comment="Whether active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserBehaviorBaseline(Base):
    """User behavior baseline data"""
    __tablename__ = "user_behavior_baselines"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, unique=True, comment="User ID")
    behavior_data = Column(JSON, comment="Behavior baseline data")
    risk_tolerance = Column(Float, default=50.0, comment="Risk tolerance")
    contact_list = Column(JSON, comment="Frequent contacts")
    frequent_urls = Column(JSON, comment="Frequently visited URLs")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ThreatIntel(Base):
    """Threat intelligence cache"""
    __tablename__ = "threat_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    indicator_type = Column(String(50), index=True, comment="Indicator type: domain/ip/phone/email")
    indicator_value = Column(String(500), index=True, comment="Indicator value")
    threat_type = Column(String(100), comment="Threat type")
    confidence = Column(Float, comment="Confidence level")
    source = Column(String(200), comment="Source")
    expires_at = Column(DateTime(timezone=True), comment="Expiration time")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class KnowledgeBase(Base):
    """RAG knowledge base"""
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), comment="Title")
    content = Column(Text, comment="Content")
    category = Column(String(100), index=True, comment="Category: fraud_case/prevention_guide/news")
    tags = Column(JSON, comment="Tags")
    embedding = Column(Text, comment="Vector embedding (JSON string)")
    source = Column(String(500), comment="Source")
    is_active = Column(Boolean, default=True, comment="Whether active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AlertRecord(Base):
    """Alert record"""
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, comment="User ID")
    detection_id = Column(Integer, comment="Associated detection record ID")
    alert_level = Column(String(20), comment="Alert level: low/medium/high/critical")
    alert_message = Column(Text, comment="Alert message")
    is_read = Column(Boolean, default=False, comment="Whether read")
    action_taken = Column(String(200), comment="Action taken")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
