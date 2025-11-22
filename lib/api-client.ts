/**
 * API Client
 * Centralized HTTP client for all backend API calls
 *
 * Authentication uses HttpOnly cookies for security:
 * - Tokens are set/cleared by the backend via Set-Cookie headers
 * - All requests include credentials to send cookies cross-origin
 * - No localStorage token storage (XSS protection)
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

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };

  try {
    // Include credentials to send/receive HttpOnly cookies
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include', // Send cookies with cross-origin requests
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
      // With HttpOnly cookies, tokens are cleared by the backend via Set-Cookie
      // We only need to redirect to login on auth failures
      if (response.status === 401) {
        const isJwtAuthError =
          errorMessage?.includes('Invalid or expired token') ||
          errorMessage?.includes('Missing or invalid authorization') ||
          endpoint === '/auth/me';

        if (isJwtAuthError && typeof window !== 'undefined') {
          // Redirect to login if on a protected page
          // Backend has already cleared cookies via logout endpoint if needed
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
