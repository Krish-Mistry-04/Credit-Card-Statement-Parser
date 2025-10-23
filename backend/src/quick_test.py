#!/usr/bin/env python3
"""
Quick Test Script
Run quick tests on your parsers
"""

import sys
import os
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{text}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

def test_single_pdf(pdf_path):
    """Quick test on a single PDF"""
    from utils.pdf_utils import PDFExtractor
    from parsers.amex_india_parser import AmexIndiaParser
    from parsers.hdfc_parser import HDFCParser
    from parsers.icici_parser import ICICIParser
    from parsers.kotak_parser import KotakParser
    from parsers.sbi_parser import SBIParser
    
    print_header(f"TESTING: {os.path.basename(pdf_path)}")
    
    # Extract text
    print_info("Extracting PDF text...")
    try:
        extractor = PDFExtractor()
        text = extractor.extract_text_pdfplumber(pdf_path)
        print_success(f"Extracted {len(text)} characters")
    except Exception as e:
        print_error(f"Failed to extract text: {e}")
        return False
    
    # Find parser
    print_info("Detecting bank...")
    parsers = [
        AmexIndiaParser(),
        HDFCParser(),
        ICICIParser(),
        KotakParser(),
        SBIParser()
    ]
    
    parser = None
    for p in parsers:
        if p.can_parse(text):
            parser = p
            break
    
    if not parser:
        print_error("No parser found - unsupported bank")
        print_warning("Supported banks: American Express, HDFC, ICICI, Kotak, SBI")
        return False
    
    print_success(f"Detected: {parser.__class__.__name__}")
    
    # Parse PDF
    print_info("Parsing statement...")
    try:
        statement = parser.parse(pdf_path)
        print_success("Parse completed!")
    except Exception as e:
        print_error(f"Parse failed: {e}")
        return False
    
    # Display results
    print_header("EXTRACTED DATA")
    
    results = {
        "Issuer": statement.issuer,
        "Card Last 4": statement.card_last_four,
        "Billing Cycle": statement.billing_cycle,
        "Due Date": statement.payment_due_date,
        "Total Balance": f"₹{statement.total_balance:,.2f}",
        "Minimum Payment": f"₹{statement.minimum_payment:,.2f}",
        "Transactions": len(statement.transactions or [])
    }
    
    # Check each field
    all_good = True
    for field, value in results.items():
        if value in ["N/A", "0.00", 0]:
            print_warning(f"{field:20}: {value}")
            all_good = False
        else:
            print_success(f"{field:20}: {value}")
    
    # Show transactions
    if statement.transactions:
        print(f"\n{Fore.BLUE}Top Transactions:{Style.RESET_ALL}")
        for i, txn in enumerate(statement.transactions[:3], 1):
            print(f"  {i}. {txn.date:12} {txn.description[:35]:35} ₹{txn.amount:>10,.2f}")
    
    # Summary
    print()
    if all_good:
        print_success("All fields extracted successfully!")
        return True
    else:
        print_warning("Some fields missing or incorrect")
        return False

def test_directory(directory):
    """Test all PDFs in a directory"""
    pdf_files = list(Path(directory).glob("*.pdf"))
    
    if not pdf_files:
        print_error(f"No PDF files found in {directory}")
        return
    
    print_header(f"TESTING {len(pdf_files)} PDFs")
    
    results = []
    for pdf_file in pdf_files:
        success = test_single_pdf(str(pdf_file))
        results.append((pdf_file.name, success))
    
    # Summary
    print_header("SUMMARY")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        if success:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{Fore.CYAN}Passed: {passed}/{total} ({passed/total*100:.1f}%){Style.RESET_ALL}")

def compare_with_expected(pdf_path):
    """Interactive comparison with expected values"""
    from utils.pdf_utils import PDFExtractor
    from parsers.amex_india_parser import AmexIndiaParser
    from parsers.hdfc_parser import HDFCParser
    from parsers.icici_parser import ICICIParser
    from parsers.kotak_parser import KotakParser
    from parsers.sbi_parser import SBIParser
    
    print_header(f"COMPARE: {os.path.basename(pdf_path)}")
    
    # Get parser
    extractor = PDFExtractor()
    text = extractor.extract_text_pdfplumber(pdf_path)
    
    parsers = [
        AmexIndiaParser(),
        HDFCParser(),
        ICICIParser(),
        KotakParser(),
        SBIParser()
    ]
    
    parser = None
    for p in parsers:
        if p.can_parse(text):
            parser = p
            break
    
    if not parser:
        print_error("No parser found")
        return
    
    statement = parser.parse(pdf_path)
    
    # Ask for expected values
    print_info("Enter expected values from the PDF (press Enter to skip):\n")
    
    expected = {}
    expected['card'] = input(f"  Card last 4 digits: ").strip()
    expected['balance'] = input(f"  Total balance: ").strip()
    expected['minimum'] = input(f"  Minimum payment: ").strip()
    expected['due'] = input(f"  Due date: ").strip()
    
    # Compare
    print_header("COMPARISON")
    
    if expected['card']:
        match = expected['card'] == statement.card_last_four
        if match:
            print_success(f"Card Number: {statement.card_last_four}")
        else:
            print_error(f"Card Number: Expected '{expected['card']}', Got '{statement.card_last_four}'")
    
    if expected['balance']:
        try:
            exp_bal = float(expected['balance'].replace(',', ''))
            match = abs(exp_bal - statement.total_balance) < 0.01
            if match:
                print_success(f"Balance: ₹{statement.total_balance:,.2f}")
            else:
                print_error(f"Balance: Expected ₹{exp_bal:,.2f}, Got ₹{statement.total_balance:,.2f}")
        except ValueError:
            print_warning("Invalid balance format")
    
    if expected['minimum']:
        try:
            exp_min = float(expected['minimum'].replace(',', ''))
            match = abs(exp_min - statement.minimum_payment) < 0.01
            if match:
                print_success(f"Minimum Payment: ₹{statement.minimum_payment:,.2f}")
            else:
                print_error(f"Minimum Payment: Expected ₹{exp_min:,.2f}, Got ₹{statement.minimum_payment:,.2f}")
        except ValueError:
            print_warning("Invalid minimum payment format")
    
    if expected['due']:
        match = expected['due'] in statement.payment_due_date
        if match:
            print_success(f"Due Date: {statement.payment_due_date}")
        else:
            print_error(f"Due Date: Expected '{expected['due']}', Got '{statement.payment_due_date}'")

def show_menu():
    """Show main menu"""
    print_header("QUICK TEST MENU")
    print("1. Test single PDF")
    print("2. Test directory (batch)")
    print("3. Compare with expected values")
    print("4. Open interactive debugger")
    print("5. View raw PDF text")
    print("0. Exit")
    print()

def view_raw_text(pdf_path):
    """View raw PDF text"""
    from utils.pdf_utils import PDFExtractor
    
    print_header(f"RAW TEXT: {os.path.basename(pdf_path)}")
    
    extractor = PDFExtractor()
    text = extractor.extract_text_pdfplumber(pdf_path)
    
    print_info(f"Total length: {len(text)} characters\n")
    
    # Show first 2000 characters
    print(text[:2000])
    print(f"\n{Fore.YELLOW}(Showing first 2000 of {len(text)} characters){Style.RESET_ALL}")
    
    # Offer to save
    save = input("\nSave full text to file? (y/n): ").strip().lower()
    if save == 'y':
        output_file = f"{os.path.splitext(pdf_path)[0]}_raw_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print_success(f"Saved to {output_file}")

def main():
    print(f"{Fore.CYAN}")
    print(r"""
    ╔═══════════════════════════════════════════╗
    ║   Credit Card Parser - Quick Test Tool   ║
    ╚═══════════════════════════════════════════╝
    """)
    print(f"{Style.RESET_ALL}")
    
    if len(sys.argv) > 1:
        # Command line mode
        path = sys.argv[1]
        
        if os.path.isfile(path):
            test_single_pdf(path)
        elif os.path.isdir(path):
            test_directory(path)
        else:
            print_error(f"Invalid path: {path}")
    else:
        # Interactive mode
        while True:
            show_menu()
            choice = input("Enter choice: ").strip()
            
            if choice == "0":
                print("\n👋 Goodbye!\n")
                break
            
            elif choice == "1":
                path = input("Enter PDF path: ").strip()
                if os.path.exists(path):
                    test_single_pdf(path)
                else:
                    print_error("File not found")
            
            elif choice == "2":
                path = input("Enter directory path: ").strip()
                if os.path.exists(path):
                    test_directory(path)
                else:
                    print_error("Directory not found")
            
            elif choice == "3":
                path = input("Enter PDF path: ").strip()
                if os.path.exists(path):
                    compare_with_expected(path)
                else:
                    print_error("File not found")
            
            elif choice == "4":
                path = input("Enter PDF path: ").strip()
                if os.path.exists(path):
                    print_info("Launching interactive debugger...")
                    os.system(f"python interactive_debugger.py {path}")
                else:
                    print_error("File not found")
            
            elif choice == "5":
                path = input("Enter PDF path: ").strip()
                if os.path.exists(path):
                    view_raw_text(path)
                else:
                    print_error("File not found")
            
            else:
                print_error("Invalid choice")
            
            input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            print("\n" * 2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)