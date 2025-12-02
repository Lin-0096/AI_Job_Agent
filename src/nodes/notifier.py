"""Notification node - supports Gmail and WhatsApp"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from datetime import datetime

from twilio.rest import Client

from src.config import config


class Notifier(ABC):
    """Base class for notification methods"""

    @abstractmethod
    def send_batch_notification(self, jobs: list) -> bool:
        """Send batch notification for multiple jobs"""
        pass

    @staticmethod
    def _email_styles() -> str:
        """Return shared CSS for Gmail template"""
        return """
        <style>
            :root {
                --brand: #10b981;
                --brand-strong: #059669;
                --bg: #f3f5f7;
                --card: #ffffff;
                --muted: #6b7280;
                --text: #111827;
                --border: #e5e7eb;
                --callout: #f8fafc;
            }
            body { margin: 0; padding: 0; background-color: var(--bg); font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; -webkit-font-smoothing: antialiased; color: var(--text); }
            a { color: var(--brand); text-decoration: none; }
            .container { max-width: 640px; margin: 24px auto; background: var(--card); border-radius: 12px; overflow: hidden; box-shadow: 0 6px 18px rgba(0,0,0,0.08); }
            .header { background: linear-gradient(135deg, var(--brand) 0%, var(--brand-strong) 100%); padding: 24px; text-align: center; color: #fff; }
            .header h1 { margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.4px; }
            .header p { margin: 8px 0 0 0; font-size: 13px; opacity: 0.92; }
            .content { padding: 4px 22px 22px 22px; }
            .job-card { padding: 20px; border: 1px solid var(--border); border-radius: 12px; background: #ffffff; margin: 16px 0; box-shadow: 0 3px 10px rgba(0,0,0,0.04); }
            .job-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
            .job-title { font-size: 18px; font-weight: 700; color: var(--text); margin: 6px 0 4px 0; display: block; }
            .job-meta { font-size: 13px; color: var(--muted); }
            .score-badge { display: inline-block; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; border: 1px solid #a7f3d0; background: #ecfdf5; color: #047857; }
            .score-med { background: #fffbeb; color: #b45309; border-color: #fde68a; }
            .score-low { background: #fef2f2; color: #b91c1c; border-color: #fecdd3; }
            .analysis-box { background: var(--callout); border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 6px; margin: 16px 0; font-size: 14px; line-height: 1.6; color: #334155; }
            .details-list { margin: 12px 0; font-size: 14px; line-height: 1.6; color: #1f2937; }
            .details-title { font-weight: 700; margin-bottom: 6px; }
            .detail-item { margin-bottom: 6px; display: flex; align-items: flex-start; }
            .detail-item .icon { margin-right: 8px; min-width: 18px; }
            .cta-row { margin-top: 18px; text-align: right; }
            .btn-apply { display: inline-block; background: var(--brand); color: #fff !important; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 14px; text-decoration: none; }
            .btn-apply:hover { background: var(--brand-strong); }
            .footer { background: #f9fafb; padding: 16px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid var(--border); }
        </style>
        """

    @staticmethod
    def _format_job_html(job: dict, index: int = None) -> str:
        """Format a single job as HTML with optional enhanced evaluation"""
        idx_str = f"{index}. " if index else ""
        title = job.get("title", "Unknown Role")
        company = job.get("company", "Unknown Company")
        location = job.get("location", "")
        link = job.get("link", "#")
        reasons = job.get("reasons", "No specific reasons provided.")
        score = int(job.get("score", 0))

        score_class = "score-high" if score >= 80 else "score-med" if score >= 50 else "score-low"
        enhanced = job.get("enhanced_result", {})
        enhanced_html = ""
        if enhanced:
            enhanced_html = Notifier._format_enhanced_job_html(job, idx_str, enhanced)

        return f"""
        <div class="job-card">
            <div class="job-header">
                <div>
                    <span class="score-badge {score_class}">Match {score}/100</span>
                    <a href="{link}" target="_blank" rel="noopener noreferrer" class="job-title">{idx_str}{title}</a>
                    <div class="job-meta">{company} • {location}</div>
                </div>
            </div>

            <div class="analysis-box">
                <strong>🤖 AI Insight</strong><br>
                {reasons}
            </div>

            {enhanced_html}

            <div class="cta-row">
                <a href="{link}" target="_blank" rel="noopener noreferrer" class="btn-apply">Apply Now →</a>
            </div>
        </div>
        """

    @staticmethod
    def _format_enhanced_job_html(job: dict, idx_str: str, enhanced: dict) -> str:
        """Format job with enhanced evaluation report"""
        sections: list[str] = []

        def _render_items(items: list[dict], icon: str, color: str, formatter) -> str:
            rendered = "".join(
                [
                    f'<div class="detail-item" style="color:{color};"><span class="icon">{icon}</span><span>{formatter(item)}</span></div>'
                    for item in items
                ]
            )
            return rendered

        strong_matches = enhanced.get("strong_matches", [])
        if strong_matches:
            items = _render_items(
                strong_matches[:3],
                "✅",
                "#1f2937",
                lambda m: f"{m.get('requirement', '')} — {m.get('evidence', '')}",
            )
            sections.append(f'<div class="details-list"><div class="details-title">Why you fit</div>{items}</div>')

        partial_matches = enhanced.get("partial_matches", [])
        if partial_matches:
            items = _render_items(
                partial_matches[:3],
                "⚠️",
                "#b45309",
                lambda m: f"{m.get('requirement', '')} — {m.get('evidence', '')} ({m.get('gap', '')})",
            )
            sections.append(f'<div class="details-list"><div class="details-title">Partial matches</div>{items}</div>')

        gaps = enhanced.get("gaps", [])
        if gaps:
            items = _render_items(
                gaps[:3],
                "❌",
                "#b91c1c",
                lambda m: f"{m.get('requirement', '')} — {m.get('reason', '')}",
            )
            sections.append(f'<div class="details-list"><div class="details-title">Gaps</div>{items}</div>')

        suggestions = enhanced.get("cv_suggestions", [])
        if suggestions:
            rendered = "".join(
                [
                    f'<div class="detail-item" style="color:#0f172a;"><span class="icon">💡</span><span>{s}</span></div>'
                    for s in suggestions[:3]
                ]
            )
            sections.append(f'<div class="details-list"><div class="details-title">CV suggestions</div>{rendered}</div>')

        return "".join(sections)


class GmailNotifier(Notifier):
    """Send email notifications via Gmail"""

    def __init__(self, email_user: str, email_password: str, recipient: str, sender_name: str = "Job Agent", dry_run: bool = False):
        self.email_user = email_user
        self.email_password = email_password
        self.recipient = recipient
        self.sender_name = sender_name
        self.dry_run = dry_run

    def send_batch_notification(self, jobs: list) -> bool:
        """Send batch notification for multiple jobs via Gmail"""
        if not jobs:
            return False

        try:
            # Build email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🎯 {len(jobs)} Job Match{'es' if len(jobs) > 1 else ''} - Job Agent"
            msg["From"] = f"{self.sender_name} <{self.email_user}>"
            msg["To"] = self.recipient

            # Create HTML content
            html_content = self._build_html_email(jobs)
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            if self.dry_run:
                print(f"[DRY RUN] Would send email to {self.recipient}")
                print(f"Subject: {msg['Subject']}")
                print(f"HTML Preview:\n{html_content}\n")
                return True

            # Send email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_user, self.email_password)
                server.send_message(msg)

            print(f"✅ Email sent to {self.recipient} with {len(jobs)} job(s)")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

    def _build_html_email(self, jobs: list) -> str:
        """Build HTML email content using modern template"""
        job_cards = "\n".join([self._format_job_html(job, i + 1) for i, job in enumerate(jobs)])
        current_date = datetime.now().strftime("%Y-%m-%d")
        match_text = f"Found {len(jobs)} match{'es' if len(jobs) > 1 else ''}"

        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                {self._email_styles()}
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 Job Match Report</h1>
                        <p>{current_date} • {match_text}</p>
                    </div>
                    <div class="content">
                        {job_cards}
                    </div>
                    <div class="footer">
                        <p>Job Agent · Powered by LangGraph & OpenAI</p>
                        <p style="margin-top:4px;">This is an automated message. Please do not reply.</p>
                    </div>
                </div>
            </body>
        </html>
        """


class WhatsAppNotifier(Notifier):
    """Send WhatsApp notifications via Twilio"""

    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_number: str, dry_run: bool = False):
        self.client = Client(account_sid, auth_token) if not dry_run else None
        self.from_number = from_number
        self.to_number = to_number
        self.dry_run = dry_run

    def send_batch_notification(self, jobs: list) -> bool:
        """Send batch notification for multiple jobs"""
        if not jobs:
            return False

        message = self._format_batch_message(jobs)

        if self.dry_run:
            print(f"[DRY RUN] Would send WhatsApp message:\n{message}\n")
            return True

        try:
            self.client.messages.create(
                body=message, from_=self.from_number, to=self.to_number
            )
            print(f"✅ WhatsApp message sent to {self.to_number} with {len(jobs)} job(s)")
            return True
        except Exception as e:
            print(f"❌ Failed to send WhatsApp message: {str(e)}")
            return False

    def _format_batch_message(self, jobs: list) -> str:
        """Format multiple jobs as single WhatsApp message"""
        count = len(jobs)
        header = f"🎯 Found {count} Matched Job{'s' if count > 1 else ''}\n"

        job_sections = []
        for idx, job in enumerate(jobs, 1):
            # Check for enhanced result
            enhanced = job.get("enhanced_result", {})
            if enhanced and (enhanced.get("strong_matches") or enhanced.get("gaps")):
                section = self._format_enhanced_whatsapp(job, idx, enhanced)
            else:
                section = f"""━━━━━━━━━━━━━━━━━━━
{idx}️⃣ Score: {job['score']}/100
{job['title']}
{job['company']} • {job['location']}

{job['reasons']}

🔗 {job['link']}"""
            job_sections.append(section)

        return header + "\n".join(job_sections)

    def _format_enhanced_whatsapp(self, job: dict, idx: int, enhanced: dict) -> str:
        """Format job with enhanced evaluation for WhatsApp"""
        lines = [
            f"━━━━━━━━━━━━━━━━━━━",
            f"{idx}️⃣ Score: {job['score']}/100",
            f"{job['title']}",
            f"{job['company']} • {job['location']}",
            "",
        ]

        # Strong matches
        if enhanced.get("strong_matches"):
            lines.append("✅ Matches:")
            for m in enhanced["strong_matches"][:3]:  # Limit to 3 for brevity
                lines.append(f"  • {m.get('requirement', '')}")

        # Gaps
        if enhanced.get("gaps"):
            lines.append("❌ Gaps:")
            for m in enhanced["gaps"][:2]:  # Limit to 2
                lines.append(f"  • {m.get('requirement', '')}")

        # Suggestions (1 only)
        if enhanced.get("cv_suggestions"):
            lines.append(f"💡 {enhanced['cv_suggestions'][0]}")

        lines.append("")
        lines.append(f"🔗 {job['link']}")

        return "\n".join(lines)


def notify_jobs(state: dict) -> dict:
    """LangGraph node: Send notifications for filtered jobs"""
    filtered_jobs = state.get("filtered_jobs", [])

    # Skip if no jobs
    if not filtered_jobs:
        state["notifications_sent"] = 0
        return state

    notification_config = config.notification
    method = notification_config.method

    try:
        if method == "gmail":
            notifier = GmailNotifier(
                email_user=config.email.user,
                email_password=config.email.password,
                recipient=notification_config.recipient_email,
                sender_name=notification_config.sender_name,
                dry_run=False,
            )
        elif method == "whatsapp":
            # Validate WhatsApp config
            if not config.twilio.account_sid or not config.twilio.auth_token:
                print("❌ WhatsApp is configured but Twilio credentials are missing")
                state["notifications_sent"] = 0
                return state

            notifier = WhatsAppNotifier(
                account_sid=config.twilio.account_sid,
                auth_token=config.twilio.auth_token,
                from_number=config.twilio.whatsapp_from,
                to_number=config.twilio.whatsapp_to,
                dry_run=False,
            )
        else:
            print(f"❌ Unknown notification method: {method}")
            state["notifications_sent"] = 0
            return state

        # Send notification
        if notifier.send_batch_notification(filtered_jobs):
            state["notifications_sent"] = len(filtered_jobs)
        else:
            state["notifications_sent"] = 0

    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        state["notifications_sent"] = 0

    return state


# Backward compatibility - keep old function name
def notify_whatsapp(state: dict) -> dict:
    """Deprecated: Use notify_jobs instead"""
    return notify_jobs(state)
