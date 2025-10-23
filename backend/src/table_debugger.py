"""
Table Extraction Debugger
Visualize and debug table extraction issues
"""

import pdfplumber
import pandas as pd
from typing import List, Dict
import sys

class TableDebugger:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
    
    def analyze(self):
        """Full analysis of PDF table structure"""
        print("\n" + "="*100)
        print(f"📄 ANALYZING: {self.pdf_path}")
        print("="*100)
        
        with pdfplumber.open(self.pdf_path) as pdf:
            self.pdf = pdf
            
            for page_num, page in enumerate(pdf.pages):
                print(f"\n{'='*100}")
                print(f"📃 PAGE {page_num + 1}")
                print(f"{'='*100}")
                
                # Show page dimensions
                print(f"\n📐 Page Dimensions:")
                print(f"   Width: {page.width}, Height: {page.height}")
                
                # Extract and show tables
                self._analyze_tables(page, page_num)
                
                # Show text extraction comparison
                self._compare_text_methods(page, page_num)
    
    def _analyze_tables(self, page, page_num: int):
        """Analyze tables on a page"""
        print(f"\n📊 TABLE ANALYSIS:")
        print("-" * 100)
        
        tables = page.extract_tables()
        
        if not tables:
            print("   ❌ No tables found on this page")
            return
        
        print(f"   ✅ Found {len(tables)} table(s)\n")
        
        for table_idx, table in enumerate(tables):
            self._display_table(table, page_num, table_idx)
    
    def _display_table(self, table: List[List], page_num: int, table_idx: int):
        """Display a single table with analysis"""
        print(f"\n   --- Table {table_idx + 1} ---")
        
        if not table or len(table) == 0:
            print("   ⚠️  Empty table")
            return
        
        # Create DataFrame
        try:
            # First row as headers
            headers = table[0]
            data = table[1:]
            
            df = pd.DataFrame(data, columns=headers)
            
            print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
            print(f"   Headers: {list(df.columns)}")
            
            # Show first few rows
            print(f"\n   First 3 rows:")
            print("   " + "-" * 90)
            
            display_df = df.head(3)
            for idx, row in display_df.iterrows():
                print(f"   Row {idx}:")
                for col in df.columns:
                    value = str(row[col])[:50]  # Truncate long values
                    print(f"      {col}: {value}")
                print()
            
            # Identify likely table type
            table_type = self._identify_table_type(df)
            print(f"   🔍 Likely Type: {table_type}")
            
            # Show potential issues
            self._check_table_issues(df)
            
        except Exception as e:
            print(f"   ❌ Error processing table: {e}")
            print(f"   Raw table preview:")
            for i, row in enumerate(table[:3]):
                print(f"      Row {i}: {row}")
    
    def _identify_table_type(self, df: pd.DataFrame) -> str:
        """Identify what type of table this is"""
        headers = [str(col).lower() for col in df.columns]
        
        # Transaction table
        if any('date' in h for h in headers) and any('amount' in h or 'debit' in h for h in headers):
            if any('description' in h or 'transaction' in h or 'particular' in h for h in headers):
                return "🔸 TRANSACTION TABLE"
        
        # Summary table
        if any('balance' in h or 'total' in h for h in headers):
            return "🔸 SUMMARY/BALANCE TABLE"
        
        # Account info table
        if any('account' in h or 'card' in h for h in headers):
            return "🔸 ACCOUNT INFO TABLE"
        
        return "🔸 UNKNOWN TYPE"
    
    def _check_table_issues(self, df: pd.DataFrame):
        """Check for common table extraction issues"""
        issues = []
        
        # Check for merged cells (None or empty values)
        null_count = df.isnull().sum().sum()
        if null_count > len(df) * 0.3:  # More than 30% null
            issues.append(f"⚠️  High number of empty cells ({null_count})")
        
        # Check for columns with no header
        unnamed_cols = [col for col in df.columns if 'None' in str(col) or str(col).strip() == '']
        if unnamed_cols:
            issues.append(f"⚠️  {len(unnamed_cols)} column(s) without header")
        
        # Check for data in wrong columns (numbers in description, text in amounts)
        for col in df.columns:
            col_lower = str(col).lower()
            
            if 'amount' in col_lower or 'balance' in col_lower or 'debit' in col_lower or 'credit' in col_lower:
                # Should be numeric
                non_numeric = 0
                for val in df[col]:
                    val_str = str(val).strip()
                    if val_str and val_str != 'nan':
                        # Check if it's not a number
                        cleaned = val_str.replace(',', '').replace('.', '').replace('₹', '').replace('Rs', '').strip()
                        if not cleaned.replace('-', '').isdigit():
                            non_numeric += 1
                
                if non_numeric > len(df) * 0.2:  # More than 20%
                    issues.append(f"⚠️  Column '{col}' should be numeric but contains text")
        
        # Check for wide cells (might indicate merged data)
        for col in df.columns:
            avg_length = df[col].astype(str).str.len().mean()
            if avg_length > 100:
                issues.append(f"⚠️  Column '{col}' has very long values (avg: {avg_length:.0f} chars)")
        
        if issues:
            print("\n   ⚠️  POTENTIAL ISSUES:")
            for issue in issues:
                print(f"      {issue}")
        else:
            print("\n   ✅ No obvious issues detected")
    
    def _compare_text_methods(self, page, page_num: int):
        """Compare different text extraction methods"""
        print(f"\n📝 TEXT EXTRACTION COMPARISON:")
        print("-" * 100)
        
        # Method 1: Simple text extraction
        text_simple = page.extract_text()
        
        # Method 2: Layout-preserving extraction
        text_layout = page.extract_text(layout=True)
        
        # Method 3: With x_tolerance and y_tolerance
        text_tolerant = page.extract_text(x_tolerance=3, y_tolerance=3)
        
        print(f"\n   Method 1: Simple extraction (first 500 chars)")
        print("   " + "-" * 90)
        print("   " + (text_simple[:500] if text_simple else "No text").replace('\n', '\n   '))
        
        print(f"\n   Method 2: Layout-preserving (first 500 chars)")
        print("   " + "-" * 90)
        print("   " + (text_layout[:500] if text_layout else "No text").replace('\n', '\n   '))
        
        print(f"\n   Method 3: With tolerance (first 500 chars)")
        print("   " + "-" * 90)
        print("   " + (text_tolerant[:500] if text_tolerant else "No text").replace('\n', '\n   '))
        
        # Compare lengths
        print(f"\n   📊 Comparison:")
        print(f"      Simple:    {len(text_simple) if text_simple else 0} chars")
        print(f"      Layout:    {len(text_layout) if text_layout else 0} chars")
        print(f"      Tolerant:  {len(text_tolerant) if text_tolerant else 0} chars")
        
        # Recommend best method
        if text_layout and len(text_layout) > len(text_simple or ''):
            print(f"\n   💡 RECOMMENDATION: Use layout-preserving extraction")
        else:
            print(f"\n   💡 RECOMMENDATION: Simple extraction seems adequate")
    
    def search_in_tables(self, search_term: str):
        """Search for a specific term across all tables"""
        print("\n" + "="*100)
        print(f"🔍 SEARCHING FOR: '{search_term}'")
        print("="*100)
        
        found_count = 0
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                for table_idx, table in enumerate(tables):
                    if not table:
                        continue
                    
                    # Search in table
                    for row_idx, row in enumerate(table):
                        for col_idx, cell in enumerate(row):
                            if cell and search_term.lower() in str(cell).lower():
                                found_count += 1
                                print(f"\n   ✅ FOUND in Page {page_num + 1}, Table {table_idx + 1}")
                                print(f"      Row {row_idx}, Column {col_idx}")
                                print(f"      Cell value: '{cell}'")
                                print(f"      Full row: {row}")
        
        if found_count == 0:
            print(f"\n   ❌ '{search_term}' not found in any tables")
        else:
            print(f"\n   Found {found_count} occurrence(s)")
    
    def export_tables(self, output_prefix: str = "table_export"):
        """Export all tables to CSV for inspection"""
        print("\n" + "="*100)
        print("💾 EXPORTING TABLES")
        print("="*100)
        
        export_count = 0
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    try:
                        # Create DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0])
                        
                        # Export to CSV
                        filename = f"{output_prefix}_page{page_num + 1}_table{table_idx + 1}.csv"
                        df.to_csv(filename, index=False)
                        
                        print(f"   ✅ Exported: {filename} ({len(df)} rows, {len(df.columns)} columns)")
                        export_count += 1
                    except Exception as e:
                        print(f"   ❌ Failed to export Page {page_num + 1}, Table {table_idx + 1}: {e}")
        
        print(f"\n   Total tables exported: {export_count}")
    
    def show_recommendations(self):
        """Show recommendations based on analysis"""
        print("\n" + "="*100)
        print("💡 RECOMMENDATIONS FOR PARSING")
        print("="*100)
        
        recommendations = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total_tables = 0
            pages_with_tables = 0
            
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    total_tables += len(tables)
                    pages_with_tables += 1
            
            if total_tables > 0:
                recommendations.append(
                    "✅ USE TABLE-AWARE EXTRACTION\n"
                    f"   Found {total_tables} table(s) across {pages_with_tables} page(s).\n"
                    "   Use pdfplumber's extract_tables() instead of plain text extraction."
                )
                
                recommendations.append(
                    "✅ IDENTIFY TABLE COLUMNS\n"
                    "   Look for column headers like 'Date', 'Description', 'Amount'.\n"
                    "   Use these to correctly extract transaction data."
                )
                
                recommendations.append(
                    "✅ HANDLE EMPTY CELLS\n"
                    "   Tables may have merged cells or empty values.\n"
                    "   Use df.dropna() or df.fillna() to clean data."
                )
                
                recommendations.append(
                    "✅ VALIDATE COLUMN DATA\n"
                    "   Check that amount columns contain numbers.\n"
                    "   Check that date columns contain valid dates."
                )
            else:
                recommendations.append(
                    "⚠️  NO TABLES DETECTED\n"
                    "   This PDF might not have structured tables.\n"
                    "   Use layout-preserving text extraction instead."
                )
            
            recommendations.append(
                "✅ USE REGION-BASED EXTRACTION\n"
                "   Extract header info from top region (card number, dates).\n"
                "   Extract transactions from middle/bottom regions."
            )
            
            recommendations.append(
                "✅ TEST WITH MULTIPLE SAMPLES\n"
                "   Table structures may vary across different statements.\n"
                "   Test with 3-5 samples from the same bank."
            )
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec}")
        
        print("\n" + "="*100)


def main():
    if len(sys.argv) < 2:
        print("Usage: python table_debugger.py <pdf_file> [options]")
        print("\nOptions:")
        print("  --search <term>     Search for a term in tables")
        print("  --export            Export all tables to CSV")
        print("\nExamples:")
        print("  python table_debugger.py statement.pdf")
        print("  python table_debugger.py statement.pdf --search 'Total Balance'")
        print("  python table_debugger.py statement.pdf --export")
        return
    
    pdf_path = sys.argv[1]
    debugger = TableDebugger(pdf_path)
    
    # Check for options
    if len(sys.argv) > 2:
        if sys.argv[2] == "--search" and len(sys.argv) > 3:
            search_term = sys.argv[3]
            debugger.search_in_tables(search_term)
        elif sys.argv[2] == "--export":
            debugger.export_tables()
    else:
        # Full analysis
        debugger.analyze()
        debugger.show_recommendations()

if __name__ == "__main__":
    main()