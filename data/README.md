# Data Directory

This directory stores project data files.

## File Descriptions

### Required Files (must be created manually)

1. **cv.txt** or **cv.pdf** - Your resume
   - Copy `cv_template.txt` to `cv.txt`
   - Replace with your actual resume content
   - PDF format is also supported
   - ⚠️ Note: This file is in .gitignore and won't be committed to Git

2. **history.json** - Record of pushed jobs
   - Copy `history_template.json` to `history.json`
   - System will automatically update this file
   - ⚠️ Note: This file is in .gitignore and won't be committed to Git

### Template Files

- `cv_template.txt` - CV template (can be committed to Git)
- `history_template.json` - History template (can be committed to Git)

## Quick Setup

```bash
# Run in data directory
cp cv_template.txt cv.txt
cp history_template.json history.json

# Then edit cv.txt with your actual information
```

## Privacy Protection

All files containing real personal information are configured in `.gitignore`:
- `data/cv.txt` - Won't be committed
- `data/cv.pdf` - Won't be committed
- `data/CV.*` - Won't be committed
- `data/history.json` - Won't be committed
- `data/emails/` - Won't be committed (if saving raw emails)

Only template files will be committed to version control.
