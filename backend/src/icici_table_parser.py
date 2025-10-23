"""
Enhanced ICICI Bank Parser with Table-Aware Extraction
"""

import re
import pandas as pd
from typing import List, Dict, Optional
from models.statement import StatementData, Transaction
from utils.table_aware_extractor import TableAwarePDFExtractor

class ICICITableParser:
    def __init__(self):
        self.extractor = TableAwarePDFExtractor()
    
    def can_parse(self, text: str) -> bool:
        indicators = ['icici bank', 'icicibank', 'icici credit card', 'ICICI Bank Credit Cards']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        """Parse ICICI statement using table-aware extraction"""
        
        # Extract with table awareness
        extraction = self.extractor.extract_with_layout(pdf_path)
        
        # Extract fields
        card_last_four = self._extract_card_number(extraction)
        billing_cycle = self._extract_billing_cycle(extraction)
        due_date = self._extract_due_date(extraction)
        total_balance = self._extract_balance(extraction)
        minimum_payment = self._extract_minimum(extraction)
        transactions = self._extract_transactions(extraction)
        
        return StatementData(
            issuer="ICICI Bank",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[-5:] if len(transactions) >= 5 else transactions  # Last 5 transactions
        )
    
    def _extract_card_number(self, extraction: Dict) -> str:
        """Extract card number from top region"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                patterns = [
                    r'Card Number\s*:\s*(\d{4})\s*[Xx]{4}\s*[Xx]{4}\s*(\d{4})',
                    r'(\d{4})\s*XXXX\s*XXXX\s*(\d{3,4})',
                    r'Card Account No\s*(\d{4})\s*[Xx]+\s*[Xx]+\s*(\d{3,4})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # Return last 4 digits
                        return match.group(match.lastindex)
        
        return "N/A"
    
    def _extract_billing_cycle(self, extraction: Dict) -> str:
        """Extract billing cycle"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                patterns = [
                    r'Statement Date\s+(\d{2}/\d{2}/\d{4})',
                    r'Statement Period.*?From\s*(\d{2}/\d{2}/\d{4})\s*to\s*(\d{2}/\d{2}/\d{4})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                    if match:
                        if match.lastindex == 2:
                            return f"{match.group(1)} - {match.group(2)}"
                        return f"Statement date: {match.group(1)}"
        
        return "N/A"
    
    def _extract_due_date(self, extraction: Dict) -> str:
        """Extract due date"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                patterns = [
                    r'Due Date\s*:\s*(\d{2}/\d{2}/\d{4})',
                    r'Payment.*?Due.*?(\d{2}/\d{2}/\d{4})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return match.group(1)
        
        return "N/A"
    
    def _extract_balance(self, extraction: Dict) -> float:
        """Extract total balance"""
        # Try tables first
        for table_info in extraction['tables']:
            df = table_info['data']
            
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col]).lower()
                    if 'total amount due' in cell_value or 'your total amount due' in cell_value:
                        # Balance should be in adjacent column
                        for other_col in df.columns:
                            if other_col != col:
                                amount_str = str(row[other_col])
                                amount = self._parse_amount(amount_str)
                                if amount > 0:
                                    return amount
        
        # Fallback to text
        for region_name, text in extraction['text_by_region'].items():
            patterns = [
                r'Your Total Amount Due\s*`?\s*([\d,]+\.?\d*)',
                r'Total Amount Due\s+([\d,]+\.?\d*)',
                r'Total Dues\s+([\d,]+\.?\d*)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._parse_amount(match.group(1))
        
        return 0.0
    
    def _extract_minimum(self, extraction: Dict) -> float:
        """Extract minimum payment"""
        # Try tables
        for table_info in extraction['tables']:
            df = table_info['data']
            
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col]).lower()
                    if 'minimum amount due' in cell_value:
                        for other_col in df.columns:
                            if other_col != col:
                                amount_str = str(row[other_col])
                                amount = self._parse_amount(amount_str)
                                if amount > 0:
                                    return amount
        
        # Fallback to text
        for region_name, text in extraction['text_by_region'].items():
            pattern = r'Minimum Amount Due\s+([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        
        return 0.0
    
    def _extract_transactions(self, extraction: Dict) -> List[Transaction]:
        """Extract transactions from table"""
        transactions = []
        
        # Find transaction table
        txn_table = self._find_transaction_table(extraction['tables'])
        
        if txn_table is None:
            return transactions
        
        # Identify columns
        date_col = self._find_column_by_keywords(txn_table, ['date', 'transaction date', 'txn date'])
        desc_col = self._find_column_by_keywords(txn_table, ['description', 'transaction', 'particulars'])
        amount_col = self._find_column_by_keywords(txn_table, ['amount', 'value', 'transaction amount'])
        
        if not all([date_col, desc_col, amount_col]):
            return transactions
        
        # Extract transactions
        for idx, row in txn_table.iterrows():
            try:
                date = str(row[date_col]).strip()
                description = str(row[desc_col]).strip()
                amount_str = str(row[amount_col]).strip()
                
                # Skip headers
                if 'date' in date.lower() or 'nan' in date.lower() or len(date) < 5:
                    continue
                
                if len(description) < 3:
                    continue
                
                # Parse amount
                amount = self._parse_amount(amount_str)
                
                if amount > 0:
                    # Skip payment/credit entries
                    skip_terms = ['PAYMENT', 'CREDIT CARD PAYMENT', 'INFINITY PAYMENT', 
                                 'NEFT', 'IMPS', 'DISCOUNT', 'FINANCE CHARGES', 'GST']
                    if any(skip in description.upper() for skip in skip_terms):
                        continue
                    
                    transactions.append(Transaction(
                        date=date,
                        description=description,
                        amount=amount
                    ))
            except:
                continue
        
        return transactions
    
    def _find_transaction_table(self, tables: List[Dict]) -> Optional[pd.DataFrame]:
        """Find transaction table"""
        best_match = None
        best_score = 0
        
        for table_info in tables:
            df = table_info['data']
            
            if df.empty or len(df) < 3:
                continue
            
            score = 0
            headers = [str(col).lower() for col in df.columns]
            
            # Score based on headers
            if any('date' in h for h in headers):
                score += 2
            if any('description' in h or 'transaction' in h or 'particular' in h for h in headers):
                score += 2
            if any('amount' in h for h in headers):
                score += 2
            
            # More rows = likely transaction table
            if len(df) > 5:
                score += 1
            
            # Should have at least 3 columns
            if len(df.columns) >= 3:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = df
        
        return best_match
    
    def _find_column_by_keywords(self, df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Find column matching keywords"""
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str or amount_str == 'nan':
            return 0.0
        
        # Remove currency and spaces
        cleaned = re.sub(r'[₹$Rs`\s]', '', amount_str)
        cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return 0.0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python icici_table_parser.py <pdf_file>")
        sys.exit(1)
    
    parser = ICICITableParser()
    statement = parser.parse(sys.argv[1])
    
    print("\n" + "="*80)
    print("ICICI BANK STATEMENT")
    print("="*80)
    print(f"Issuer:          {statement.issuer}")
    print(f"Card Last 4:     {statement.card_last_four}")
    print(f"Billing Cycle:   {statement.billing_cycle}")
    print(f"Due Date:        {statement.payment_due_date}")
    print(f"Total Balance:   ₹{statement.total_balance:,.2f}")
    print(f"Min Payment:     ₹{statement.minimum_payment:,.2f}")
    print(f"\nLast {len(statement.transactions)} Transactions:")
    for i, txn in enumerate(statement.transactions, 1):
        print(f"  {i}. {txn.date:12} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")