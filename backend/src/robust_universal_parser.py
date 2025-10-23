"""
Robust Universal Parser
Handles multiple PDF formats and extraction methods
"""

import re
import pdfplumber
import pandas as pd
from typing import List, Dict, Optional, Tuple

class RobustExtractor:
    """Enhanced extractor with multiple fallback strategies"""
    
    def __init__(self):
        self.debug = False
    
    def extract_all_methods(self, pdf_path: str) -> Dict:
        """Try multiple extraction methods"""
        result = {
            'text_simple': '',
            'text_layout': '',
            'tables_default': [],
            'tables_alt': [],
            'all_text_blocks': []
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            all_text_simple = []
            all_text_layout = []
            
            for page in pdf.pages:
                # Method 1: Simple text
                text = page.extract_text()
                if text:
                    all_text_simple.append(text)
                
                # Method 2: Layout-preserving
                layout = page.extract_text(layout=True)
                if layout:
                    all_text_layout.append(layout)
                
                # Method 3: Tables - default settings
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 0:
                            result['tables_default'].append({
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table[0] else 0
                            })
                
                # Method 4: Tables - alternative settings
                table_settings = {
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                    "intersection_tolerance": 3
                }
                tables_alt = page.extract_tables(table_settings=table_settings)
                if tables_alt:
                    for table in tables_alt:
                        if table and len(table) > 0:
                            result['tables_alt'].append({
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table[0] else 0
                            })
            
            result['text_simple'] = '\n'.join(all_text_simple)
            result['text_layout'] = '\n'.join(all_text_layout)
        
        return result
    
    def smart_search(self, text: str, patterns: List[str], context_chars: int = 150) -> Optional[str]:
        """Search with multiple patterns and return best match"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None
    
    def extract_card_number(self, extraction: Dict) -> str:
        """Extract card number with multiple strategies"""
        text = extraction['text_layout'] or extraction['text_simple']
        
        patterns = [
            # 16-digit cards
            r'(?:Card\s+(?:Number|No\.?|Account\s+No\.?))[\s:]*(\d{4})[\s\*Xx-]*(\d{4}|\d{2}[Xx]{2})[\s\*Xx-]*[Xx\*]{4}[\s\*Xx-]*(\d{4})',
            r'(\d{4})[\s-](\d{2})[Xx]{2}[\s-][Xx]{4}[\s-](\d{4})',
            
            # 15-digit cards (Amex)
            r'(?:Membership|Card)\s+Number[\s:]*[Xx\*]{4}[\s-]*[Xx\*]{6}[\s-]*(\d{5})',
            r'[Xx\*]{4}[\s-]*[Xx\*]{6}[\s-]*(\d{5})',
            
            # Account numbers
            r'(?:Account|A/c)\s+(?:Number|No\.?)[\s:]*(\d{11,17})',
            
            # Kotak format
            r'(\d{6})[Xx]{6}(\d{4})',
        ]
        
        result = self.smart_search(text, patterns)
        
        if result:
            # Extract last 4-5 digits
            digits = re.findall(r'\d+', result)
            if digits:
                last_group = digits[-1]
                return last_group[-5:] if len(last_group) == 5 else last_group[-4:]
        
        return "N/A"
    
    def extract_billing_cycle(self, extraction: Dict) -> str:
        """Extract billing cycle"""
        text = extraction['text_layout'] or extraction['text_simple']
        
        patterns = [
            r'Statement\s+(?:Period|Date)[\s:]*(?:From\s+)?(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4}|\d{1,2}/\d{1,2}/\d{4})[\s]*(?:to|To|-|–)[\s]*(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4}|\d{1,2}/\d{1,2}/\d{4})',
            r'Statement\s+Date[\s:]*(\d{1,2}/\d{1,2}/\d{4})',
            r'Closing\s+Date[\s:]*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'from\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+to\s+(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})',
        ]
        
        result = self.smart_search(text, patterns)
        return result if result else "N/A"
    
    def extract_due_date(self, extraction: Dict) -> str:
        """Extract due date"""
        text = extraction['text_layout'] or extraction['text_simple']
        
        patterns = [
            r'(?:Payment\s+)?Due\s+Date[\s:]*(\d{1,2}[/-][A-Za-z]{3}[/-]\d{4}|\d{1,2}/\d{1,2}/\d{4})',
            r'Minimum\s+Payment\s+Due[\s:]*[^\d]*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        ]
        
        result = self.smart_search(text, patterns)
        return result if result else "N/A"
    
    def extract_balance(self, extraction: Dict) -> float:
        """Extract balance with multiple strategies"""
        text = extraction['text_layout'] or extraction['text_simple']
        
        patterns = [
            r'(?:Total\s+Amount\s+Due|Your\s+Total\s+Amount\s+Due|Total\s+Dues|Closing\s+Balance|New\s+Balance)[\s:]*`?[\s]*(?:Rs\.?|₹)?[\s]*([\d,]+\.?\d*)',
            r'(?:Balance|Amount\s+Due)[\s:]*(?:Rs\.?|₹)?[\s]*([\d,]+\.?\d*)',
        ]
        
        result = self.smart_search(text, patterns)
        
        if result:
            cleaned = re.sub(r'[₹Rs\s,]', '', result)
            try:
                return float(cleaned)
            except:
                pass
        
        return 0.0
    
    def extract_minimum_payment(self, extraction: Dict) -> float:
        """Extract minimum payment"""
        text = extraction['text_layout'] or extraction['text_simple']
        
        patterns = [
            r'(?:Minimum\s+(?:Amount\s+Due|Payment(?:\s+Due)?)|Min\s+Payment\s+Due)[\s:]*(?:Rs\.?|₹)?[\s]*([\d,]+\.?\d*)',
        ]
        
        result = self.smart_search(text, patterns)
        
        if result:
            cleaned = re.sub(r'[₹Rs\s,]', '', result)
            try:
                return float(cleaned)
            except:
                pass
        
        return 0.0
    
    def extract_transactions_from_text(self, extraction: Dict, max_count: int = 20) -> List[Dict]:
        """Extract transactions from text when tables fail"""
        text = extraction['text_layout'] or extraction['text_simple']
        transactions = []
        
        # Multiple transaction patterns
        patterns = [
            # DD/MM/YYYY Description Amount
            r'(\d{1,2}/\d{1,2}/\d{4})\s+([A-Z][A-Za-z0-9\s\-\.\*&,]{5,60}?)\s+([\d,]+\.?\d{2})',
            
            # DD Mon YYYY Description Amount  
            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})\s+([A-Z][A-Za-z0-9\s\-\.\*&,]{5,60}?)\s+([\d,]+\.?\d{2})',
            
            # DD-Mon-YYYY Description Amount
            r'(\d{1,2}-[A-Za-z]{3}-\d{4})\s+([A-Z][A-Za-z0-9\s\-\.\*&,]{5,60}?)\s+([\d,]+\.?\d{2})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            
            for match in matches:
                try:
                    date = match[0].strip()
                    description = re.sub(r'\s+', ' ', match[1].strip())
                    amount_str = match[2].strip()
                    
                    # Skip if description is too short or looks like a header
                    if len(description) < 5 or 'description' in description.lower():
                        continue
                    
                    # Skip payments/credits
                    skip_terms = ['PAYMENT', 'CREDIT', 'NEFT', 'IMPS', 'THANK YOU']
                    if any(term in description.upper() for term in skip_terms):
                        continue
                    
                    amount = self._parse_amount(amount_str)
                    
                    if amount > 0:
                        transactions.append({
                            'date': date,
                            'description': description,
                            'amount': amount
                        })
                except:
                    continue
            
            if len(transactions) >= max_count:
                break
        
        return transactions[:max_count]
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string"""
        cleaned = re.sub(r'[₹Rs\s,]', '', str(amount_str))
        try:
            return float(cleaned)
        except:
            return 0.0


def test_extractor(pdf_path: str):
    """Test the robust extractor"""
    print(f"\n{'='*100}")
    print(f"TESTING ROBUST EXTRACTOR: {pdf_path}")
    print(f"{'='*100}\n")
    
    extractor = RobustExtractor()
    extraction = extractor.extract_all_methods(pdf_path)
    
    print("📊 EXTRACTION RESULTS:")
    print("-" * 100)
    print(f"Text (simple): {len(extraction['text_simple'])} chars")
    print(f"Text (layout): {len(extraction['text_layout'])} chars")
    print(f"Tables (default): {len(extraction['tables_default'])}")
    print(f"Tables (alt): {len(extraction['tables_alt'])}")
    
    print("\n📝 EXTRACTED FIELDS:")
    print("-" * 100)
    print(f"Card Number:      {extractor.extract_card_number(extraction)}")
    print(f"Billing Cycle:    {extractor.extract_billing_cycle(extraction)}")
    print(f"Due Date:         {extractor.extract_due_date(extraction)}")
    print(f"Balance:          ₹{extractor.extract_balance(extraction):,.2f}")
    print(f"Minimum Payment:  ₹{extractor.extract_minimum_payment(extraction):,.2f}")
    
    transactions = extractor.extract_transactions_from_text(extraction, max_count=5)
    print(f"\n📜 TRANSACTIONS ({len(transactions)}):")
    print("-" * 100)
    for i, txn in enumerate(transactions[-5:], 1):
        print(f"  {i}. {txn['date']:15} {txn['description'][:45]:45} ₹{txn['amount']:>10,.2f}")
    
    print("\n" + "="*100)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python robust_universal_parser.py <pdf_file>")
        sys.exit(1)
    
    test_extractor(sys.argv[1])