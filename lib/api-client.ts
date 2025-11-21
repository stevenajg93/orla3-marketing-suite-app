/**
 * API Client
 * Centralized HTTP client for all backend API calls
 */

import { config } from './config';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public endpoint: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Get JWT access token from localStorage
 */
function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/**
 * Make an API request to the backend
 * @param endpoint - API endpoint (e.g., '/strategy/next-keyword')
 * @param options - Fetch options
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${config.apiUrl}${endpoint}`;

  if (config.enableDebugLogs) {
    console.log(`[API] ${options?.method || 'GET'} ${url}`);
  }

  // Get access token and add to headers
  const token = getAccessToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };

  // Add Authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      // Try to get error message from response body
      let errorMessage = response.statusText;
      let errorData: any = null;
      try {
        errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // If JSON parsing fails, use statusText
      }

      // If 401 Unauthorized AND it's a JWT auth error (not OAuth/Drive errors)
      if (response.status === 401) {
        // Only clear tokens if it's an actual JWT authentication failure
        // Don't clear for Google Drive OAuth errors or other 401s
        const isJwtAuthError =
          errorMessage?.includes('Invalid or expired token') ||
          errorMessage?.includes('Missing authorization token') ||
          errorMessage?.includes('Missing or invalid authorization header') ||
          endpoint === '/auth/me'; // Always clear on /auth/me failure

        if (isJwtAuthError && typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');

          // Redirect to login if on a protected page
          if (window.location.pathname.startsWith('/dashboard')) {
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
          }
        }
      }

      throw new ApiError(
        errorMessage,
        response.status,
        endpoint
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;

    // Network error or other fetch failure
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      endpoint
    );
  }
}

/**
 * Convenience methods for common HTTP verbs
 */
export const api = {
  get: <T = any>(endpoint: string) => 
    apiRequest<T>(endpoint, { method: 'GET' }),
  
  post: <T = any>(endpoint: string, body?: any) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  
  put: <T = any>(endpoint: string, body?: any) =>
    apiRequest<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  patch: <T = any>(endpoint: string, body?: any) =>
    apiRequest<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  delete: <T = any>(endpoint: string) =>
    apiRequest<T>(endpoint, { method: 'DELETE' }),
};
