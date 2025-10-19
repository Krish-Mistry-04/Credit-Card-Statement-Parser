import pytest
import os
from parsers.chase_parser import ChaseParser
from parsers.amex_parser import AmexParser
from parsers.bofa_parser import BofAParser
from parsers.citi_parser import CitiParser
from parsers.wells_fargo_parser import WellsFargoParser

class TestParsers:
    def test_chase_parser_detection(self):
        parser = ChaseParser()
        chase_text = "Chase Bank Statement Account Summary"
        assert parser.can_parse(chase_text) == True
        
        non_chase_text = "Bank of America Statement"
        assert parser.can_parse(non_chase_text) == False
    
    def test_amex_parser_detection(self):
        parser = AmexParser()
        amex_text = "American Express Statement of Account"
        assert parser.can_parse(amex_text) == True
    
    def test_card_number_extraction(self):
        parser = ChaseParser()
        test_text = "Account Number: XXXX-XXXX-XXXX-1234"
        result = parser.extract_card_last_four(test_text)
        assert result == "1234"
    
    def test_amount_extraction(self):
        parser = ChaseParser()
        assert parser.extractor.extract_amount("$1,234.56") == 1234.56
        assert parser.extractor.extract_amount("1234.56") == 1234.56
        assert parser.extractor.extract_amount("$1,234") == 1234.0