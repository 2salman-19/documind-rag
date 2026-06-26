"""
Document processor for multiple file formats.

WHY: Separates file parsing logic from RAG pipeline.
Makes it easy to add new formats (PPTX, XLSX) without touching core RAG code.
Includes security validation to prevent malicious file uploads.
"""

import os
from pathlib import Path
from typing import Union
from pypdf import PdfReader
from docx import Document as DocxDocument


# Configuration
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class DocumentProcessor:
    """Handles parsing of multiple document formats."""
    
    @staticmethod
    def validate_file(file_path: str, filename: str) -> tuple[bool, str]:
        """
        Validates file extension and size.
        
        WHY: Security first - prevents malicious files and resource exhaustion.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"File type '{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            return False, f"File too large ({file_size/1024/1024:.2f}MB). Max: {MAX_FILE_SIZE_MB}MB"
        
        if file_size == 0:
            return False, "File is empty"
        
        return True, ""
    
    @staticmethod
    def extract_text(file_path: str, filename: str) -> str:
        """
        Extracts text from supported file formats.
        
        Args:
            file_path: Path to the saved file
            filename: Original filename (for extension detection)
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file format is unsupported
            RuntimeError: If extraction fails
        """
        ext = Path(filename).suffix.lower()
        
        try:
            if ext == '.pdf':
                return DocumentProcessor._extract_pdf(file_path)
            elif ext == '.docx':
                return DocumentProcessor._extract_docx(file_path)
            elif ext == '.txt':
                return DocumentProcessor._extract_txt(file_path)
            else:
                raise ValueError(f"Unsupported format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from {filename}: {str(e)}")
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Extracts text from PDF files."""
        reader = PdfReader(file_path)
        text_parts = []
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        text = '\n\n'.join(text_parts)
        
        if not text.strip():
            raise RuntimeError("PDF contains no extractable text (may be scanned image)")
        
        return text
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Extracts text from DOCX files."""
        doc = DocxDocument(file_path)
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        text = '\n\n'.join(text_parts)
        
        if not text.strip():
            raise RuntimeError("DOCX file contains no text")
        
        return text
    
    @staticmethod
    def _extract_txt(file_path: str) -> str:
        """Extracts text from TXT files."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        if not text.strip():
            raise RuntimeError("TXT file is empty")
        
        return text