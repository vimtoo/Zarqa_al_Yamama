"""
Forecast Registry
Stores predictions with full context for calibration (Brier/CRPS scoring).
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from sqlalchemy import Column, String, DateTime, Float, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from app.db.init_db import engine, SessionLocal
from app.graph.contracts import (
    ForecastRecord,
    FusionResult,
    EvaluationMetrics,
    ModelVersions,
    TimeHorizon,
)

logger = logging.getLogger(__name__)

Base = declarative_base()


class ForecastRecordModel(Base):
    """SQLAlchemy model for forecast records."""
    
    __tablename__ = "forecast_registry"
    
    record_id = Column(String(36), primary_key=True)
    forecast_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scenario = Column(String(500), nullable=False, index=True)
    horizons = Column(JSON, nullable=False)  # List of TimeHorizon values
    
    # Serialized FusionResult
    outputs_json = Column(Text, nullable=True)
    
    # Evidence snapshot
    evidence_snapshot_json = Column(Text, nullable=True)
    
    # Model versions
    model_versions_json = Column(JSON, nullable=True)
    
    # Evaluation fields
    resolved = Column(Boolean, default=False)
    resolution_date = Column(DateTime, nullable=True)
    actual_outcome = Column(String(1000), nullable=True)
    brier_score = Column(Float, nullable=True)
    pinball_loss = Column(Float, nullable=True)
    crps = Column(Float, nullable=True)


class ForecastRegistry:
    """
    Registry for storing and retrieving forecast records.
    
    Provides:
    1. Forecast persistence for audit trail
    2. Calibration metric computation (Brier, CRPS)
    3. Historical query for pattern analysis
    """
    
    def __init__(self):
        self._initialized = False
    
    def initialize(self):
        """Create tables if they don't exist."""
        if not self._initialized:
            try:
                Base.metadata.create_all(bind=engine)
                self._initialized = True
                logger.info("Forecast Registry tables initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Forecast Registry: {e}")
    
    def save_forecast(self, record: ForecastRecord) -> bool:
        """
        Save a forecast record to the registry.
        
        Returns True if successful, False otherwise.
        """
        self.initialize()
        
        try:
            db_record = ForecastRecordModel(
                record_id=record.record_id,
                forecast_id=record.forecast_id,
                created_at=record.created_at,
                scenario=record.scenario,
                horizons=[h.value for h in record.horizons],
                outputs_json=record.outputs.model_dump_json() if record.outputs else None,
                evidence_snapshot_json=json.dumps(record.evidence_graph_snapshot),
                model_versions_json=record.model_versions.model_dump() if record.model_versions else None,
                resolved=record.evaluation.resolved,
                resolution_date=record.evaluation.resolution_date,
                actual_outcome=record.evaluation.actual_outcome,
                brier_score=record.evaluation.brier_score,
                pinball_loss=record.evaluation.pinball_loss,
                crps=record.evaluation.crps,
            )
            
            with SessionLocal() as session:
                session.add(db_record)
                session.commit()
            
            logger.info(f"Saved forecast record: {record.record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save forecast record: {e}")
            return False
    
    def get_forecast(self, record_id: str) -> Optional[ForecastRecord]:
        """Retrieve a forecast record by ID."""
        self.initialize()
        
        try:
            with SessionLocal() as session:
                db_record = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.record_id == record_id
                ).first()
                
                if not db_record:
                    return None
                
                return self._model_to_record(db_record)
                
        except Exception as e:
            logger.error(f"Failed to retrieve forecast record: {e}")
            return None
    
    def get_forecasts_by_scenario(
        self, 
        scenario: str, 
        limit: int = 100
    ) -> List[ForecastRecord]:
        """Retrieve forecast records for a scenario."""
        self.initialize()
        
        try:
            with SessionLocal() as session:
                db_records = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.scenario.ilike(f"%{scenario}%")
                ).order_by(
                    ForecastRecordModel.created_at.desc()
                ).limit(limit).all()
                
                return [self._model_to_record(r) for r in db_records]
                
        except Exception as e:
            logger.error(f"Failed to retrieve forecasts: {e}")
            return []
    
    def get_unresolved_forecasts(self, limit: int = 100) -> List[ForecastRecord]:
        """Get forecasts that haven't been resolved yet."""
        self.initialize()
        
        try:
            with SessionLocal() as session:
                db_records = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.resolved == False
                ).order_by(
                    ForecastRecordModel.created_at.asc()
                ).limit(limit).all()
                
                return [self._model_to_record(r) for r in db_records]
                
        except Exception as e:
            logger.error(f"Failed to retrieve unresolved forecasts: {e}")
            return []
    
    def resolve_forecast(
        self,
        record_id: str,
        actual_outcome: str,
        resolution_date: Optional[datetime] = None
    ) -> bool:
        """
        Mark a forecast as resolved with the actual outcome.
        
        This enables calibration scoring.
        """
        self.initialize()
        
        try:
            with SessionLocal() as session:
                db_record = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.record_id == record_id
                ).first()
                
                if not db_record:
                    logger.warning(f"Forecast record not found: {record_id}")
                    return False
                
                db_record.resolved = True
                db_record.resolution_date = resolution_date or datetime.utcnow()
                db_record.actual_outcome = actual_outcome
                
                session.commit()
                
            logger.info(f"Resolved forecast record: {record_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve forecast: {e}")
            return False
    
    def compute_brier_score(
        self,
        predicted_probability: float,
        actual_occurred: bool
    ) -> float:
        """
        Compute Brier score for a binary forecast.
        
        Brier = (predicted - actual)^2
        Lower is better. Range: 0 (perfect) to 1 (worst).
        """
        actual = 1.0 if actual_occurred else 0.0
        return (predicted_probability - actual) ** 2
    
    def compute_pinball_loss(
        self,
        predicted_quantile: float,
        actual_value: float,
        quantile: float = 0.5  # 0.5 = median
    ) -> float:
        """
        Compute pinball loss for a quantile forecast.
        
        Used for P10, P50, P90 evaluation.
        """
        error = actual_value - predicted_quantile
        if error >= 0:
            return quantile * error
        else:
            return (quantile - 1) * error
    
    def update_evaluation_metrics(
        self,
        record_id: str,
        brier_score: Optional[float] = None,
        pinball_loss: Optional[float] = None,
        crps: Optional[float] = None
    ) -> bool:
        """Update evaluation metrics for a resolved forecast."""
        self.initialize()
        
        try:
            with SessionLocal() as session:
                db_record = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.record_id == record_id
                ).first()
                
                if not db_record:
                    return False
                
                if brier_score is not None:
                    db_record.brier_score = brier_score
                if pinball_loss is not None:
                    db_record.pinball_loss = pinball_loss
                if crps is not None:
                    db_record.crps = crps
                
                session.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
            return False
    
    def get_calibration_stats(self, scenario_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Get aggregate calibration statistics.
        
        Returns average Brier, CRPS, and calibration bins.
        """
        self.initialize()
        
        try:
            with SessionLocal() as session:
                query = session.query(ForecastRecordModel).filter(
                    ForecastRecordModel.resolved == True
                )
                
                if scenario_pattern:
                    query = query.filter(
                        ForecastRecordModel.scenario.ilike(f"%{scenario_pattern}%")
                    )
                
                records = query.all()
                
                if not records:
                    return {"total_records": 0, "evaluated_records": 0}
                
                brier_scores = [r.brier_score for r in records if r.brier_score is not None]
                pinball_losses = [r.pinball_loss for r in records if r.pinball_loss is not None]
                crps_scores = [r.crps for r in records if r.crps is not None]
                
                return {
                    "total_records": len(records),
                    "evaluated_records": len(brier_scores),
                    "avg_brier_score": sum(brier_scores) / len(brier_scores) if brier_scores else None,
                    "avg_pinball_loss": sum(pinball_losses) / len(pinball_losses) if pinball_losses else None,
                    "avg_crps": sum(crps_scores) / len(crps_scores) if crps_scores else None,
                }
                
        except Exception as e:
            logger.error(f"Failed to get calibration stats: {e}")
            return {"error": str(e)}
    
    def _model_to_record(self, db_record: ForecastRecordModel) -> ForecastRecord:
        """Convert DB model to Pydantic record."""
        outputs = None
        if db_record.outputs_json:
            try:
                outputs = FusionResult.model_validate_json(db_record.outputs_json)
            except Exception as e:
                logger.warning(f"Failed to parse outputs JSON: {e}")
        
        model_versions = ModelVersions()
        if db_record.model_versions_json:
            try:
                model_versions = ModelVersions(**db_record.model_versions_json)
            except Exception:
                pass
        
        evidence_snapshot = {}
        if db_record.evidence_snapshot_json:
            try:
                evidence_snapshot = json.loads(db_record.evidence_snapshot_json)
            except Exception:
                pass
        
        return ForecastRecord(
            record_id=db_record.record_id,
            forecast_id=db_record.forecast_id,
            created_at=db_record.created_at,
            scenario=db_record.scenario,
            horizons=[TimeHorizon(h) for h in db_record.horizons],
            outputs=outputs,
            evidence_graph_snapshot=evidence_snapshot,
            model_versions=model_versions,
            evaluation=EvaluationMetrics(
                resolved=db_record.resolved,
                resolution_date=db_record.resolution_date,
                actual_outcome=db_record.actual_outcome,
                brier_score=db_record.brier_score,
                pinball_loss=db_record.pinball_loss,
                crps=db_record.crps,
            )
        )


# Singleton instance
forecast_registry = ForecastRegistry()
