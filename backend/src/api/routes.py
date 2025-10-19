from flask import Blueprint, request, jsonify
import os
import tempfile
from werkzeug.utils import secure_filename
from parsers.chase_parser import ChaseParser
from parsers.amex_parser import AmexParser
from parsers.bofa_parser import BofAParser
from parsers.citi_parser import CitiParser
from parsers.wells_fargo_parser import WellsFargoParser
from utils.pdf_utils import PDFExtractor

api_blueprint = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {'pdf'}
PARSERS = [
    ChaseParser(),
    AmexParser(),
    BofAParser(),
    CitiParser(),
    WellsFargoParser()
]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_blueprint.route('/parse', methods=['POST'])
def parse_statement():
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed'}), 400
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Extract text to determine issuer
            extractor = PDFExtractor()
            text = extractor.extract_text_pdfplumber(temp_path)
            
            # Find appropriate parser
            parser = None
            for p in PARSERS:
                if p.can_parse(text):
                    parser = p
                    break
            
            if not parser:
                return jsonify({'error': 'Unsupported credit card issuer'}), 400
            
            # Parse the statement
            statement_data = parser.parse(temp_path)
            
            return jsonify({
                'success': True,
                'data': statement_data.to_dict()
            }), 200
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_blueprint.route('/supported-issuers', methods=['GET'])
def get_supported_issuers():
    issuers = [
        'Chase',
        'American Express',
        'Bank of America',
        'Citi',
        'Wells Fargo'
    ]
    return jsonify({'issuers': issuers}), 200