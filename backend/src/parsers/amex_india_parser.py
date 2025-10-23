import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class AmexIndiaParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = [
            'american express', 
            'amex', 
            'americanexpress.co.in',
            'American Express Banking Corp',
            'AEBC'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_amex_card_number(text)
        billing_cycle = self.extract_amex_billing_cycle(text)
        due_date = self.extract_amex_due_date(text)
        total_balance = self.extract_amex_balance(text)
        minimum_payment = self.extract_amex_minimum(text)
        transactions = self.extract_amex_transactions(text)
        
        return StatementData(
            issuer="American Express",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_amex_card_number(self, text: str) -> str:
        """Extract Amex card number (15 digits)"""
        patterns = [
            r'Membership Number.*?[Xx*]{4}[-\s]*[Xx*]{6}[-\s]*(\d{5})',
            r'Card Number.*?[Xx*]{4}[-\s]*[Xx*]{6}[-\s]*(\d{5})',
            r'[Xx*]{4}[-\s]*[Xx*]{6}[-\s]*(\d{5})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_amex_billing_cycle(self, text: str) -> str:
        """Extract billing cycle from Amex statement"""
        patterns = [
            r'Statement Period.*?From\s+([A-Za-z]+\s+\d{1,2})\s+to\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
            r'Statement Period.*?(\d{1,2}/\d{1,2}/\d{4})\s*to\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Closing Date.*?([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                if match.lastindex == 2:
                    return f"{match.group(1)} - {match.group(2)}"
                else:
                    return f"Statement ending {match.group(1)}"
        return "N/A"
    
    def extract_amex_due_date(self, text: str) -> str:
        """Extract payment due date"""
        patterns = [
            r'Minimum Payment Due.*?([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
            r'Payment Due Date.*?(\d{1,2}/\d{1,2}/\d{4})',
            r'Due Date.*?(\d{1,2}/\d{1,2}/\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return "N/A"
    
    def extract_amex_balance(self, text: str) -> float:
        """Extract total balance"""
        patterns = [
            r'Closing Balance Rs\s*([\d,]+\.?\d*)',
            r'New Balance.*?Rs\s*([\d,]+\.?\d*)',
            r'Total Amount Due.*?Rs\s*([\d,]+\.?\d*)',
            r'Total Dues\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_amex_minimum(self, text: str) -> float:
        """Extract minimum payment"""
        patterns = [
            r'Min Payment Due Rs\s*([\d,]+\.?\d*)',
            r'Minimum Payment Due.*?Rs\s*([\d,]+\.?\d*)',
            r'Minimum Amount Due\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self.extractor.extract_amount(match.group(1))
        return 0.0
    
    def extract_amex_transactions(self, text: str) -> list:
        """Extract transactions from Amex statement"""
        transactions = []
        
        # Amex India format: Date Description Amount
        patterns = [
            r'([A-Za-z]{3}\s+\d{1,2})\s+([A-Z][A-Z0-9\s\-\.&]{3,50}?)\s+([\d,]+\.?\d*)',
            r'(\d{1,2}/\d{1,2}/\d{4})\s+([A-Z][A-Z0-9\s\-\.&]{3,50}?)\s+([\d,]+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            
            for match in matches[:10]:
                try:
                    date = match[0].strip()
                    description = match[1].strip()
                    amount_str = match[2]
                    
                    # Skip if description is too short
                    if len(description) < 3:
                        continue
                    
                    amount = self.extractor.extract_amount(amount_str)
                    
                    if amount > 0:
                        trans = Transaction(
                            date=date,
                            description=description,
                            amount=amount
                        )
                        transactions.append(trans)
                except:
                    continue
            
            if len(transactions) >= 5:
                break
        
        return transactions