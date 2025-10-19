from dataclasses import dataclass
from datetime import date
from typing import List, Optional

@dataclass
class Transaction:
    date: str
    description: str
    amount: float
    category: Optional[str] = None

@dataclass
class StatementData:
    issuer: str
    card_last_four: str
    billing_cycle: str
    payment_due_date: str
    total_balance: float
    minimum_payment: Optional[float] = None
    transactions: List[Transaction] = None
    
    def to_dict(self):
        return {
            'issuer': self.issuer,
            'cardLastFour': self.card_last_four,
            'billingCycle': self.billing_cycle,
            'paymentDueDate': self.payment_due_date,
            'totalBalance': self.total_balance,
            'minimumPayment': self.minimum_payment,
            'transactions': [
                {
                    'date': t.date,
                    'description': t.description,
                    'amount': t.amount,
                    'category': t.category
                } for t in (self.transactions or [])
            ]
        }