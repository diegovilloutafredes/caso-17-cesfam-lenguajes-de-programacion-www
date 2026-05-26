from datetime import date, datetime
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from services.common.db import Base
from services.common.enums import (
    UserRole,
    TreatmentType,
    PrescriptionStatus,
    WriteOffReason,
    WriteOffStatus,
    ReportType,
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    rut = Column(String(32), nullable=False)
    full_name = Column(String(200))
    email = Column(String(200))
    role = Column(String(50))


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    rut = Column(String(32), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    birth_date = Column(Date)
    address = Column(Text)
    phone = Column(String(50))
    email = Column(String(200))


class Medication(Base):
    __tablename__ = "medications"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    manufacturer = Column(String(200))
    type = Column(String(100))
    components = Column(Text)
    content = Column(String(200))
    packaging = Column(String(200))
    min_stock = Column(Integer, default=0)
    batches = relationship("Batch", back_populates="medication")


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    lot_number = Column(String(100))
    arrival_date = Column(Date)
    expiration_date = Column(Date)
    initial_quantity = Column(Integer, default=0)
    available_quantity = Column(Integer, default=0)
    medication = relationship("Medication", back_populates="batches")
    writeoffs = relationship("WriteOff", back_populates="batch")


class WriteOff(Base):
    __tablename__ = "writeoffs"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    reason = Column(String(50))
    quantity = Column(Integer, default=0)
    status = Column(String(50))
    expired_at = Column(Date)
    discard_date = Column(Date)
    batch = relationship("Batch", back_populates="writeoffs")


class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    emission_date = Column(DateTime, default=datetime.utcnow)
    pickup_deadline = Column(Date)
    treatment_type = Column(String(50))
    duration_days = Column(Integer)
    status = Column(String(50))
    next_scheduled_delivery = Column(Date)
    lines = relationship("PrescriptionLine", back_populates="prescription")


class PrescriptionLine(Base):
    __tablename__ = "prescription_lines"
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=True)
    doses_per_interval = Column(Integer)
    interval_hours = Column(Integer)
    dose_description = Column(Text)
    duration_days = Column(Integer)
    total_quantity = Column(Integer)
    prescription = relationship("Prescription", back_populates="lines")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50))
    generated_at = Column(DateTime, default=datetime.utcnow)
    parameters = Column(Text)
