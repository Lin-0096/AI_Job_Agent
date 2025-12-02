# Deployment Guide

## Deployment Options

Choose one of the following deployment methods:

1. **[GitHub Actions](#github-actions-recommended)** - Free, cloud-based, no server needed
2. **[Local Cron](#local-cron)** - Run on your local machine
3. **[Cloud VPS](#cloud-vps)** - Dedicated server for 24/7 operation

---

## GitHub Actions (Recommended)

**Best for**: Most users who want free, automated, cloud-based execution

**Pros**:
- ✅ Completely free (2000 minutes/month)
- ✅ No server or computer needed
- ✅ Runs in the cloud automatically
- ✅ Easy to set up and manage

**Setup**: See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed instructions.

**Quick Start**:
1. Extract CV text: `bash scripts/encode_cv.sh`
2. Add GitHub Secrets (EMAIL, API keys, CV_CONTENT, etc.)
3. Enable Actions in your repository
4. Done! Runs every 2 hours automatically

---

## Local Cron

**Best for**: Testing or if you have a computer that runs 24/7

## Scheduled Execution

### Linux/Mac (cron)

```bash
# Edit crontab
crontab -e

# Run every hour
0 * * * * cd /path/to/ai-job-agent && /path/to/venv/bin/python -m src.main >> logs/cron.log 2>&1
```

### Manual Execution

```bash
cd /home/xinma/ai_agent_study/projects/alert
source venv/bin/activate
python -m src.main
```

## Logging

Logs output to stdout, can be redirected to file:

```bash
python -m src.main >> logs/app.log 2>&1
```

## Environment Variable Checklist

Ensure `.env` configuration is complete:

```bash
# Required
EMAIL_USER
EMAIL_PASSWORD
OPENAI_API_KEY

# Optional (WhatsApp push)
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
WHATSAPP_TO
```

## Cloud VPS

**Best for**: Advanced users who want full control and 24/7 operation

**Recommended providers**:
- **Oracle Cloud** - Free tier (ARM instances)
- **DigitalOcean** - $6/month
- **Linode** - $5/month
- **Vultr** - $3.5/month

**Setup**:
```bash
# 1. SSH into your server
ssh user@your-server-ip

# 2. Clone repository
git clone https://github.com/xinyuanma/ai-job-agent.git
cd ai-job-agent

# 3. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure .env
cp .env.example .env
nano .env  # Add your credentials

# 5. Setup cron
crontab -e
# Add: 0 */2 * * * cd /path/to/ai-job-agent && /path/to/venv/bin/python -m src.main >> logs/cron.log 2>&1
```

---

## Troubleshooting

1. **Email reading failure** - Check Gmail app-specific password
2. **LLM matching failure** - Check OpenAI API key and balance
3. **WhatsApp push failure** - Check Twilio configuration and sandbox settings
4. **GitHub Actions fails** - Check [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) troubleshooting section
