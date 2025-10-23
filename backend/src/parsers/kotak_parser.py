import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class KotakParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = [
            'kotak',
            'kotak mahindra bank',
            'kotak credit card',
            'kotak bank'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_kotak_card_number(text)
        billing_cycle = self.extract_kotak_billing_cycle(text)
        due_date = self.extract_kotak_due_date(text)
        total_balance = self.extract_kotak_balance(text)
        minimum_payment = self.extract_kotak_minimum(text)
        transactions = self.extract_kotak_transactions(text)
        
        return StatementData(
            issuer="Kotak Mahindra Bank",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_kotak_card_number(self, text: str) -> str:
        """Extract Kotak card last 4 digits"""
        patterns = [
            r'Card No:\s*\d{6}[Xx]{6}(\d{4})',
            r'\d{6}XXXXXX(\d{4})',
            r'Card.*?\d{4}[Xx*]{2}XX\s*XXXX\s*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_kotak_billing_cycle(self, text: str) -> str:
        """Extract billing cycle"""
        patterns = [
            r'Statement Period\s*(\d{1,2}-[A-Za-z]{3}-\d{4})\s*To\s*(\d{1,2}-[A-Za-z]{3}-\d{4})',
            r'Statement Date\s*(\d{1,2}-[A-Za-z]{3}-\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    return f"{match.group(1)} - {match.group(2)}"
                return f"Statement date: {match.group(1)}"
        return "N/A"
    
    def extract_kotak_due_date(self, text: str) -> str:
        """Extract payment due date"""
        patterns = [
            r'Due Date\s*(\d{1,2}-[A-Za-z]{3}-\d{4})',
            r'Payment Due Date\s*(\d{1,2}-[A-Za-z]{3}-\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_kotak_balance(self, text: str) -> float:
        """Extract total balance"""
        patterns = [
            r'Total Amount Due\s*\(Rs\.\)\s*([\d,]+\.?\d*)',
            r'Total Dues\s*([\d,]+\.?\d*)',
            r'Amount Due\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_kotak_minimum(self, text: str) -> float:
        """Extract minimum payment"""
        patterns = [
            r'Minimum Amount Due\s*([\d,]+\.?\d*)',
            r'Minimum Payment\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_kotak_transactions(self, text: str) -> list:
        """Extract transactions"""
        transactions = []
        
        # Kotak format: Date Transaction Details Spends Area Amount
        pattern = r'(\d{2}/\d{2}/\d{4})\s+([A-Z][A-Za-z0-9\s\-\.\*&]{3,50}?)\s+[A-Za-z]+\s+([\d,]+\.?\d*)'
        matches = re.findall(pattern, text, re.MULTILINE)
        
        for match in matches[:10]:
            try:
                date = match[0].strip()
                description = match[1].strip()
                
                # Clean description
                description = re.sub(r'\s+', ' ', description)
                
                # Skip payment entries
                if 'PAYMENT' in description.upper() or 'NEFT' in description.upper():
                    continue
                
                if len(description) < 3:
                    continue
                
                amount = self.extractor.extract_amount(match[2])
                
                if amount > 0:
                    trans = Transaction(
                        date=date,
                        description=description,
                        amount=amount
                    )
                    transactions.append(trans)
            except:
                continue
        
        return transactions