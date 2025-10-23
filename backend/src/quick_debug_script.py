#!/usr/bin/env python3
"""
Quick Debug Script - Find out why extraction is failing
Run this on your failing PDFs to get immediate answers
"""

import sys
import re
import pdfplumber

def quick_debug(pdf_path):
    """Quick diagnostic for extraction issues"""
    
    print(f"\n{'='*80}")
    print(f"🔍 QUICK DEBUG: {pdf_path}")
    print(f"{'='*80}\n")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Get first page
        page = pdf.pages[0]
        
        # Extract text
        text = page.extract_text()
        
        if not text or len(text) < 50:
            print("❌ PROBLEM: Very little text extracted!")
            print("   This PDF might be:")
            print("   - Scanned image (needs OCR)")
            print("   - Encrypted")
            print("   - Corrupted")
            return
        
        print(f"✅ Text extracted: {len(text)} characters\n")
        
        # Check for key fields
        print("🔎 SEARCHING FOR KEY FIELDS:")
        print("-" * 80)
        
        checks = {
            "Card Number": [
                r'\d{4}[\s\-]*\d{4}[\s\-]*\d{4}[\s\-]*\d{4}',
                r'\d{4}[\s\-]*[Xx]{4}[\s\-]*[Xx]{4}[\s\-]*\d{4}',
                r'\d{6}[Xx]{6}\d{4}',
                r'[Xx]{4}[\s\-]*[Xx]{6}[\s\-]*\d{5}',
            ],
            "Date": [
                r'\d{1,2}/\d{1,2}/\d{4}',
                r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}',
                r'\d{1,2}-[A-Za-z]{3}-\d{4}',
            ],
            "Amount": [
                r'₹\s*[\d,]+\.?\d*',
                r'Rs\.?\s*[\d,]+\.?\d*',
                r'[\d,]+\.\d{2}',
            ],
            "Balance": [
                r'(?:Total|Balance|Due).*?[\d,]+\.\d{2}',
                r'Closing Balance',
                r'Total Amount Due',
            ],
        }
        
        for field, patterns in checks.items():
            found = False
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    print(f"✅ {field:15} Found! Examples: {matches[:3]}")
                    found = True
                    break
            
            if not found:
                print(f"❌ {field:15} NOT FOUND")
        
        # Check for tables
        print(f"\n📊 TABLE DETECTION:")
        print("-" * 80)
        
        tables = page.extract_tables()
        
        if tables:
            print(f"✅ Found {len(tables)} table(s)")
            for i, table in enumerate(tables):
                if table:
                    print(f"\n   Table {i+1}:")
                    print(f"   - Rows: {len(table)}")
                    print(f"   - Columns: {len(table[0]) if table else 0}")
                    if len(table) > 0:
                        print(f"   - Headers: {table[0]}")
        else:
            print("❌ No tables found with default settings")
            print("   Trying alternative settings...")
            
            table_settings = {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
            }
            tables_alt = page.extract_tables(table_settings=table_settings)
            
            if tables_alt:
                print(f"✅ Found {len(tables_alt)} table(s) with alternative settings!")
            else:
                print("❌ No tables found with any settings")
                print("   → Your PDF might not have structured tables")
                print("   → Use text-based extraction instead")
        
        # Show sample text
        print(f"\n📄 TEXT SAMPLE (first 500 chars):")
        print("-" * 80)
        print(text[:500])
        print("-" * 80)
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        print("="*80)
        
        if not tables:
            print("1. ⚠️  NO TABLES: Use text-based extraction with regex patterns")
            print("   → Update your parser to extract from text, not tables")
        
        card_found = any(re.search(p, text, re.IGNORECASE) for patterns in checks["Card Number"] for p in patterns)
        if not card_found:
            print("2. ⚠️  CARD NUMBER NOT FOUND: Check if it's masked differently")
            print("   → Search manually in PDF for card number format")
            print("   → Update card number regex pattern")
        
        amount_matches = sum(len(re.findall(p, text, re.IGNORECASE)) for p in checks["Amount"])
        if amount_matches < 3:
            print("3. ⚠️  FEW AMOUNTS FOUND: Check currency format")
            print("   → Your PDF might use different currency symbols")
            print("   → Update amount extraction patterns")
        
        print("\n📋 NEXT STEPS:")
        print("="*80)
        print("1. Run full analyzer: python pdf_analyzer.py", pdf_path)
        print("2. Test robust extractor: python robust_universal_parser.py", pdf_path)
        print("3. Update parser patterns based on what's found above")
        print("="*80 + "\n")


def batch_debug(pdf_files):
    """Debug multiple PDFs"""
    for pdf_file in pdf_files:
        try:
            quick_debug(pdf_file)
        except Exception as e:
            print(f"\n❌ ERROR processing {pdf_file}: {e}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_debug_script.py <pdf_file> [pdf_file2] [pdf_file3] ...")
        print("\nExample:")
        print("  python quick_debug_script.py icici.pdf")
        print("  python quick_debug_script.py icici.pdf kotak.pdf amex.pdf")
        sys.exit(1)
    
    pdf_files = sys.argv[1:]
    
    if len(pdf_files) == 1:
        quick_debug(pdf_files[0])
    else:
        batch_debug(pdf_files)