"""Email reader node for fetching LinkedIn job alerts"""

import email
import imaplib
from datetime import datetime, timedelta
from email.message import Message
from typing import List

from src.config import EmailConfig


class EmailReader:
    """Read emails from Gmail IMAP"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.imap: imaplib.IMAP4_SSL | None = None

    def connect(self) -> None:
        """Connect to IMAP server"""
        self.imap = imaplib.IMAP4_SSL(self.config.host, self.config.port)
        self.imap.login(self.config.user, self.config.password)
        # Select the specified folder (supports Gmail labels)
        self._select_folder()

    def _select_folder(self) -> None:
        """Select the specified Gmail folder/label"""
        if not self.imap:
            raise RuntimeError("Not connected to IMAP server")
        
        folder = self.config.folder
        
        # For Gmail, try with and without quotes
        try:
            self.imap.select(folder)
            print(f"✅ Connected to folder: {folder}")
        except imaplib.IMAP4.error:
            # Try with quotes for Gmail labels with spaces
            try:
                quoted_folder = f'"{folder}"'
                self.imap.select(quoted_folder)
                print(f"✅ Connected to folder: {folder}")
            except imaplib.IMAP4.error:
                # Try Gmail label format: [Gmail]/Label
                try:
                    gmail_label = f"[Gmail]/{folder}"
                    self.imap.select(gmail_label)
                    print(f"✅ Connected to folder: {gmail_label}")
                except imaplib.IMAP4.error:
                    print(f"⚠️  Could not select folder '{folder}', using INBOX instead")
                    self.imap.select("INBOX")

    def disconnect(self) -> None:
        """Disconnect from IMAP server"""
        if self.imap:
            self.imap.close()
            self.imap.logout()

    def search_emails(self) -> List[str]:
        """Search for LinkedIn job alert emails"""
        if not self.imap:
            raise RuntimeError("Not connected to IMAP server")

        search_criteria = self._build_search_criteria()
        _, message_ids = self.imap.search(None, *search_criteria)

        if not message_ids[0]:
            return []

        return message_ids[0].split()

    def _build_search_criteria(self) -> List[str]:
        """Build IMAP search criteria"""
        criteria = []

        # Search by sender
        criteria.append(f'FROM "{self.config.search_from}"')

        # Search by date
        if self.config.search_days > 0:
            since_date = datetime.now() - timedelta(days=self.config.search_days)
            criteria.append(f'SINCE {since_date.strftime("%d-%b-%Y")}')

        # Search by read status
        if self.config.unread_only:
            criteria.append("UNSEEN")

        return criteria

    def fetch_email(self, message_id: bytes) -> Message:
        """Fetch a single email by ID"""
        if not self.imap:
            raise RuntimeError("Not connected to IMAP server")

        _, msg_data = self.imap.fetch(message_id, "(RFC822)")
        raw_email = msg_data[0][1]
        return email.message_from_bytes(raw_email)

    def extract_html(self, msg: Message) -> str:
        """Extract HTML content from email"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="ignore")
        else:
            if msg.get_content_type() == "text/html":
                payload = msg.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="ignore")

        return ""

    def fetch_recent_emails(self) -> List[str]:
        """Fetch recent LinkedIn job alert emails and return HTML content"""
        try:
            self.connect()
            message_ids = self.search_emails()

            html_emails = []
            for msg_id in message_ids:
                msg = self.fetch_email(msg_id)
                html = self.extract_html(msg)
                if html:
                    html_emails.append(html)

            return html_emails
        finally:
            self.disconnect()

    def list_folders(self) -> List[str]:
        """List all available folders/labels in Gmail"""
        try:
            self.connect()
            if not self.imap:
                return []
            
            _, mailboxes = self.imap.list()
            folders = []
            for mailbox in mailboxes:
                # Parse mailbox string - format: (flags) "/" "name"
                # Example: (b'\\All', b'\\HasNoChildren') b'/' b'INBOX'
                if isinstance(mailbox, bytes):
                    parts = mailbox.decode('utf-8').split('"/"')
                    if len(parts) >= 2:
                        folder_name = parts[-1].strip().strip('"')
                        folders.append(folder_name)
            
            return sorted(folders)
        finally:
            self.disconnect()



def read_emails(state: dict) -> dict:
    """LangGraph node: Read emails from inbox"""
    from src.config import config

    config.email.validate()
    reader = EmailReader(config.email)
    html_emails = reader.fetch_recent_emails()

    state["raw_emails"] = html_emails
    return state
