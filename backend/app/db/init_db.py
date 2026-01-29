"""
Database initialization script for Zarqa al Yamama
Creates tables and initializes connections
"""

import logging
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Forecast(Base):
    """Forecast record model"""
    __tablename__ = "forecasts"
    
    request_id = Column(String(50), primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    scenario = Column(String(255), nullable=False)
    user_id = Column(String(100), nullable=True)
    
    # Temporal data
    temporal_forecast = Column(JSON, nullable=True)
    temporal_confidence = Column(Float, nullable=True)
    temporal_model = Column(String(100), nullable=True)
    
    # Context data
    context_sentiment = Column(JSON, nullable=True)
    context_confidence = Column(Float, nullable=True)
    context_themes = Column(JSON, nullable=True)
    
    # Quantified output
    quantified_forecast = Column(JSON, nullable=True)
    quantified_confidence = Column(Float, nullable=True)
    
    # Validation & Ethics
    validation_status = Column(String(50), nullable=True)
    ethical_status = Column(String(50), nullable=True)
    
    # Metadata
    processing_time_ms = Column(Float, nullable=True)
    agents_executed = Column(JSON, nullable=True)
    citation_chain = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)


class TimeSeries(Base):
    """Time-series data model"""
    __tablename__ = "timeseries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=True)


class NewsEvent(Base):
    """News event model"""
    __tablename__ = "news_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    title = Column(String(500), nullable=False)
    source = Column(String(100), nullable=False)
    sentiment_score = Column(Float, nullable=True)
    themes = Column(JSON, nullable=True)
    actors = Column(JSON, nullable=True)
    url = Column(String(500), nullable=True)


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    request_id = Column(String(50), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    """Initialize database and create tables"""
    try:
        logger.info(f"Initializing database: {settings.DATABASE_URL}")
        
        # Create engine
        engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        return engine
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise


import asyncio

def get_session(engine):
    """Get database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def _save_forecast_sync(engine, forecast_data: dict):
    """Sync helper for saving forecast"""
    session = get_session(engine)
    try:
        save_forecast(session, forecast_data)
    finally:
        session.close()

async def save_forecast_async(engine, forecast_data: dict):
    """Async wrapper for saving forecast"""
    await asyncio.to_thread(_save_forecast_sync, engine, forecast_data)


def _save_timeseries_sync(engine, metric: str, value: float, source: str = None, metadata: dict = None):
    """Sync helper for saving timeseries"""
    session = get_session(engine)
    try:
        save_timeseries(session, metric, value, source, metadata)
    finally:
        session.close()

async def save_timeseries_async(engine, metric: str, value: float, source: str = None, metadata: dict = None):
    """Async wrapper for saving timeseries"""
    await asyncio.to_thread(_save_timeseries_sync, engine, metric, value, source, metadata)


def _save_news_event_sync(engine, event_data: dict):
    """Sync helper for saving news event"""
    session = get_session(engine)
    try:
        save_news_event(session, event_data)
    finally:
        session.close()

async def save_news_event_async(engine, event_data: dict):
    """Async wrapper for saving news event"""
    await asyncio.to_thread(_save_news_event_sync, engine, event_data)


def _save_audit_log_sync(engine, request_id: str, action: str, details: str = None, status: str = None):
    """Sync helper for saving audit log"""
    session = get_session(engine)
    try:
        save_audit_log(session, request_id, action, details, status)
    finally:
        session.close()

async def save_audit_log_async(engine, request_id: str, action: str, details: str = None, status: str = None):
    """Async wrapper for saving audit log"""
    await asyncio.to_thread(_save_audit_log_sync, engine, request_id, action, details, status)

# Keep original sync functions for internal usage or legacy support
def save_forecast(session, forecast_data: dict):
    """Save forecast to database"""
    try:
        forecast = Forecast(
            request_id=forecast_data.get('request_id'),
            scenario=forecast_data.get('scenario'),
            user_id=forecast_data.get('user_id'),
            temporal_forecast=forecast_data.get('temporal_forecast'),
            temporal_confidence=forecast_data.get('temporal_confidence'),
            context_sentiment=forecast_data.get('context_sentiment'),
            context_confidence=forecast_data.get('context_confidence'),
            quantified_forecast=forecast_data.get('quantified_forecast'),
            quantified_confidence=forecast_data.get('quantified_confidence'),
            validation_status=str(forecast_data.get('validation_status')),
            ethical_status=str(forecast_data.get('ethical_status')),
            processing_time_ms=forecast_data.get('processing_time_ms'),
            agents_executed=forecast_data.get('agents_executed'),
            citation_chain=forecast_data.get('citation_chain'),
            errors=forecast_data.get('errors'),
            warnings=forecast_data.get('warnings')
        )
        
        session.add(forecast)
        session.commit()
        logger.info(f"Forecast saved: {forecast_data.get('request_id')}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving forecast: {str(e)}")
        raise


def save_timeseries(session, metric: str, value: float, source: str = None, metadata: dict = None):
    """Save time-series data"""
    try:
        ts = TimeSeries(
            metric=metric,
            value=value,
            source=source,
            metadata=metadata
        )
        
        session.add(ts)
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving time-series: {str(e)}")
        raise


def save_news_event(session, event_data: dict):
    """Save news event"""
    try:
        event = NewsEvent(
            title=event_data.get('title'),
            source=event_data.get('source'),
            sentiment_score=event_data.get('sentiment_score'),
            themes=event_data.get('themes'),
            actors=event_data.get('actors'),
            url=event_data.get('url')
        )
        
        session.add(event)
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving news event: {str(e)}")
        raise


def save_audit_log(session, request_id: str, action: str, details: str = None, status: str = None):
    """Save audit log entry"""
    try:
        log = AuditLog(
            request_id=request_id,
            action=action,
            details=details,
            status=status
        )
        
        session.add(log)
        session.commit()
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving audit log: {str(e)}")
        raise
