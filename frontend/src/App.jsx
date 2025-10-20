import React, { useState } from 'react'
import Header from './components/Header'
import FileUpload from './components/FileUpload'
import ResultsDisplay from './components/ResultsDisplay'
import { parseStatement } from './services/api'
import './App.css'

function App() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleFileUpload = async (file) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await parseStatement(file)
      setResults(response.data)
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred while parsing the statement')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResults(null)
    setError(null)
  }

  return (
    <div className="app">
      <Header />
      <main className="main-content">
        <div className="container">
          {!results && (
            <FileUpload 
              onFileUpload={handleFileUpload}
              loading={loading}
              error={error}
            />
          )}
          {results && (
            <ResultsDisplay 
              results={results}
              onReset={handleReset}
            />
          )}
        </div>
      </main>
    </div>
  )
}

export default App