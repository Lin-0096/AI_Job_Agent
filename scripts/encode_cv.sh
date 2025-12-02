#!/bin/bash

# Helper script to extract CV text for GitHub Actions

echo "=== CV Text Extractor for GitHub Actions ==="
echo ""

# Check if CV file exists
CV_FILE=""
if [ -f "data/Lin Liu-CV.pdf" ]; then
    CV_FILE="data/Lin Liu-CV.pdf"
elif [ -f "data/cv.pdf" ]; then
    CV_FILE="data/cv.pdf"
elif [ -f "data/cv.txt" ]; then
    CV_FILE="data/cv.txt"
else
    echo "❌ Error: CV file not found!"
    echo ""
    echo "Please place your CV file in the data/ directory as one of:"
    echo "  - data/cv.pdf"
    echo "  - data/cv.txt"
    echo "  - data/CV.pdf"
    exit 1
fi

echo "✅ Found CV file: $CV_FILE"
echo ""

# Check if it's a PDF
if [[ "$CV_FILE" == *.pdf ]]; then
    echo "📄 Extracting text from PDF..."

    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Extract text using PyPDFLoader
    python -c "
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader('$CV_FILE')
documents = loader.load()
content = '\n\n'.join([doc.page_content for doc in documents])
print(content)
" > cv_text.txt

    if [ $? -eq 0 ]; then
        echo "✅ Done! Text content saved to: cv_text.txt"
    else
        echo "❌ Error: Failed to extract PDF content"
        exit 1
    fi
else
    # For text files, just copy
    echo "📝 Copying text file..."
    cp "$CV_FILE" cv_text.txt
    echo "✅ Done! Text content saved to: cv_text.txt"
fi

echo ""
echo "📋 Next steps:"
echo "   1. Open cv_text.txt and copy the entire content"
echo "   2. Go to: https://github.com/xinyuanma/ai-job-agent/settings/secrets/actions"
echo "   3. Click 'New repository secret'"
echo "   4. Name: CV_CONTENT"
echo "   5. Value: Paste the text content"
echo ""
echo "⚠️  Note: After copying, you can delete cv_text.txt for security"
