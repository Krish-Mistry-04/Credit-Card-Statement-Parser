from abc import ABC, abstractmethod
from models.statement import StatementData
from utils.pdf_utils import PDFExtractor
import re

class BaseParser(ABC):
    def __init__(self):
        self.extractor = PDFExtractor()
    
    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Check if this parser can handle the given text"""
        pass
    
    @abstractmethod
    def parse(self, pdf_path: str) -> StatementData:
        """Parse the PDF and extract statement data"""
        pass
    
    def extract_card_last_four(self, text: str) -> str:
        """Extract last 4 digits of card number"""
        patterns = [
            r'[Xx]{4}\s*[Xx]{4}\s*[Xx]{4}\s*(\d{4})',
            r'\*{4}\s*\*{4}\s*\*{4}\s*(\d{4})',
            r'ending\s+in\s+(\d{4})',
            r'Account\s+Number:?\s*[Xx\*\-]*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_date_range(self, text: str) -> str:
        """Extract billing cycle date range"""
        patterns = [
            r'(?:Statement Period|Billing Period|Statement Date):?\s*([\w\s]+\d{1,2},?\s*\d{4})\s*(?:to|-)\s*([\w\s]+\d{1,2},?\s*\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:to|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} - {match.group(2)}"
        return "N/A"
    
    def extract_due_date(self, text: str) -> str:
        """Extract payment due date"""
        patterns = [
            r'(?:Payment Due Date|Due Date|Payment Due):?\s*([\w\s]+\d{1,2},?\s*\d{4})',
            r'(?:Payment Due Date|Due Date):?\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"