const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

class ApiService {
  private getHeaders(token?: string) {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    return headers;
  }

  async post(endpoint: string, data: any, token?: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(token),
        body: JSON.stringify(data),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'API request failed');
      }
      
      return result;
    } catch (error) {
      console.error(`API POST ${endpoint} error:`, error);
      throw error;
    }
  }

  async get(endpoint: string, token?: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders(token),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'API request failed');
      }
      
      return result;
    } catch (error) {
      console.error(`API GET ${endpoint} error:`, error);
      throw error;
    }
  }

  async put(endpoint: string, data: any, token?: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: this.getHeaders(token),
        body: JSON.stringify(data),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'API request failed');
      }
      
      return result;
    } catch (error) {
      console.error(`API PUT ${endpoint} error:`, error);
      throw error;
    }
  }

  async delete(endpoint: string, token?: string) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        headers: this.getHeaders(token),
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'API request failed');
      }
      
      return result;
    } catch (error) {
      console.error(`API DELETE ${endpoint} error:`, error);
      throw error;
    }
  }
}

export const apiService = new ApiService();