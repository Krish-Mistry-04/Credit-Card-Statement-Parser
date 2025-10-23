import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class ICICIParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = [
            'icici bank',
            'icicibank',
            'icici credit card',
            'ICICI Bank Credit Cards'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_icici_card_number(text)
        billing_cycle = self.extract_icici_billing_cycle(text)
        due_date = self.extract_icici_due_date(text)
        total_balance = self.extract_icici_balance(text)
        minimum_payment = self.extract_icici_minimum(text)
        transactions = self.extract_icici_transactions(text)
        
        return StatementData(
            issuer="ICICI Bank",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_icici_card_number(self, text: str) -> str:
        """Extract ICICI card last 4 digits"""
        patterns = [
            r'Card Number\s*:\s*\d{4}\s*[Xx]{4}\s*[Xx]{4}\s*(\d{4})',
            r'\d{4}\s*XXXX\s*XXXX\s*(\d{3,4})',
            r'Card Account No\s*(\d{4}\s*XXXX\s*XXXX\s*\d{3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = match.group(1)
                # Extract only digits
                digits = re.sub(r'[^0-9]', '', result)
                if digits:
                    return digits[-4:] if len(digits) >= 4 else digits
        return "N/A"
    
    def extract_icici_billing_cycle(self, text: str) -> str:
        """Extract billing cycle"""
        patterns = [
            r'Statement Date\s*(\d{2}/\d{2}/\d{4})',
            r'Statement Period.*?From\s*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                if match.lastindex == 2:
                    return f"{match.group(1)} - {match.group(2)}"
                return f"Statement date: {match.group(1)}"
        return "N/A"
    
    def extract_icici_due_date(self, text: str) -> str:
        """Extract payment due date"""
        patterns = [
            r'Due Date\s*:\s*(\d{2}/\d{2}/\d{4})',
            r'Payment.*?Due.*?(\d{2}/\d{2}/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_icici_balance(self, text: str) -> float:
        """Extract total balance"""
        patterns = [
            r'Your Total Amount Due\s*`?\s*([\d,]+\.?\d*)',
            r'Total Amount Due\s*([\d,]+\.?\d*)',
            r'Total Dues\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_icici_minimum(self, text: str) -> float:
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
    
    def extract_icici_transactions(self, text: str) -> list:
        """Extract transactions"""
        transactions = []
        
        # ICICI format: Date Ref.Number Description Amount
        pattern = r'(\d{2}/\d{2}/\d{4})\s+\d+\s+([A-Z][A-Za-z0-9\s\-\.\*&]{3,50}?)\s+([\d,]+\.?\d*)'
        matches = re.findall(pattern, text, re.MULTILINE)
        
        for match in matches[:10]:
            try:
                date = match[0].strip()
                description = match[1].strip()
                
                # Clean description
                description = re.sub(r'\s+', ' ', description)
                
                # Skip certain entries
                skip_terms = ['PAYMENT', 'CREDIT CARD PAYMENT', 'INFINITY PAYMENT', 
                             'DISCOUNT', 'FINANCE CHARGES', 'GST', 'IGST']
                if any(skip in description.upper() for skip in skip_terms):
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