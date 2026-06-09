from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Installation(Base):
    """
    Tracks every org/user that has installed the GitHub App.
    Created when GitHub fires the installation.created webhook event.
    """
    __tablename__ = "installations"

    id = Column(Integer, primary_key=True)
    installation_id = Column(Integer, unique=True, nullable=False)
    account_login = Column(String, nullable=False)   # org or user name
    account_type = Column(String, nullable=False)    # "Organization" or "User"
    installed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class RepoSettings(Base):
    """
    Per-repo configuration — loaded from .codelens.yml or set via API.
    """
    __tablename__ = "repo_settings"

    id = Column(Integer, primary_key=True)
    repo_full_name = Column(String, unique=True, nullable=False)
    installation_id = Column(Integer, nullable=False)
    enabled = Column(Boolean, default=True)
    excluded_paths = Column(Text, default="")       # comma-separated
    severity_threshold = Column(String, default="suggestion")  # suggestion | warning | error
    created_at = Column(DateTime, default=datetime.utcnow)