import PyPDF2
import pdfplumber
import re
from typing import List, Dict, Any

class PDFExtractor:
    @staticmethod
    def extract_text_pypdf2(pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text
    
    @staticmethod
    def extract_text_pdfplumber(pdf_path: str) -> str:
        """Extract text using pdfplumber for better table extraction"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    @staticmethod
    def extract_tables_pdfplumber(pdf_path: str) -> List[List[List[str]]]:
        """Extract tables from PDF"""
        all_tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)
        return all_tables
    
    @staticmethod
    def find_pattern(text: str, pattern: str, group: int = 1) -> str:
        """Find pattern in text and return matched group"""
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(group).strip()
        return None
    
    @staticmethod
    def extract_amount(text: str) -> float:
        """Extract monetary amount from text"""
        # Remove currency symbols and commas
        text = re.sub(r'[$,]', '', text)
        # Find numeric pattern
        match = re.search(r'[\d,]+\.?\d*', text)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
        return 0.0