import React from 'react'

const ResultsDisplay = ({ results, onReset }) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Parsed Statement Data</h2>
        <button className="reset-button" onClick={onReset}>
          Parse Another Statement
        </button>
      </div>

      <div className="issuer-badge">{results.issuer}</div>

      <div className="data-grid">
        <div className="data-card">
          <div className="data-label">Card Number</div>
          <div className="data-value">•••• {results.cardLastFour}</div>
        </div>

        <div className="data-card">
          <div className="data-label">Billing Cycle</div>
          <div className="data-value">{results.billingCycle}</div>
        </div>

        <div className="data-card">
          <div className="data-label">Payment Due Date</div>
          <div className="data-value">{results.paymentDueDate}</div>
        </div>

        <div className="data-card">
          <div className="data-label">Total Balance</div>
          <div className="data-value amount">
            {formatCurrency(results.totalBalance)}
          </div>
        </div>

        {results.minimumPayment && (
          <div className="data-card">
            <div className="data-label">Minimum Payment</div>
            <div className="data-value amount">
              {formatCurrency(results.minimumPayment)}
            </div>
          </div>
        )}
      </div>

      {results.transactions && results.transactions.length > 0 && (
        <div className="transactions-section">
          <h3>Recent Transactions</h3>
          <div className="transaction-list">
            {results.transactions.map((transaction, index) => (
              <div key={index} className="transaction-item">
                <div className="transaction-info">
                  <div className="transaction-date">{transaction.date}</div>
                  <div className="transaction-description">
                    {transaction.description}
                  </div>
                </div>
                <div className="transaction-amount">
                  {formatCurrency(transaction.amount)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ResultsDisplay