import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class BofAParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = ['bank of america', 'bofa', 'bankofamerica.com']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_card_last_four(text)
        billing_cycle = self.extract_statement_period(text)
        due_date = self.extract_due_date(text)
        total_balance = self.extract_new_balance(text)
        minimum_payment = self.extract_minimum_payment(text)
        transactions = self.extract_transactions(text)
        
        return StatementData(
            issuer="Bank of America",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_statement_period(self, text: str) -> str:
        pattern = r'Statement (?:Period|Date):?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:through|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} - {match.group(2)}"
        return self.extract_date_range(text)
    
    def extract_new_balance(self, text: str) -> float:
        patterns = [
            r'New Balance:?\s*\$?([\d,]+\.?\d*)',
            r'Current Balance:?\s*\$?([\d,]+\.?\d*)',
            r'Total Balance:?\s*\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_minimum_payment(self, text: str) -> float:
        patterns = [
            r'Minimum Payment:?\s*\$?([\d,]+\.?\d*)',
            r'Minimum Amount Due:?\s*\$?([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_transactions(self, text: str) -> list:
        transactions = []
        # BofA format: MM/DD description amount
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