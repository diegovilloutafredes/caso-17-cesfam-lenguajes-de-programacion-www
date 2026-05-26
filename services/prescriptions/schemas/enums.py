from enum import Enum


class UserRole(str, Enum):
    DOCTOR = "doctor"
    PHARMACY_STAFF = "pharmacy_staff"


class PrescriptionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    RESERVED = "RESERVED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    PICKED_UP = "PICKED_UP"
    EXTERNAL_PURCHASE = "EXTERNAL_PURCHASE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class TreatmentType(str, Enum):
    SHORT = "SHORT"
    LONG = "LONG"


class NotificationType(str, Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ERROR = "ERROR"


class WriteOffStatus(str, Enum):
    DEDUCTED_FROM_AVAILABLE = "DEDUCTED_FROM_AVAILABLE"
    DISCARDED = "DISCARDED"


class WriteOffReason(str, Enum):
    EXPIRATION = "EXPIRATION"
    DAMAGED = "DAMAGED"
    BROKEN_PACKAGE = "BROKEN_PACKAGE"
    OTHER = "OTHER"


class ReportType(str, Enum):
    STOCK = "STOCK"
    RESERVED = "RESERVED"
    EXPIRED = "EXPIRED"


class NotificationEvent(str, Enum):
    STOCK_ARRIVED = "STOCK_ARRIVED"
    RESERVATION_AVAILABLE = "RESERVATION_AVAILABLE"
    PICKUP_REMINDER = "PICKUP_REMINDER"
