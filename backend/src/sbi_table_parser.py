"""
Enhanced SBI (State Bank of India) Parser with Table-Aware Extraction
"""

import re
import pandas as pd
from typing import List, Dict, Optional
from models.statement import StatementData, Transaction
from utils.table_aware_extractor import TableAwarePDFExtractor

class SBITableParser:
    def __init__(self):
        self.extractor = TableAwarePDFExtractor()
    
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
        """Parse SBI statement using table-aware extraction"""
        
        # Extract with table awareness
        extraction = self.extractor.extract_with_layout(pdf_path)
        
        # Extract fields
        card_last_four = self._extract_account_number(extraction)
        billing_cycle = self._extract_statement_period(extraction)
        due_date = "N/A"  # Savings account doesn't have due date
        total_balance = self._extract_balance(extraction)
        minimum_payment = 0.0  # N/A for savings account
        transactions = self._extract_transactions(extraction)
        
        return StatementData(
            issuer="State Bank of India",
            card_last_four=card_last_four,
            billing_cycle=billing_cycle,
            payment_due_date=due_date,
            total_balance=total_balance,
            minimum_payment=minimum_payment,
            transactions=transactions[-5:] if len(transactions) >= 5 else transactions  # Last 5 transactions
        )
    
    def _extract_account_number(self, extraction: Dict) -> str:
        """Extract account number"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
                patterns = [
                    r'Account Number\s*:\s*(\d{11,17})',
                    r'A/c\s*No\.?\s*:\s*(\d{11,17})',
                    r'Account No\s*:\s*(\d{11,17})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        number = match.group(1)
                        return number[-4:] if len(number) >= 4 else number
        
        return "N/A"
    
    def _extract_statement_period(self, extraction: Dict) -> str:
        """Extract statement period"""
        for region_name, text in extraction['text_by_region'].items():
            if 'top' in region_name:
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
    
    def _extract_balance(self, extraction: Dict) -> float:
        """Extract closing balance"""
        # Try to find balance in tables
        for table_info in extraction['tables']:
            df = table_info['data']
            
            # Look for Balance column
            balance_col = self._find_column_by_keywords(df, ['balance', 'closing balance'])
            
            if balance_col:
                # Get last non-null balance
                for idx in reversed(df.index):
                    balance_str = str(df.at[idx, balance_col])
                    if balance_str and balance_str != 'nan':
                        amount = self._parse_amount(balance_str)
                        if amount > 0:
                            return amount
        
        # Fallback to text search
        for region_name, text in extraction['text_by_region'].items():
            pattern = r'(?:Closing Balance|Balance).*?([\d,]+\.?\d*)'
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
        date_col = self._find_column_by_keywords(txn_table, ['date', 'txn date', 'value date'])
        desc_col = self._find_column_by_keywords(txn_table, ['description', 'particulars', 'narration'])
        debit_col = self._find_column_by_keywords(txn_table, ['debit', 'withdrawal', 'dr'])
        credit_col = self._find_column_by_keywords(txn_table, ['credit', 'deposit', 'cr'])
        
        if not date_col or not desc_col:
            return transactions
        
        # Extract transactions (prefer debits, but include credits if no debits)
        for idx, row in txn_table.iterrows():
            try:
                date = str(row[date_col]).strip()
                description = str(row[desc_col]).strip()
                
                # Skip headers
                if 'date' in date.lower() or 'nan' in date.lower() or len(date) < 5:
                    continue
                
                if len(description) < 3:
                    continue
                
                # Try to get debit amount first
                amount = 0.0
                if debit_col:
                    debit_str = str(row[debit_col]).strip()
                    amount = self._parse_amount(debit_str)
                
                # If no debit, try credit
                if amount == 0.0 and credit_col:
                    credit_str = str(row[credit_col]).strip()
                    amount = self._parse_amount(credit_str)
                
                if amount > 0:
                    # Skip certain entries
                    skip_terms = ['TRANSFER TO', 'NEFT', 'IMPS', 'UPI', 'PAYMENT']
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
            
            # Score headers
            if any('date' in h for h in headers):
                score += 2
            if any('description' in h or 'particular' in h or 'narration' in h for h in headers):
                score += 2
            if any('debit' in h or 'credit' in h or 'withdrawal' in h for h in headers):
                score += 2
            
            if len(df) > 5:
                score += 1
            
            # SBI statements typically have 5+ columns
            if len(df.columns) >= 5:
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
        """Parse amount string"""
        if not amount_str or amount_str == 'nan':
            return 0.0
        
        cleaned = re.sub(r'[₹$Rs\s]', '', amount_str)
        cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return 0.0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sbi_table_parser.py <pdf_file>")
        sys.exit(1)
    
    parser = SBITableParser()
    statement = parser.parse(sys.argv[1])
    
    print("\n" + "="*80)
    print("STATE BANK OF INDIA STATEMENT")
    print("="*80)
    print(f"Issuer:          {statement.issuer}")
    print(f"Account Last 4:  {statement.card_last_four}")
    print(f"Statement Period:{statement.billing_cycle}")
    print(f"Due Date:        {statement.payment_due_date}")
    print(f"Closing Balance: ₹{statement.total_balance:,.2f}")
    print(f"Min Payment:     ₹{statement.minimum_payment:,.2f}")
    print(f"\nLast {len(statement.transactions)} Transactions:")
    for i, txn in enumerate(statement.transactions, 1):
        print(f"  {i}. {txn.date:12} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")