from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    category = Column(String(50))
    location = Column(String(200))
    installation_date = Column(DateTime)
    status = Column(String(20), default="normal")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fault_cases = relationship("FaultCase", back_populates="device")
    maintenance_records = relationship("MaintenanceRecord", back_populates="device", order_by="MaintenanceRecord.created_at.desc()")
    issue_reports = relationship("IssueReport", back_populates="device", order_by="IssueReport.created_at.desc()")


class FaultCase(Base):
    __tablename__ = "fault_cases"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    fault_type = Column(String(50), nullable=False)
    fault_phenomenon = Column(Text, nullable=False)
    fault_reason = Column(Text)
    solution = Column(Text)
    maintenance_record = Column(Text)
    severity = Column(String(20))
    status = Column(String(20), default="open")
    reported_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("Device", back_populates="fault_cases")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(20))
    content = Column(Text)
    chunk_count = Column(Integer, default=0)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    error_message = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    maintenance_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    technician = Column(String(100))
    cost = Column(Float, default=0)
    parts_replaced = Column(Text)
    next_maintenance_date = Column(DateTime)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("Device", back_populates="maintenance_records")


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    issue_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    priority = Column(String(20), default="normal")
    status = Column(String(20), default="open")
    reporter_name = Column(String(100), nullable=False)
    reporter_department = Column(String(100))
    assignee_name = Column(String(100))
    assignee_department = Column(String(100))
    location = Column(String(200))
    attachment_url = Column(String(500))
    progress_percent = Column(Integer, default=0)
    due_date = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("Device", back_populates="issue_reports")
    progress_logs = relationship("WorkProgress", back_populates="issue", order_by="WorkProgress.created_at.desc()")


class WorkProgress(Base):
    __tablename__ = "work_progress"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issue_reports.id"), nullable=False)
    user_name = Column(String(100), nullable=False)
    user_department = Column(String(100))
    progress_note = Column(Text, nullable=False)
    progress_percent = Column(Integer)
    status = Column(String(20))
    action_taken = Column(Text)
    hours_spent = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    issue = relationship("IssueReport", back_populates="progress_logs")


class ProviderType(str, enum.Enum):
    THIRD_PARTY = "third_party"
    LOCAL = "local"


class ModelProvider(Base):
    __tablename__ = "model_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    provider_type = Column(Enum(ProviderType), default=ProviderType.THIRD_PARTY)
    provider_name = Column(String(50), nullable=False)
    api_base = Column(String(500), nullable=False)
    api_key = Column(String(500), default="")
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2048)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    extra_config = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
