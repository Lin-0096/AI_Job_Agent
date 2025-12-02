"""Utility functions for AI Job Agent"""

import os
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


class CVLoader:
    """Load CV from various file formats"""

    @staticmethod
    def load_cv(file_path: str) -> str:
        """Load CV content from file (supports .txt and .pdf)"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CV file not found: {file_path}")

        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".txt":
            return CVLoader._load_txt(file_path)
        elif extension == ".pdf":
            return CVLoader._load_pdf(file_path)
        else:
            raise ValueError(
                f"Unsupported CV file format: {extension}. "
                "Supported formats: .txt, .pdf"
            )

    @staticmethod
    def load_cv_with_paragraphs(file_path: str) -> str:
        """Load CV with paragraph numbers for evidence tracing.

        Each paragraph is prefixed with [Paragraph N] for easy reference
        in enhanced matching results.

        Returns:
            CV content with numbered paragraphs
        """
        raw_content = CVLoader.load_cv(file_path)
        return CVLoader._add_paragraph_numbers(raw_content)

    @staticmethod
    def _add_paragraph_numbers(content: str) -> str:
        """Add paragraph numbers to content for evidence tracing.

        Splits by double newlines and numbers each non-empty paragraph.
        """
        # Split by multiple newlines (2 or more)
        import re
        paragraphs = re.split(r'\n\s*\n', content)

        numbered = []
        para_num = 1

        for para in paragraphs:
            para = para.strip()
            if para:
                # Prefix with paragraph number
                numbered.append(f"[Paragraph {para_num}] {para}")
                para_num += 1

        return '\n\n'.join(numbered)

    @staticmethod
    def _load_txt(file_path: str) -> str:
        """Load text file"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    @staticmethod
    def _load_pdf(file_path: str) -> str:
        """Load PDF file using LangChain"""
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # Combine all pages
        content = "\n\n".join([doc.page_content for doc in documents])
        return content.strip()
