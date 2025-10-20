import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const FileUpload = ({ onFileUpload, loading, error }) => {
  const [file, setFile] = useState(null)

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  const handleUpload = () => {
    if (file) {
      onFileUpload(file)
    }
  }

  const removeFile = () => {
    setFile(null)
  }

  return (
    <div className="upload-container">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="dropzone-icon">📄</div>
        <p>Drag & drop your credit card statement here</p>
        <span>or click to browse (PDF files only)</span>
      </div>

      {file && (
        <div className="file-info">
          <span className="file-name">📎 {file.name}</span>
          <button className="remove-file" onClick={removeFile}>✕</button>
        </div>
      )}

      {file && (
        <button 
          className="upload-button" 
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? (
            <>Parsing Statement<span className="loading-spinner"></span></>
          ) : (
            'Parse Statement'
          )}
        </button>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="supported-issuers">
        <h3>Supported Credit Card Issuers:</h3>
        <div className="issuer-list">
          <span className="issuer-tag">Chase</span>
          <span className="issuer-tag">American Express</span>
          <span className="issuer-tag">Bank of America</span>
          <span className="issuer-tag">Citi</span>
          <span className="issuer-tag">Wells Fargo</span>
        </div>
      </div>
    </div>
  )
}

export default FileUpload