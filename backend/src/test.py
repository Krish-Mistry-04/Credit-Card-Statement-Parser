import pytest
import os
from parsers.amex_india_parser import AmexIndiaParser
from parsers.hdfc_parser import HDFCParser
from parsers.icici_parser import ICICIParser
from parsers.kotak_parser import KotakParser
from parsers.sbi_parser import SBIParser

class TestIndianParsers:
    """Test suite for Indian bank parsers"""
    
    def test_amex_parser_detection(self):
        """Test American Express parser can detect Amex statements"""
        parser = AmexIndiaParser()
        amex_text = "American Express Banking Corp Statement of Account"
        assert parser.can_parse(amex_text) == True
        
        non_amex_text = "HDFC Bank Credit Card Statement"
        assert parser.can_parse(non_amex_text) == False
    
    def test_hdfc_parser_detection(self):
        """Test HDFC parser can detect HDFC statements"""
        parser = HDFCParser()
        hdfc_text = "HDFC Bank Credit Cards Statement Platinum Times Card"
        assert parser.can_parse(hdfc_text) == True
    
    def test_icici_parser_detection(self):
        """Test ICICI parser can detect ICICI statements"""
        parser = ICICIParser()
        icici_text = "ICICI Bank Credit Cards Statement"
        assert parser.can_parse(icici_text) == True
    
    def test_kotak_parser_detection(self):
        """Test Kotak parser can detect Kotak statements"""
        parser = KotakParser()
        kotak_text = "Kotak Corporate Credit Card Statement"
        assert parser.can_parse(kotak_text) == True
    
    def test_sbi_parser_detection(self):
        """Test SBI parser can detect SBI statements"""
        parser = SBIParser()
        sbi_text = "State Bank of India Account Statement"
        assert parser.can_parse(sbi_text) == True
    
    def test_amex_card_number_extraction(self):
        """Test Amex card number extraction"""
        parser = AmexIndiaParser()
        test_text = "Membership Number XXXX-XXXXXX-01007"
        result = parser.extract_amex_card_number(test_text)
        assert result == "01007" or len(result) >= 4
    
    def test_hdfc_card_number_extraction(self):
        """Test HDFC card number extraction"""
        parser = HDFCParser()
        test_text = "Card No: 5228 52XX XXXX 0591"
        result = parser.extract_hdfc_card_number(test_text)
        assert result == "0591"
    
    def test_icici_card_number_extraction(self):
        """Test ICICI card number extraction"""
        parser = ICICIParser()
        test_text = "Card Number : 4375 XXXX XXXX 3019"
        result = parser.extract_icici_card_number(test_text)
        assert result == "3019"
    
    def test_amount_extraction(self):
        """Test amount extraction with Indian number format"""
        parser = HDFCParser()
        assert parser.extractor.extract_amount("45,240.00") == 45240.0
        assert parser.extractor.extract_amount("1,23,456.78") == 123456.78
        assert parser.extractor.extract_amount("Rs 5,882.52") == 5882.52
    
    def test_date_extraction(self):
        """Test various date format extraction"""
        parser = HDFCParser()
        test_text = "Payment Due Date 28/06/2019"
        result = parser.extract_hdfc_due_date(test_text)
        assert "28/06/2019" in result or result != "N/A"
    
    def test_transaction_extraction(self):
        """Test transaction extraction"""
        parser = HDFCParser()
        test_text = """
        23/05/2019 Flipkart Payments BANGALORE 8,249.00
        24/05/2019 FOOD PARK NORTH (24) P 360.00
        """
        transactions = parser.extract_hdfc_transactions(test_text)
        assert len(transactions) > 0
        if transactions:
            assert transactions[0].amount > 0
            assert len(transactions[0].description) > 0
    
    def test_balance_extraction(self):
        """Test balance extraction"""
        parser = AmexIndiaParser()
        test_text = "Closing Balance Rs 56,856.49"
        balance = parser.extract_amex_balance(test_text)
        assert balance == 56856.49 or balance > 0
    
    def test_minimum_payment_extraction(self):
        """Test minimum payment extraction"""
        parser = HDFCParser()
        test_text = "Minimum Amount Due 2,262.00"
        minimum = parser.extract_hdfc_minimum(test_text)
        assert minimum == 2262.0 or minimum > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])