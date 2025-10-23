"""
Interactive Parser Debugger
Debug parser behavior step-by-step
"""

import re
import sys
from utils.pdf_utils import PDFExtractor
from parsers.amex_india_parser import AmexIndiaParser
from parsers.hdfc_parser import HDFCParser
from parsers.icici_parser import ICICIParser
from parsers.kotak_parser import KotakParser
from parsers.sbi_parser import SBIParser

class InteractiveDebugger:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.extractor = PDFExtractor()
        self.text = self.extractor.extract_text_pdfplumber(pdf_path)
        
        self.parsers = {
            "1": ("American Express", AmexIndiaParser()),
            "2": ("HDFC Bank", HDFCParser()),
            "3": ("ICICI Bank", ICICIParser()),
            "4": ("Kotak Mahindra Bank", KotakParser()),
            "5": ("SBI", SBIParser())
        }
        
        self.selected_parser = None
    
    def start(self):
        """Start interactive debugging session"""
        print("\n" + "="*80)
        print("🔧 INTERACTIVE PARSER DEBUGGER")
        print("="*80 + "\n")
        print(f"PDF: {self.pdf_path}")
        print(f"Text length: {len(self.text)} characters\n")
        
        while True:
            self.show_menu()
            choice = input("\nEnter choice: ").strip()
            
            if choice == "0":
                print("Goodbye!")
                break
            
            self.handle_choice(choice)
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "-"*80)
        print("MAIN MENU")
        print("-"*80)
        print("1. View raw PDF text")
        print("2. Search in PDF text")
        print("3. Test regex patterns")
        print("4. Select parser")
        print("5. Test field extraction")
        print("6. Run full parse")
        print("7. Compare with expected values")
        print("8. Show extraction patterns")
        print("0. Exit")
        print("-"*80)
    
    def handle_choice(self, choice: str):
        """Handle menu choice"""
        if choice == "1":
            self.view_text()
        elif choice == "2":
            self.search_text()
        elif choice == "3":
            self.test_regex()
        elif choice == "4":
            self.select_parser()
        elif choice == "5":
            self.test_field_extraction()
        elif choice == "6":
            self.run_full_parse()
        elif choice == "7":
            self.compare_expected()
        elif choice == "8":
            self.show_patterns()
        else:
            print("Invalid choice")
    
    def view_text(self):
        """View raw PDF text"""
        print("\n📄 RAW PDF TEXT:")
        print("-"*80)
        
        start = input("Start position (default 0): ").strip()
        start = int(start) if start else 0
        
        length = input("Length (default 1000): ").strip()
        length = int(length) if length else 1000
        
        print(self.text[start:start+length])
        print("-"*80)
        print(f"Showing characters {start} to {start+length} of {len(self.text)}")
    
    def search_text(self):
        """Search for text in PDF"""
        search_term = input("Enter search term: ").strip()
        
        if not search_term:
            return
        
        print(f"\n🔍 Searching for '{search_term}'...")
        print("-"*80)
        
        # Case insensitive search
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        matches = list(pattern.finditer(self.text))
        
        print(f"Found {len(matches)} matches\n")
        
        for i, match in enumerate(matches[:10], 1):  # Show first 10
            start = max(0, match.start() - 50)
            end = min(len(self.text), match.end() + 50)
            context = self.text[start:end].replace('\n', ' ')
            print(f"{i}. Position {match.start()}: ...{context}...")
        
        if len(matches) > 10:
            print(f"\n(Showing first 10 of {len(matches)} matches)")
    
    def test_regex(self):
        """Test regex patterns"""
        print("\n🔬 REGEX PATTERN TESTER")
        print("-"*80)
        
        pattern = input("Enter regex pattern: ").strip()
        
        if not pattern:
            return
        
        try:
            regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            matches = list(regex.finditer(self.text))
            
            print(f"\n✅ Valid regex! Found {len(matches)} matches\n")
            
            for i, match in enumerate(matches[:10], 1):
                print(f"{i}. Match: {match.group(0)[:100]}")
                if match.groups():
                    print(f"   Groups: {match.groups()}")
                print()
            
            if len(matches) > 10:
                print(f"(Showing first 10 of {len(matches)} matches)")
        
        except re.error as e:
            print(f"❌ Invalid regex: {e}")
    
    def select_parser(self):
        """Select a parser"""
        print("\n📋 SELECT PARSER:")
        print("-"*80)
        
        for key, (name, parser) in self.parsers.items():
            status = "✓" if parser.can_parse(self.text) else " "
            print(f"{key}. [{status}] {name}")
        
        choice = input("\nSelect parser (1-5): ").strip()
        
        if choice in self.parsers:
            self.selected_parser = self.parsers[choice]
            print(f"\n✅ Selected: {self.selected_parser[0]}")
        else:
            print("Invalid choice")
    
    def test_field_extraction(self):
        """Test individual field extraction"""
        if not self.selected_parser:
            print("⚠️  Please select a parser first (option 4)")
            return
        
        parser_name, parser = self.selected_parser
        
        print(f"\n🔍 TESTING FIELD EXTRACTION - {parser_name}")
        print("-"*80)
        print("1. Card Number")
        print("2. Billing Cycle")
        print("3. Due Date")
        print("4. Total Balance")
        print("5. Minimum Payment")
        print("6. Transactions")
        print("7. All fields")
        
        choice = input("\nSelect field: ").strip()
        
        if choice == "1":
            result = self._extract_card_number(parser)
            print(f"\n💳 Card Number: {result}")
        
        elif choice == "2":
            result = self._extract_billing_cycle(parser)
            print(f"\n📅 Billing Cycle: {result}")
        
        elif choice == "3":
            result = self._extract_due_date(parser)
            print(f"\n📆 Due Date: {result}")
        
        elif choice == "4":
            result = self._extract_balance(parser)
            print(f"\n💰 Balance: ₹{result:,.2f}")
        
        elif choice == "5":
            result = self._extract_minimum(parser)
            print(f"\n💵 Minimum Payment: ₹{result:,.2f}")
        
        elif choice == "6":
            result = self._extract_transactions(parser)
            print(f"\n📝 Transactions ({len(result)}):")
            for i, txn in enumerate(result[:5], 1):
                print(f"  {i}. {txn.date:15} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")
        
        elif choice == "7":
            self._extract_all_fields(parser)
    
    def _extract_card_number(self, parser):
        """Extract card number based on parser type"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_card_number(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_card_number(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_card_number(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_card_number(self.text)
        elif isinstance(parser, SBIParser):
            return parser.extract_sbi_card_number(self.text)
    
    def _extract_billing_cycle(self, parser):
        """Extract billing cycle"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_billing_cycle(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_billing_cycle(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_billing_cycle(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_billing_cycle(self.text)
        elif isinstance(parser, SBIParser):
            return parser.extract_sbi_billing_cycle(self.text)
    
    def _extract_due_date(self, parser):
        """Extract due date"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_due_date(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_due_date(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_due_date(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_due_date(self.text)
        elif isinstance(parser, SBIParser):
            return "N/A"
    
    def _extract_balance(self, parser):
        """Extract balance"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_balance(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_balance(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_balance(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_balance(self.text)
        elif isinstance(parser, SBIParser):
            return parser.extract_sbi_balance(self.text)
    
    def _extract_minimum(self, parser):
        """Extract minimum payment"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_minimum(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_minimum(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_minimum(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_minimum(self.text)
        elif isinstance(parser, SBIParser):
            return 0.0
    
    def _extract_transactions(self, parser):
        """Extract transactions"""
        if isinstance(parser, AmexIndiaParser):
            return parser.extract_amex_transactions(self.text)
        elif isinstance(parser, HDFCParser):
            return parser.extract_hdfc_transactions(self.text)
        elif isinstance(parser, ICICIParser):
            return parser.extract_icici_transactions(self.text)
        elif isinstance(parser, KotakParser):
            return parser.extract_kotak_transactions(self.text)
        elif isinstance(parser, SBIParser):
            return parser.extract_sbi_transactions(self.text)
    
    def _extract_all_fields(self, parser):
        """Extract all fields"""
        print("\n📊 ALL FIELDS:")
        print("-"*80)
        print(f"Card Number:      {self._extract_card_number(parser)}")
        print(f"Billing Cycle:    {self._extract_billing_cycle(parser)}")
        print(f"Due Date:         {self._extract_due_date(parser)}")
        print(f"Balance:          ₹{self._extract_balance(parser):,.2f}")
        print(f"Minimum Payment:  ₹{self._extract_minimum(parser):,.2f}")
        
        transactions = self._extract_transactions(parser)
        print(f"\nTransactions ({len(transactions)}):")
        for i, txn in enumerate(transactions[:5], 1):
            print(f"  {i}. {txn.date:15} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")
    
    def run_full_parse(self):
        """Run full parse"""
        if not self.selected_parser:
            print("⚠️  Please select a parser first (option 4)")
            return
        
        parser_name, parser = self.selected_parser
        
        print(f"\n⚙️  RUNNING FULL PARSE - {parser_name}")
        print("-"*80)
        
        try:
            statement = parser.parse(self.pdf_path)
            
            print("\n✅ Parse successful!\n")
            print(f"Issuer:           {statement.issuer}")
            print(f"Card Number:      {statement.card_last_four}")
            print(f"Billing Cycle:    {statement.billing_cycle}")
            print(f"Due Date:         {statement.payment_due_date}")
            print(f"Balance:          ₹{statement.total_balance:,.2f}")
            print(f"Minimum Payment:  ₹{statement.minimum_payment:,.2f}")
            
            print(f"\nTransactions ({len(statement.transactions or [])}):")
            for i, txn in enumerate((statement.transactions or [])[:5], 1):
                print(f"  {i}. {txn.date:15} {txn.description[:40]:40} ₹{txn.amount:>10,.2f}")
        
        except Exception as e:
            print(f"\n❌ Parse failed: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    def compare_expected(self):
        """Compare with expected values"""
        print("\n📋 COMPARE WITH EXPECTED VALUES")
        print("-"*80)
        print("Enter expected values (press Enter to skip):\n")
        
        expected = {}
        expected['card_last_four'] = input("Card last 4 digits: ").strip()
        expected['billing_cycle'] = input("Billing cycle: ").strip()
        expected['due_date'] = input("Due date: ").strip()
        expected['balance'] = input("Total balance: ").strip()
        expected['minimum'] = input("Minimum payment: ").strip()
        
        if not self.selected_parser:
            print("\n⚠️  Please select a parser first")
            return
        
        parser_name, parser = self.selected_parser
        statement = parser.parse(self.pdf_path)
        
        print("\n📊 COMPARISON:")
        print("-"*80)
        
        def compare_field(label, expected_val, actual_val):
            if not expected_val:
                return
            match = expected_val.lower() in str(actual_val).lower()
            status = "✅" if match else "❌"
            print(f"{status} {label:20}: Expected: {expected_val:30} | Got: {str(actual_val)[:30]}")
        
        compare_field("Card Number", expected['card_last_four'], statement.card_last_four)
        compare_field("Billing Cycle", expected['billing_cycle'], statement.billing_cycle)
        compare_field("Due Date", expected['due_date'], statement.payment_due_date)
        
        if expected['balance']:
            exp_bal = float(expected['balance'].replace(',', ''))
            match = abs(exp_bal - statement.total_balance) < 0.01
            status = "✅" if match else "❌"
            print(f"{status} {'Balance':20}: Expected: ₹{exp_bal:,.2f}            | Got: ₹{statement.total_balance:,.2f}")
        
        if expected['minimum']:
            exp_min = float(expected['minimum'].replace(',', ''))
            match = abs(exp_min - statement.minimum_payment) < 0.01
            status = "✅" if match else "❌"
            print(f"{status} {'Minimum Payment':20}: Expected: ₹{exp_min:,.2f}            | Got: ₹{statement.minimum_payment:,.2f}")
    
    def show_patterns(self):
        """Show extraction patterns used by parser"""
        if not self.selected_parser:
            print("⚠️  Please select a parser first (option 4)")
            return
        
        parser_name, parser = self.selected_parser
        
        print(f"\n📝 EXTRACTION PATTERNS - {parser_name}")
        print("-"*80)
        print("\nNote: This shows the regex patterns used by the parser.")
        print("You can test these patterns with option 3 (Test regex patterns)\n")
        
        # This would ideally show the patterns from the parser
        # For now, just show a message
        print("To see patterns, look at the parser source code:")
        print(f"  backend/src/parsers/{parser.__class__.__name__.lower()}.py")

def main():
    if len(sys.argv) < 2:
        print("Usage: python interactive_debugger.py <pdf_file>")
        return
    
    pdf_path = sys.argv[1]
    debugger = InteractiveDebugger(pdf_path)
    debugger.start()

if __name__ == "__main__":
    main()