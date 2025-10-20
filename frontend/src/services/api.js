import axios from 'axios'

const API_BASE_URL = '/api'

export const parseStatement = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE_URL}/parse`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

export const getSupportedIssuers = async () => {
  const response = await axios.get(`${API_BASE_URL}/supported-issuers`)
  return response.data
}