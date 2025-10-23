import PyPDF2
import pdfplumber
import re
from typing import List, Dict, Any
from .ocr_utils import OCRProcessor

class EnhancedPDFExtractor:
    def __init__(self):
        self.ocr_processor = OCRProcessor()
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """Check if PDF is scanned (image-based) or text-based"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                # If very little text is extracted, it's likely scanned
                if not text or len(text.strip()) < 50:
                    return True
                
                # Check if text is mostly gibberish (bad OCR in PDF)
                words = text.split()
                if words:
                    # Check if most "words" are just symbols or numbers
                    readable_words = [w for w in words if re.match(r'^[a-zA-Z]+$', w)]
                    if len(readable_words) < len(words) * 0.3:
                        return True
                        
            return False
        except:
            return True
    
    def extract_text_hybrid(self, pdf_path: str) -> str:
        """
        Hybrid extraction: Try text extraction first, 
        fall back to OCR if needed
        """
        # First, try standard text extraction
        text = self.extract_text_pdfplumber(pdf_path)
        
        # Check if we got meaningful text
        if text and len(text.strip()) > 100:
            # Check text quality
            if self.is_text_quality_good(text):
                print("Using direct text extraction")
                return text
        
        # Fall back to OCR
        print("Falling back to OCR extraction")
        return self.extract_text_with_ocr(pdf_path)
    
    def is_text_quality_good(self, text: str) -> bool:
        """Check if extracted text is of good quality"""
        # Check for common credit card statement keywords
        keywords = ['balance', 'payment', 'account', 'statement', 
                   'transaction', 'credit', 'card', 'date', 'amount']
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
        
        # If we find several keywords, text is likely good
        return keyword_count >= 3
    
    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR"""
        all_text = []
        
        # Convert PDF to images
        images = self.ocr_processor.pdf_to_images(pdf_path)
        
        for i, image in enumerate(images):
            print(f"Processing page {i+1} with OCR...")
            
            # Extract text from image
            page_text = self.ocr_processor.extract_text_from_image(image)
            all_text.append(page_text)
        
        return "\n".join(all_text)
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except:
            pass
        return text
    
    def extract_with_confidence_scores(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text with confidence scores to determine
        which extraction method works best
        """
        results = {
            'text_extraction': {
                'text': '',
                'confidence': 0
            },
            'ocr_extraction': {
                'text': '',
                'confidence': 0
            },
            'best_method': '',
            'final_text': ''
        }
        
        # Try text extraction
        text_extracted = self.extract_text_pdfplumber(pdf_path)
        if text_extracted:
            results['text_extraction']['text'] = text_extracted
            results['text_extraction']['confidence'] = self.calculate_confidence(text_extracted)
        
        # Try OCR extraction
        ocr_extracted = self.extract_text_with_ocr(pdf_path)
        if ocr_extracted:
            results['ocr_extraction']['text'] = ocr_extracted
            results['ocr_extraction']['confidence'] = self.calculate_confidence(ocr_extracted)
        
        # Determine best method
        if results['text_extraction']['confidence'] > results['ocr_extraction']['confidence']:
            results['best_method'] = 'text_extraction'
            results['final_text'] = results['text_extraction']['text']
        else:
            results['best_method'] = 'ocr_extraction'
            results['final_text'] = results['ocr_extraction']['text']
        
        return results
    
    def calculate_confidence(self, text: str) -> float:
        """Calculate confidence score for extracted text"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Check for statement keywords
        keywords = ['statement', 'balance', 'payment', 'account', 'credit', 
                   'card', 'transaction', 'due', 'date', 'amount', 'total']
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                score += 0.1
        
        # Check for date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'[A-Za-z]+ \d{1,2}, \d{4}'
        ]
        for pattern in date_patterns:
            if re.search(pattern, text):
                score += 0.1
        
        # Check for amount patterns
        if re.search(r'\$[\d,]+\.?\d*', text):
            score += 0.2
        
        # Check for card number patterns
        if re.search(r'[Xx*]{4}[\s-]?[Xx*]{4}[\s-]?[Xx*]{4}[\s-]?\d{4}', text):
            score += 0.2
        
        return min(score, 1.0)