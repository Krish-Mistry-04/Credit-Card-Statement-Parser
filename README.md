# Credit Card Statement Parser - Indian Banks

A full-stack application to parse credit card and bank statements from major Indian banks and extract key information.

## Supported Banks

- 🏦 **American Express** - Credit Card Statements
- 🏦 **HDFC Bank** - Credit Card Statements
- 🏦 **ICICI Bank** - Credit Card Statements
- 🏦 **Kotak Mahindra Bank** - Credit Card Statements
- 🏦 **State Bank of India** - Bank Account Statements

## Features

- 📄 PDF statement parsing
- 💳 Extracts card/account last 4 digits
- 📅 Billing cycle/statement period
- 💰 Total balance and minimum payment
- 📊 Recent transactions
- 🎨 Modern, responsive UI
- ⚡ Fast processing

## Extracted Information

- **Card Last 4 Digits**: Last 4 digits of card/account number
- **Billing Cycle**: Statement period dates
- **Payment Due Date**: When payment is due
- **Total Balance**: Outstanding balance amount
- **Minimum Payment**: Minimum amount to pay (for credit cards)
- **Transactions**: Recent 5 transactions with date, description, and amount

## Technology Stack

### Backend
- Python 3.8+
- Flask
- PyPDF2 & pdfplumber for PDF parsing
- Regular expressions for data extraction

### Frontend
- React 18
- Vite
- Axios for API calls
- react-dropzone for file upload

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the Flask server:
```bash
python src/app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Project Structure

```
credit-card-parser/
├── backend/
│   ├── src/
│   │   ├── parsers/
│   │   │   ├── base_parser.py
│   │   │   ├── amex_india_parser.py
│   │   │   ├── hdfc_parser.py
│   │   │   ├── icici_parser.py
│   │   │   ├── kotak_parser.py
│   │   │   └── sbi_parser.py
│   │   ├── models/
│   │   │   └── statement.py
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── utils/
│   │   │   └── pdf_utils.py
│   │   └── app.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── ResultsDisplay.jsx
│   │   │   └── Header.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

## API Endpoints

### POST /api/parse
Upload and parse a credit card statement PDF.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: PDF file

**Response:**
```json
{
  "success": true,
  "data": {
    "issuer": "HDFC Bank",
    "cardLastFour": "0591",
    "billingCycle": "08/05/2019 - 08/06/2019",
    "paymentDueDate": "28/06/2019",
    "totalBalance": 45240.00,
    "minimumPayment": 13636.00,
    "transactions": [
      {
        "date": "23/05/2019",
        "description": "Flipkart Payments BANGALORE",
        "amount": 8249.00
      }
    ]
  }
}
```

### GET /api/supported-issuers
Get list of supported banks.

## Usage

1. Open the application in your browser
2. Drag and drop a PDF statement or click to browse
3. Click "Parse Statement"
4. View extracted information

## Bank-Specific Notes

### American Express
- Supports 15-digit card numbers
- Extracts installment plan details
- Handles international transactions

### HDFC Bank
- Times Card and other credit cards
- Extracts reward points
- GST details included

### ICICI Bank
- Multiple card variant support
- Reward points transfer to PAYBACK
- Detailed transaction categories

### Kotak Mahindra Bank
- Corporate and personal cards
- Handles foreign currency transactions
- GST invoice details

### State Bank of India
- Bank account statements
- Savings and current accounts
- Transaction reference numbers

## Testing

Run tests with:
```bash
cd backend
pytest tests/
```

## Error Handling

The application handles various errors:
- Invalid file format
- Unsupported bank/issuer
- Corrupted PDF files
- Missing required information

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] More bank support
- [ ] Export to CSV/Excel
- [ ] Multi-statement batch processing
- [ ] Transaction categorization
- [ ] Spending analytics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Contact

For issues and questions, please open an issue on GitHub.
