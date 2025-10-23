"""
Enhanced HDFC Parser with Table-Aware Extraction
"""

import re
import pandas as pd
from models.statement import StatementData, Transaction
from utils.table_aware_extractor import TableAwarePDFExtractor
from typing import List, Dict, Optional

class HDFCTableParser:
    def __init__(self):
        self.extractor = TableAwarePDFExtractor()
    
    def can_parse(self, text: str) -> bool:
        indicators = ['hdfc bank', 'hdfcbank', 'hdfc credit card', 'times card']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def parse(self, pdf_path: str) -> StatementData:
        """Parse HDFC statement using table-aware extraction"""
        
        # Extract with table awareness
        extraction = self.extractor.extract_with_layout(pdf_path)
        
        # Extract fields from structured regions
        card_last_four = self._extract_card_number(extraction)
        billing_cycle = self._extract_billing_cycle(extraction)
        due_date = self._extract_due_date(extraction)
        total_balance = self._extract_balance(extraction)
        minimum_payment = self._extract_minimum(extraction)
        transactions = self._extract_transactions(extraction)
        
        return StatementData(
            issuer="HDFC Bank",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[:5]
        )
    
    def _extract_card_number(self, extraction: Dict) -> str:
        """Extract card number from top region (header area)"""
        # Look in top region first
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                patterns = [
                    r'Card No:\s*(\d{4})\s*(\d{2})[Xx]{2}\s*[Xx]{4}\s*(\d{4})',
                    r'(\d{4})\s*\d{2}XX\s*XXXX\s*(\d{3,4})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        # Return last 4 digits
                        return match.group(match.lastindex)
        
        return "N/A"
    
    def _extract_billing_cycle(self, extraction: Dict) -> str:
        """Extract billing cycle from header"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                pattern = r'Statement Date:\s*(\d{2}/\d{2}/\d{4})'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return f"Statement date: {match.group(1)}"
        
        return "N/A"
    
    def _extract_due_date(self, extraction: Dict) -> str:
        """Extract due date"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                pattern = r'Payment Due Date\s+(\d{2}/\d{2}/\d{4})'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        return "N/A"
    
    def _extract_balance(self, extraction: Dict) -> float:
        """Extract balance from Account Summary table or text"""
        # First try to find in tables
        for table_info in extraction['tables']:
            df = table_info['data']
            
            # Look for "Total Dues" row
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col])
                    if 'total dues' in cell_value.lower():
                        # Balance should be in next column or same row
                        for other_col in df.columns:
                            if other_col != col:
                                amount_str = str(row[other_col])
                                amount = self._parse_amount(amount_str)
                                if amount > 0:
                                    return amount
        
        # Fallback to text extraction
        for region_name, text in extraction['text_by_region'].items():
            pattern = r'Total Dues\s+([\d,]+\.?\d*)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_amount(match.group(1))
        
        return 0.0
    
    def _extract_minimum(self, extraction: Dict) -> float:
        """Extract minimum payment"""
        # Try tables first
        for table_info in extraction['tables']:
            df = table_info['data']
            
            for idx, row in df.iterrows():
                for col in df.columns:
                    cell_value = str(row[col])
                    if 'minimum amount due' in cell_value.lower():
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
        """Extract transactions from transaction table"""
        transactions = []
        
        # Find the transaction table
        txn_table = self._find_transaction_table(extraction['tables'])
        
        if txn_table is None:
            return transactions
        
        # Identify columns
        date_col = self._find_column_by_keywords(txn_table, ['date', 'txn date'])
        desc_col = self._find_column_by_keywords(txn_table, ['description', 'transaction', 'details'])
        amount_col = self._find_column_by_keywords(txn_table, ['amount', 'value', 'rs'])
        
        if not all([date_col, desc_col, amount_col]):
            return transactions
        
        # Extract each transaction
        for idx, row in txn_table.iterrows():
            try:
                date = str(row[date_col]).strip()
                description = str(row[desc_col]).strip()
                amount_str = str(row[amount_col]).strip()
                
                # Skip headers and invalid rows
                if 'date' in date.lower() or 'nan' in date.lower():
                    continue
                
                if len(description) < 3:
                    continue
                
                # Parse amount
                amount = self._parse_amount(amount_str)
                
                if amount > 0:
                    # Skip payment/credit entries
                    if any(skip in description.upper() for skip in ['PAYMENT', 'NEFT CREDIT', 'INFINITY PAYMENT']):
                        continue
                    
                    transactions.append(Transaction(
                        date=date,
                        description=description,
                        amount=amount
                    ))
            except Exception as e:
                continue
        
        return transactions
    
    def _find_transaction_table(self, tables: List[Dict]) -> Optional[pd.DataFrame]:
        """Find the table containing transactions"""
        best_match = None
        best_score = 0
        
        for table_info in tables:
            df = table_info['data']
            
            if df.empty or len(df) < 3:  # Need at least 3 rows
                continue
            
            score = 0
            
            # Check column headers
            headers = [str(col).lower() for col in df.columns]
            
            if any('date' in h for h in headers):
                score += 2
            if any('description' in h or 'transaction' in h for h in headers):
                score += 2
            if any('amount' in h for h in headers):
                score += 2
            
            # Transaction tables usually have many rows
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
        """Find column that matches keywords"""
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
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹$Rs\s]', '', amount_str)
        # Remove commas
        cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return 0.0


# Test function
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hdfc_table_parser.py <pdf_file>")
        sys.exit(1)
    
    parser = HDFCTableParser()
    statement = parser.parse(sys.argv[1])
    
    print("\n" + "="*80)
    print("PARSED STATEMENT")
    print("="*80)
    print(f"Issuer:          {statement.issuer}")
    print(f"Card Last 4:     {statement.card_last_four}")
    print(f"Billing Cycle:   {statement.billing_cycle}")
    print(f"Due Date:        {statement.payment_due_date}")
    print(f"Total Balance:   ₹{statement.total_balance:,.2f}")
    print(f"Min Payment:     ₹{statement.minimum_payment:,.2f}")
    print(f"\nTransactions ({len(statement.transactions)}):")
    for i, txn in enumerate(statement.transactions, -1):
        print(f"  {i}. {txn.date:12} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")