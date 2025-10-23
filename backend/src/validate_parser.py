"""
PDF Parser Validation Tool
Run this to manually verify parser accuracy against actual PDFs
"""

import sys
import os
from pathlib import Path
from utils.pdf_utils import PDFExtractor
from parsers.amex_india_parser import AmexIndiaParser
from parsers.hdfc_parser import HDFCParser
from parsers.icici_parser import ICICIParser
from parsers.kotak_parser import KotakParser
from parsers.sbi_parser import SBIParser

class ValidationTool:
    def __init__(self):
        self.parsers = [
            AmexIndiaParser(),
            HDFCParser(),
            ICICIParser(),
            KotakParser(),
            SBIParser()
        ]
        self.extractor = PDFExtractor()
    
    def validate_pdf(self, pdf_path: str):
        """Validate a single PDF file"""
        print(f"\n{'='*80}")
        print(f"VALIDATING: {os.path.basename(pdf_path)}")
        print(f"{'='*80}\n")
        
        # Extract raw text
        text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        # Show first 500 characters of raw text
        print("📄 RAW TEXT PREVIEW (first 500 chars):")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)
        print()
        
        # Find appropriate parser
        parser = None
        for p in self.parsers:
            if p.can_parse(text):
                parser = p
                break
        
        if not parser:
            print("❌ ERROR: No parser found for this PDF")
            print("\n💡 TIP: Check if the PDF contains bank name/identifiers")
            return
        
        print(f"✅ DETECTED ISSUER: {parser.__class__.__name__}")
        print()
        
        # Parse the statement
        try:
            statement = parser.parse(pdf_path)
            
            # Display extracted data
            print("📊 EXTRACTED DATA:")
            print("-" * 80)
            print(f"Issuer:              {statement.issuer}")
            print(f"Card Last 4:         {statement.card_last_four}")
            print(f"Billing Cycle:       {statement.billing_cycle}")
            print(f"Payment Due Date:    {statement.payment_due_date}")
            print(f"Total Balance:       ₹{statement.total_balance:,.2f}")
            print(f"Minimum Payment:     ₹{statement.minimum_payment:,.2f}")
            print()
            
            print(f"📝 TRANSACTIONS ({len(statement.transactions or [])}):")
            print("-" * 80)
            if statement.transactions:
                for i, txn in enumerate(statement.transactions, 1):
                    print(f"{i}. {txn.date:15} {txn.description:40} ₹{txn.amount:>10,.2f}")
            else:
                print("No transactions extracted")
            print("-" * 80)
            
            # Validation checklist
            print("\n✓ VALIDATION CHECKLIST:")
            print("-" * 80)
            self._print_validation_item("Card Number", statement.card_last_four, statement.card_last_four != "N/A")
            self._print_validation_item("Billing Cycle", statement.billing_cycle, statement.billing_cycle != "N/A")
            self._print_validation_item("Due Date", statement.payment_due_date, statement.payment_due_date != "N/A")
            self._print_validation_item("Balance", f"₹{statement.total_balance:,.2f}", statement.total_balance > 0)
            self._print_validation_item("Transactions", f"{len(statement.transactions or [])} found", len(statement.transactions or []) > 0)
            print("-" * 80)
            
            # Search functionality
            print("\n🔍 SEARCH IN RAW TEXT:")
            print("-" * 80)
            self._search_in_text(text, "card number", statement.card_last_four)
            self._search_in_text(text, "balance", str(int(statement.total_balance)))
            print("-" * 80)
            
        except Exception as e:
            print(f"❌ ERROR during parsing: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def _print_validation_item(self, label, value, is_valid):
        status = "✅" if is_valid else "❌"
        print(f"{status} {label:20} : {value}")
    
    def _search_in_text(self, text, label, search_term):
        """Search for a term in the raw text"""
        if not search_term or search_term == "N/A":
            return
        
        # Clean search term
        search_term = str(search_term).replace(",", "")
        
        if search_term in text:
            # Find context around the match
            index = text.find(search_term)
            start = max(0, index - 50)
            end = min(len(text), index + len(search_term) + 50)
            context = text[start:end].replace('\n', ' ')
            print(f"Found '{label}': ...{context}...")
        else:
            print(f"⚠️  '{search_term}' not found in raw text for {label}")
    
    def batch_validate(self, pdf_directory: str):
        """Validate all PDFs in a directory"""
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {pdf_directory}")
            return
        
        print(f"\n🔍 Found {len(pdf_files)} PDF files to validate\n")
        
        for pdf_file in pdf_files:
            self.validate_pdf(str(pdf_file))
            print("\n" + "="*80 + "\n")

def main():
    tool = ValidationTool()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python validate_parser.py <pdf_file>")
        print("  python validate_parser.py <directory>")
        print("\nExample:")
        print("  python validate_parser.py statements/amex_sample.pdf")
        print("  python validate_parser.py statements/")
        return
    
    path = sys.argv[1]
    
    if os.path.isfile(path):
        tool.validate_pdf(path)
    elif os.path.isdir(path):
        tool.batch_validate(path)
    else:
        print(f"Error: {path} is not a valid file or directory")

if __name__ == "__main__":
    main()