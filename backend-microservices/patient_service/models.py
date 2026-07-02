from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patient_service.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "PAT-001"
    rut: Mapped[str] = mapped_column(String)
    firstName: Mapped[str] = mapped_column(String)
    lastName: Mapped[str] = mapped_column(String)
    birthDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    # PatientCard embebido como columnas
    patientCardNumber: Mapped[str | None] = mapped_column(String, nullable=True)
    patientCardIssueDate: Mapped[date | None] = mapped_column(Date, nullable=True)

    guardians: Mapped[list["Guardian"]] = relationship(
        back_populates="patient", cascade="all, delete-orphan", lazy="selectin"
    )


class Guardian(Base):
    __tablename__ = "guardians"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "GRD-001"
    patientId: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    rut: Mapped[str] = mapped_column(String)
    firstName: Mapped[str] = mapped_column(String)
    lastName: Mapped[str] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    # relationship_ porque 'relationship' choca con SQLAlchemy
    relationship_: Mapped[str] = mapped_column("relationship", String)
    authorizationDate: Mapped[date | None] = mapped_column(Date, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="guardians")
