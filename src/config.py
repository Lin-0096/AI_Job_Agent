"""Configuration management for AI Job Agent"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _find_cv_file() -> str:
    """Auto-detect CV file in data directory"""
    data_dir = Path("data")

    # Check common CV filenames
    candidates = [
        "cv.pdf",
        "cv.txt",
        "CV.pdf",
        "CV.txt",
    ]

    # Also check for any PDF files in data directory
    for file in data_dir.glob("*.pdf"):
        if file.name.lower().endswith("cv.pdf") or "cv" in file.name.lower():
            return str(file)

    # Check predefined candidates
    for filename in candidates:
        path = data_dir / filename
        if path.exists():
            return str(path)

    return "data/cv.txt"  # Default fallback


@dataclass
class EmailConfig:
    """Email IMAP configuration"""

    host: str
    port: int
    user: str
    password: str
    search_days: int = 7
    search_from: str = "linkedin.com"
    unread_only: bool = False
    folder: str = "INBOX"  # Gmail folder to search in

    @classmethod
    def from_env(cls) -> "EmailConfig":
        """Load email config from environment variables"""
        return cls(
            host=os.getenv("EMAIL_HOST", "imap.gmail.com"),
            port=int(os.getenv("EMAIL_PORT", "993")),
            user=os.getenv("EMAIL_USER", ""),
            password=os.getenv("EMAIL_PASSWORD", ""),
            search_days=int(os.getenv("EMAIL_SEARCH_DAYS", "7")),
            search_from=os.getenv("EMAIL_SEARCH_FROM", "linkedin.com"),
            unread_only=os.getenv("EMAIL_UNREAD_ONLY", "false").lower() == "true",
            folder=os.getenv("EMAIL_FOLDER", "INBOX"),
        )

    def validate(self) -> None:
        """Validate required fields"""
        if not self.user:
            raise ValueError("EMAIL_USER is required")
        if not self.password:
            raise ValueError("EMAIL_PASSWORD is required")


@dataclass
class LLMConfig:
    """LLM API configuration"""

    api_key: str
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Load LLM config from environment variables"""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("LLM_BASE_URL"),
        )


@dataclass
class MatchConfig:
    """Enhanced matching configuration for reasoning models"""

    extract_model: str = "gpt-4o-mini"  # Lightweight model for JD extraction
    match_model: str = "o3-mini"  # Reasoning model for deep matching
    reasoning_effort: str = "low"  # low/medium/high
    use_enhanced: bool = True  # Enable enhanced matching system

    @classmethod
    def from_env(cls) -> "MatchConfig":
        """Load match config from environment variables"""
        return cls(
            extract_model=os.getenv("JD_EXTRACT_MODEL", "gpt-4o-mini"),
            match_model=os.getenv("MATCH_MODEL", "o3-mini"),
            reasoning_effort=os.getenv("REASONING_EFFORT", "low"),
            use_enhanced=os.getenv("USE_ENHANCED_MATCHING", "true").lower() == "true",
        )

    def validate(self) -> None:
        """Validate reasoning effort value"""
        if self.reasoning_effort not in ("low", "medium", "high"):
            raise ValueError(
                f"Invalid REASONING_EFFORT: {self.reasoning_effort}. "
                "Must be 'low', 'medium', or 'high'"
            )


@dataclass
class TwilioConfig:
    """Twilio WhatsApp configuration"""

    account_sid: str
    auth_token: str
    whatsapp_from: str
    whatsapp_to: str

    @classmethod
    def from_env(cls) -> "TwilioConfig":
        """Load Twilio config from environment variables"""
        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            whatsapp_from=os.getenv("TWILIO_WHATSAPP_FROM", ""),
            whatsapp_to=os.getenv("WHATSAPP_TO", ""),
        )


@dataclass
class NotificationConfig:
    """Notification configuration"""

    method: str = "gmail"  # "gmail" or "whatsapp"
    recipient_email: str = ""  # For Gmail notifications
    sender_name: str = "Job Agent"  # Display name for Gmail

    @classmethod
    def from_env(cls) -> "NotificationConfig":
        """Load notification config from environment variables"""
        return cls(
            method=os.getenv("NOTIFICATION_METHOD", "gmail").lower(),
            recipient_email=os.getenv("NOTIFICATION_EMAIL", ""),
            sender_name=os.getenv("NOTIFICATION_SENDER_NAME", "Job Agent"),
        )

    def validate(self) -> None:
        """Validate notification config"""
        if self.method not in ("gmail", "whatsapp"):
            raise ValueError(
                f"Invalid NOTIFICATION_METHOD: {self.method}. Must be 'gmail' or 'whatsapp'"
            )
        if self.method == "gmail" and not self.recipient_email:
            raise ValueError("NOTIFICATION_EMAIL is required when using Gmail notifications")
        if self.method == "whatsapp" and not self.recipient_email:
            raise ValueError("WHATSAPP_TO is required when using WhatsApp notifications")


@dataclass
class AppConfig:
    """Application configuration"""

    email: EmailConfig
    llm: LLMConfig
    twilio: TwilioConfig
    notification: NotificationConfig
    match: MatchConfig
    match_threshold: int = 50
    cv_path: str = "data/cv.txt"
    history_path: str = "data/history.json"

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load app config from environment variables"""
        notification = NotificationConfig.from_env()
        notification.validate()

        match = MatchConfig.from_env()
        match.validate()

        return cls(
            email=EmailConfig.from_env(),
            llm=LLMConfig.from_env(),
            twilio=TwilioConfig.from_env(),
            notification=notification,
            match=match,
            match_threshold=int(os.getenv("MATCH_THRESHOLD", "50")),
            cv_path=os.getenv("CV_PATH", _find_cv_file()),
            history_path=os.getenv("HISTORY_PATH", "data/history.json"),
        )


# Global config instance
config = AppConfig.from_env()
