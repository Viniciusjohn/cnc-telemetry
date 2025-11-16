# backend/app/db.py
# Database connection and models (SQLAlchemy + TimescaleDB)

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Float, String, DateTime, BigInteger, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from .config import settings

# Database URL from centralized settings
DATABASE_URL = settings.database_url

# Engine with connection pooling (disable pools for SQLite file/memory)
engine_args = {
    "echo": False,
}

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, **engine_args)
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        **engine_args,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==========================================
# ORM Models
# ==========================================

class Telemetry(Base):
    """Main telemetry table (hypertable in TimescaleDB)"""
    __tablename__ = "telemetry"
    
    ts = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    machine_id = Column(String(50), primary_key=True, nullable=False)
    rpm = Column(Float, nullable=False)
    feed_mm_min = Column(Float, nullable=False)
    state = Column(String(20), nullable=False)
    sequence = Column(BigInteger, nullable=True)
    src = Column(String(20), default="mtconnect")
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint('rpm >= 0', name='check_rpm_positive'),
        CheckConstraint('feed_mm_min >= 0', name='check_feed_positive'),
        CheckConstraint("state IN ('running','stopped','idle')", name='check_state_valid'),
    )


class TelemetryEvents(Base):
    """Telemetry events history for v0.2 - stores snapshots for event log"""
    __tablename__ = "telemetry_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    machine_id = Column(String(50), nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    mode = Column(String(20), nullable=True)
    execution = Column(String(20), nullable=False)
    rpm = Column(Float, nullable=False)
    feed_rate = Column(Float, nullable=True)
    spindle_load_pct = Column(Float, nullable=True)
    tool_id = Column(String(20), nullable=True)
    alarm_code = Column(String(50), nullable=True)
    alarm_message = Column(String(200), nullable=True)
    part_count = Column(BigInteger, nullable=True)
    controller_family = Column(String(50), nullable=True)
    source = Column(String(50), default="mtconnect:sim")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint('rpm >= 0', name='check_events_rpm_positive'),
        CheckConstraint("execution IN ('EXECUTING','STOPPED','READY','ALARM')", name='check_events_execution_valid'),
    )


class OEEDaily(Base):
    """OEE calculation table"""
    __tablename__ = "oee_daily"
    
    date = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    machine_id = Column(String(50), primary_key=True, nullable=False)
    shift = Column(String(20), primary_key=True, nullable=False)
    planned_time_min = Column(Float, nullable=False)
    operating_time_min = Column(Float, nullable=False)
    availability = Column(Float)
    performance = Column(Float, default=1.0)
    quality = Column(Float, default=1.0)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint('availability >= 0 AND availability <= 1', name='check_availability_range'),
        CheckConstraint('performance >= 0 AND performance <= 1', name='check_performance_range'),
        CheckConstraint('quality >= 0 AND quality <= 1', name='check_quality_range'),
        CheckConstraint("shift IN ('morning','afternoon','night','daily')", name='check_shift_valid'),
    )


# ==========================================
# Dependency injection for FastAPI
# ==========================================

def get_db():
    """FastAPI dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions (non-FastAPI)"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ==========================================
# Helper functions
# ==========================================

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"✅ Database connected: {version}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
