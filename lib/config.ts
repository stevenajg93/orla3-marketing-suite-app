/**
 * Application Configuration
 * Single source of truth for all environment variables
 */

export const config = {
  // API Configuration
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Environment
  isDev: process.env.NODE_ENV === 'development',
  isProd: process.env.NODE_ENV === 'production',
  
  // Feature Flags
  enableDebugLogs: process.env.NODE_ENV === 'development',
} as const;

// Type-safe config access
export type Config = typeof config;
