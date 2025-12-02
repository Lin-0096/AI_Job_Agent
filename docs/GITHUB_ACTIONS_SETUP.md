# GitHub Actions Setup Guide

This guide will help you set up automated job agent runs using GitHub Actions (completely free).

## Overview

GitHub Actions will:
- ✅ Run every 2 hours automatically (customizable)
- ✅ Check for new LinkedIn job emails
- ✅ Match jobs with your CV using LLM
- ✅ Send high-match jobs to WhatsApp
- ✅ Automatically save history back to the repository
- ✅ Run completely free (GitHub provides 2000 minutes/month)

## Step 1: Prepare Your CV (Text Content)

GitHub Actions needs your CV as a secret. We'll extract the text content from your CV.

### Using the Helper Script (Recommended):

```bash
cd /home/xinma/ai_agent_study/projects/alert
bash scripts/encode_cv.sh
```

This script will:
- Auto-detect your CV file (PDF or TXT)
- Extract text content from PDF using PyPDFLoader
- Save to `cv_text.txt`

### Manual Extraction:

**For PDF:**
```bash
source venv/bin/activate
python -c "
from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader('data/cv.pdf')
documents = loader.load()
content = '\n\n'.join([doc.page_content for doc in documents])
print(content)
" > cv_text.txt
```

**For Text File:**
```bash
cat data/cv.txt > cv_text.txt
```

**Copy the entire content of `cv_text.txt`** - you'll need it in the next step.

## Step 2: Configure GitHub Secrets

1. Go to your repository: https://github.com/xinyuanma/ai-job-agent

2. Click **Settings** → **Secrets and variables** → **Actions**

3. Click **New repository secret** and add each of the following:

### Required Secrets

| Secret Name | Value | Example |
|------------|-------|---------|
| `EMAIL_HOST` | Gmail IMAP host | `imap.gmail.com` |
| `EMAIL_PORT` | Gmail IMAP port | `993` |
| `EMAIL_USER` | Your Gmail address | `your_email@gmail.com` |
| `EMAIL_PASSWORD` | Gmail app password | `abcd efgh ijkl mnop` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | `ACxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | `xxxxxxxxx` |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp number | `whatsapp:+14155238886` |
| `WHATSAPP_TO` | Your WhatsApp number | `whatsapp:+358406650908` |
| `CV_CONTENT` | **CV text content** | Paste content from `cv_text.txt` |

### Optional Secrets (with defaults)

| Secret Name | Default Value | Description |
|------------|---------------|-------------|
| `EMAIL_SEARCH_DAYS` | `1` | How many days back to search |
| `EMAIL_SEARCH_FROM` | `linkedin.com` | Filter emails from this sender |
| `EMAIL_UNREAD_ONLY` | `false` | Only read unread emails |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `MATCH_THRESHOLD` | `75` | Minimum score to notify (0-100) |

## Step 3: Enable GitHub Actions

1. Go to your repository's **Actions** tab

2. If prompted, click **"I understand my workflows, go ahead and enable them"**

3. You should see the workflow **"Job Agent Scheduler"**

## Step 4: Test the Workflow

### Manual Test (Recommended First)

1. Go to **Actions** tab → **Job Agent Scheduler**

2. Click **Run workflow** → **Run workflow**

3. Wait a few minutes and check:
   - ✅ Workflow runs successfully (green checkmark)
   - ✅ You receive WhatsApp notifications for matched jobs
   - ✅ `data/history.json` is updated in the repository

### Check Logs

Click on the workflow run to see detailed logs:
- Email reading
- Job parsing
- LLM matching scores
- WhatsApp notifications sent

## Step 5: Customize Schedule

To change the run frequency, edit `.github/workflows/job-agent.yml`:

```yaml
on:
  schedule:
    # Examples:
    - cron: '0 */2 * * *'   # Every 2 hours
    - cron: '0 8,12,18 * * *'  # At 8am, 12pm, 6pm
    - cron: '0 9 * * 1-5'   # 9am on weekdays only
```

[Cron schedule reference](https://crontab.guru/)

## Troubleshooting

### Workflow fails with "Authentication failed"

- Check your `EMAIL_PASSWORD` secret - use Gmail **app-specific password**, not your regular password
- Go to https://myaccount.google.com/apppasswords to create one

### Workflow runs but no jobs found

- Check logs to see if emails were read
- Verify `EMAIL_SEARCH_FROM` and `EMAIL_SEARCH_DAYS` settings
- Make sure you have LinkedIn job alert emails

### CV file error

- Verify `CV_CONTENT` secret contains the extracted text content
- Make sure you copied the entire text from `cv_text.txt`
- For PDF CVs, ensure PyPDFLoader extracted content successfully

### WhatsApp not receiving messages

- Verify Twilio credentials
- Check Twilio console for any errors
- Ensure WhatsApp sandbox is properly configured

### History not updating

- Check that workflow has `contents: write` permission
- Verify the commit step in workflow logs

## Cost Estimate

**Completely FREE** for typical usage:
- GitHub Actions: Free (2000 min/month, each run ~2-3 min)
- Maximum runs per month: ~660 runs (more than enough)
- If running every 2 hours: 360 runs/month ✅

## Security Notes

⚠️ **Important**:
- Never commit `.env` file to Git
- All secrets are encrypted by GitHub
- Secrets are not visible in logs
- Use GitHub's secret scanning for extra protection

## Next Steps

After successful setup:
1. Monitor first few runs
2. Adjust `MATCH_THRESHOLD` if needed
3. Customize `cron` schedule
4. Check monthly GitHub Actions usage (Settings → Billing)

---

Need help? Check the [main README](../README.md) or [open an issue](https://github.com/xinyuanma/ai-job-agent/issues).
