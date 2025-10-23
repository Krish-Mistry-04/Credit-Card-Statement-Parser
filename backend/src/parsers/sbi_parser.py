import re
from models.statement import StatementData, Transaction
from parsers.base_parser import BaseParser

class SBIParser(BaseParser):
    def can_parse(self, text: str) -> bool:
        indicators = [
            'state bank of india',
            'sbi',
            'sbichq',
            'sbin'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        card_last_four = self.extract_sbi_card_number(text)
        billing_cycle = self.extract_sbi_billing_cycle(text)
        due_date = "N/A"  # SBI statement doesn't have due date for savings
        total_balance = self.extract_sbi_balance(text)
        minimum_payment = 0.0  # N/A for savings account
        transactions = self.extract_sbi_transactions(text)
        
        return StatementData(
            issuer="State Bank of India",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def extract_sbi_card_number(self, text: str) -> str:
        """Extract SBI account number"""
        patterns = [
            r'Account Number\s*:\s*(\d{11,17})',
            r'A/c\s*No\.?\s*:\s*(\d{11,17})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1)
                return number[-4:] if len(number) >= 4 else number
        return "N/A"
    
    def extract_sbi_billing_cycle(self, text: str) -> str:
        """Extract statement period"""
        patterns = [
            r'Account Statement from\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s*to\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',
            r'Statement.*?(\d{1,2}/\d{1,2}/\d{4})\s*to\s*(\d{1,2}/\d{1,2}/\d{4})',
            r'Date\s*:\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    return f"{match.group(1)} - {match.group(2)}"
                return f"Statement date: {match.group(1)}"
        return "N/A"
    
    def extract_sbi_balance(self, text: str) -> float:
        """Extract balance"""
        # Look for the last balance in the statement
        pattern = r'Balance.*?([\d,]+\.?\d*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            # Return the last balance found
            return self.extractor.extract_amount(matches[-1])
        return 0.0
    
    def extract_sbi_transactions(self, text: str) -> list:
        """Extract transactions from SBI statement"""
        transactions = []
        
        # SBI format: Date Value Date Description Ref No./Cheque No. Debit Credit Balance
        pattern = r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+([A-Z][A-Za-z0-9\s\-\.\*&]{3,50}?)\s+[\w/\-]+\s+([\d,]+\.?\d*)'
        matches = re.findall(pattern, text, re.MULTILINE)
        
        for match in matches[:10]:
            try:
                date = match[0].strip()
                description = match[1].strip()
                
                # Clean description
                description = re.sub(r'\s+', ' ', description)
                
                # Skip certain entries
                skip_terms = ['TRANSFER', 'PAYMENT', 'CREDIT', 'WITHDRAWAL', 'NEFT']
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