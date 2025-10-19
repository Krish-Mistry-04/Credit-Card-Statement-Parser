import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class CitiParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = ['citi', 'citibank', 'citigroup', 'citi.com']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_card_last_four(text)
        billing_cycle = self.extract_billing_period(text)
        due_date = self.extract_payment_due_date(text)
        total_balance = self.extract_balance(text)
        minimum_payment = self.extract_min_payment(text)
        transactions = self.extract_transactions(text)
        
        return StatementData(
            issuer="Citi",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_billing_period(self, text: str) -> str:
        pattern = r'Billing Period:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*-\s*(\d{1,2}/\d{1,2}/\d{2,4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return self.extract_date_range(text)
    
    def extract_payment_due_date(self, text: str) -> str:
        pattern = r'Payment Due Date:?\s*(\d{1,2}/\d{1,2}/\d{2,4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return self.extract_due_date(text)
    
    def extract_balance(self, text: str) -> float:
        patterns = [
            r'Balance Summary[\s\S]*?Current Balance:?\s*\$?([\d,]+\.?\d*)',
            r'New Balance:?\s*\$?([\d,]+\.?\d*)',
            r'Total Balance:?\s*\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_min_payment(self, text: str) -> float:
        patterns = [
            r'Minimum Payment Due:?\s*\$?([\d,]+\.?\d*)',
            r'Min\. Payment:?\s*\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_transactions(self, text: str) -> list:
        transactions = []
        # Citi format: MM/DD description amount
        pattern = r'(\d{1,2}/\d{1,2})\s+([^\$\n]+?)\s+\$?([\d,]+\.?\d*)'
        matches = re.findall(pattern, text)
        
        for match in matches[:10]:
            trans = Transaction(
                date=match[0],
                description=match[1].strip(),
                amount=self.extractor.extract_amount(match[2])
            )
            transactions.append(trans)
        
        return transactions