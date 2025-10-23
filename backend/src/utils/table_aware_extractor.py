"""
Table-Aware PDF Extractor
Handles PDFs with tables correctly by preserving structure
"""

import pdfplumber
import pandas as pd
from typing import List, Dict, Tuple, Optional
import re

class TableAwarePDFExtractor:
    """
    Enhanced PDF extractor that properly handles tables
    """
    
    def __init__(self):
        self.debug = False
    
    def extract_with_layout(self, pdf_path: str) -> Dict:
        """
        Extract PDF preserving layout and table structure
        Returns both text and structured table data
        """
        result = {
            'raw_text': '',
            'tables': [],
            'text_by_region': {},
            'metadata': {}
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            
            for page_num, page in enumerate(pdf.pages):
                page_data = self._extract_page_with_tables(page, page_num)
                
                all_text.append(page_data['text'])
                result['tables'].extend(page_data['tables'])
                result['text_by_region'].update(page_data['regions'])
            
            result['raw_text'] = '\n'.join(all_text)
            result['metadata']['total_pages'] = len(pdf.pages)
            result['metadata']['total_tables'] = len(result['tables'])
        
        return result
    
    def _extract_page_with_tables(self, page, page_num: int) -> Dict:
        """Extract a single page with table awareness"""
        result = {
            'text': '',
            'tables': [],
            'regions': {}
        }
        
        # Extract tables first
        tables = page.extract_tables()
        
        if tables:
            # Process each table
            for table_idx, table in enumerate(tables):
                if table and len(table) > 0:
                    # Convert to DataFrame for easier processing
                    try:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df = df.dropna(how='all')  # Remove empty rows
                        
                        # Store structured table
                        result['tables'].append({
                            'page': page_num,
                            'table_index': table_idx,
                            'data': df,
                            'raw': table
                        })
                        
                        if self.debug:
                            print(f"\n=== Table {table_idx} on Page {page_num} ===")
                            print(df.to_string())
                    except Exception as e:
                        if self.debug:
                            print(f"Error processing table {table_idx}: {e}")
        
        # Extract text with layout
        text = page.extract_text(layout=True)
        result['text'] = text if text else ''
        
        # Extract text by regions (top, middle, bottom)
        height = page.height
        result['regions'][f'page_{page_num}_top'] = self._extract_region(
            page, 0, height * 0.3
        )
        result['regions'][f'page_{page_num}_middle'] = self._extract_region(
            page, height * 0.3, height * 0.7
        )
        result['regions'][f'page_{page_num}_bottom'] = self._extract_region(
            page, height * 0.7, height
        )
        
        return result
    
    def _extract_region(self, page, y0: float, y1: float) -> str:
        """Extract text from a specific region of the page"""
        bbox = (0, y0, page.width, y1)
        cropped = page.crop(bbox)
        text = cropped.extract_text(layout=True)
        return text if text else ''
    
    def find_in_tables(self, tables: List[Dict], search_term: str) -> List[Dict]:
        """
        Search for a term in all tables
        Returns list of matches with context
        """
        matches = []
        
        for table_info in tables:
            df = table_info['data']
            
            # Search in all cells
            for col in df.columns:
                for idx, value in df[col].items():
                    if value and search_term.lower() in str(value).lower():
                        matches.append({
                            'page': table_info['page'],
                            'table_index': table_info['table_index'],
                            'column': col,
                            'row': idx,
                            'value': value,
                            'full_row': df.iloc[idx].to_dict()
                        })
        
        return matches
    
    def extract_table_by_header(self, tables: List[Dict], header_keyword: str) -> Optional[pd.DataFrame]:
        """
        Find and return a table that contains a specific header
        Useful for transaction tables
        """
        for table_info in tables:
            df = table_info['data']
            
            # Check if any column header contains the keyword
            for col in df.columns:
                if col and header_keyword.lower() in str(col).lower():
                    return df
        
        return None
    
    def extract_key_value_pairs(self, text: str, region: str = None) -> Dict[str, str]:
        """
        Extract key-value pairs from text
        Handles formats like:
        - "Total Balance: $1,234.56"
        - "Due Date     : 01/01/2024"
        - "Card Number: XXXX-XXXX-XXXX-1234"
        """
        pairs = {}
        
        # Pattern for key: value pairs
        pattern = r'([A-Za-z\s]+?)[\s:]+([^\n]+)'
        matches = re.findall(pattern, text)
        
        for key, value in matches:
            key = key.strip()
            value = value.strip()
            
            # Filter out noise
            if len(key) > 2 and len(value) > 0:
                pairs[key] = value
        
        return pairs
    
    def extract_transaction_table(self, tables: List[Dict]) -> Optional[pd.DataFrame]:
        """
        Intelligently identify and extract the transaction table
        """
        transaction_keywords = ['date', 'description', 'amount', 'transaction', 'debit', 'credit']
        
        best_match = None
        best_score = 0
        
        for table_info in tables:
            df = table_info['data']
            
            if df.empty or len(df.columns) < 2:
                continue
            
            # Score based on column headers
            score = 0
            headers = [str(col).lower() for col in df.columns]
            
            for keyword in transaction_keywords:
                if any(keyword in header for header in headers):
                    score += 1
            
            # Transaction tables usually have multiple rows
            if len(df) > 3:
                score += 1
            
            # Should have at least 3 columns (date, desc, amount)
            if len(df.columns) >= 3:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = df
        
        return best_match
    
    def visualize_extraction(self, pdf_path: str, output_path: str = None):
        """
        Visualize how text and tables are extracted
        Helpful for debugging
        """
        result = self.extract_with_layout(pdf_path)
        
        output = []
        output.append("="*80)
        output.append("PDF EXTRACTION VISUALIZATION")
        output.append("="*80)
        
        # Show tables
        output.append(f"\n📊 Found {len(result['tables'])} tables:\n")
        
        for i, table_info in enumerate(result['tables']):
            output.append(f"\n--- Table {i+1} (Page {table_info['page']}) ---")
            df = table_info['data']
            output.append(f"Columns: {list(df.columns)}")
            output.append(f"Rows: {len(df)}")
            output.append(f"\nFirst 3 rows:")
            output.append(df.head(3).to_string())
        
        # Show regions
        output.append("\n\n📍 Text by regions:\n")
        for region_name, region_text in result['text_by_region'].items():
            output.append(f"\n--- {region_name} ---")
            output.append(region_text[:300] + "..." if len(region_text) > 300 else region_text)
        
        output_text = "\n".join(output)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)
            print(f"✅ Visualization saved to {output_path}")
        else:
            print(output_text)
        
        return output_text


class TableBasedParser:
    """
    Base class for parsers that work with table-aware extraction
    """
    
    def __init__(self):
        self.extractor = TableAwarePDFExtractor()
    
    def parse_with_tables(self, pdf_path: str) -> Dict:
        """
        Parse PDF using table-aware extraction
        Override this in subclasses
        """
        # Extract with table awareness
        extraction = self.extractor.extract_with_layout(pdf_path)
        
        result = {
            'card_last_four': self._extract_from_layout(extraction, 'card'),
            'billing_cycle': self._extract_from_layout(extraction, 'billing'),
            'due_date': self._extract_from_layout(extraction, 'due_date'),
            'total_balance': self._extract_from_layout(extraction, 'balance'),
            'minimum_payment': self._extract_from_layout(extraction, 'minimum'),
            'transactions': self._extract_transactions_from_table(extraction['tables'])
        }
        
        return result
    
    def _extract_from_layout(self, extraction: Dict, field_type: str) -> str:
        """
        Extract field using layout-aware approach
        Override in subclasses for bank-specific logic
        """
        # Search in top region first (most summary info is at top)
        for region_name, region_text in extraction['text_by_region'].items():
            if 'top' in region_name:
                # Extract based on field type
                if field_type == 'card':
                    match = re.search(r'[Xx*]{4}[\s-]*[Xx*]{4}[\s-]*[Xx*]{4}[\s-]*(\d{4})', region_text)
                    if match:
                        return match.group(1)
                
                elif field_type == 'balance':
                    match = re.search(r'(?:Total|Balance|Due)[\s:]+[\$₹Rs\.]*\s*([\d,]+\.?\d*)', region_text)
                    if match:
                        return match.group(1)
        
        return "N/A"
    
    def _extract_transactions_from_table(self, tables: List[Dict]) -> List[Dict]:
        """
        Extract transactions from the transaction table
        """
        # Find transaction table
        txn_table = self.extractor.extract_transaction_table(tables)
        
        if txn_table is None or txn_table.empty:
            return []
        
        transactions = []
        
        # Identify columns
        date_col = self._find_column(txn_table, ['date', 'txn', 'transaction'])
        desc_col = self._find_column(txn_table, ['description', 'desc', 'particulars', 'details', 'merchant'])
        amount_col = self._find_column(txn_table, ['amount', 'debit', 'value', 'price'])
        
        if not all([date_col, desc_col, amount_col]):
            return []
        
        # Extract transactions
        for idx, row in txn_table.iterrows():
            try:
                date = str(row[date_col]).strip()
                description = str(row[desc_col]).strip()
                amount_str = str(row[amount_col]).strip()
                
                # Clean amount
                amount = self._clean_amount(amount_str)
                
                if amount > 0 and len(description) > 2:
                    transactions.append({
                        'date': date,
                        'description': description,
                        'amount': amount
                    })
            except:
                continue
        
        return transactions[:10]  # Return top 10
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Find column that matches any of the keywords"""
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None
    
    def _clean_amount(self, amount_str: str) -> float:
        """Clean and convert amount string to float"""
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹$Rs\s]', '', amount_str)
        # Remove commas
        cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except:
            return 0.0


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python table_aware_extractor.py <pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print("🔍 Analyzing PDF with table-aware extraction...\n")
    
    extractor = TableAwarePDFExtractor()
    extractor.debug = True
    
    # Extract and visualize
    extractor.visualize_extraction(pdf_path)
    
    print("\n" + "="*80)
    print("💡 TIP: Use this output to understand the table structure")
    print("   Then update your parser to use table-based extraction")
    print("="*80)