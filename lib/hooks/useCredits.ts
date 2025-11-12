/**
 * Credits Hook
 * Manages credit balance fetching and state
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../api-client';

export interface CreditBalance {
  balance: number;
  monthly_allocation: number;
  total_used: number;
  total_purchased: number;
  percentage_used: number;
  warning_threshold: boolean;
  last_reset?: string;
}

export interface CreditTransaction {
  id: string;
  transaction_type: string;
  amount: number;
  balance_after: number;
  operation_type?: string;
  operation_details?: any;
  description?: string;
  created_at: string;
}

export interface CreditPackage {
  name: string;
  price_id: string;
  price: number;
  currency: string;
  credits: number;
  description: string;
  price_per_credit: number;
  badge?: string;
}

interface CreditsResponse {
  success: boolean;
  credits: CreditBalance;
}

interface TransactionHistoryResponse {
  success: boolean;
  transactions: CreditTransaction[];
  count: number;
}

interface CreditPackagesResponse {
  success: boolean;
  packages: Record<string, CreditPackage>;
}

export function useCredits() {
  const [credits, setCredits] = useState<CreditBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch credit balance
  const fetchCredits = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<CreditsResponse>('/credits/balance');

      if (response.success) {
        setCredits(response.credits);
      } else {
        setError('Failed to load credits');
      }
    } catch (err: any) {
      console.error('[Credits] Error fetching balance:', err);
      setError(err.message || 'Failed to load credits');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch transaction history
  const fetchHistory = useCallback(async (limit: number = 50): Promise<CreditTransaction[]> => {
    try {
      const response = await api.get<TransactionHistoryResponse>(`/credits/history?limit=${limit}`);
      return response.transactions || [];
    } catch (err: any) {
      console.error('[Credits] Error fetching history:', err);
      return [];
    }
  }, []);

  // Fetch available credit packages
  const fetchPackages = useCallback(async (): Promise<Record<string, CreditPackage>> => {
    try {
      const response = await api.get<CreditPackagesResponse>('/payment/credit-packages');
      return response.packages || {};
    } catch (err: any) {
      console.error('[Credits] Error fetching packages:', err);
      return {};
    }
  }, []);

  // Check if user has enough credits for an operation
  const checkCredits = useCallback(async (operationType: string): Promise<boolean> => {
    try {
      const response = await api.get<any>(`/credits/check/${operationType}`);
      return response.has_credits || false;
    } catch (err: any) {
      console.error('[Credits] Error checking availability:', err);
      return false;
    }
  }, []);

  // Refresh credits (useful after purchases or usage)
  const refresh = useCallback(() => {
    fetchCredits();
  }, [fetchCredits]);

  // Load credits on mount
  useEffect(() => {
    fetchCredits();
  }, [fetchCredits]);

  return {
    credits,
    loading,
    error,
    refresh,
    fetchHistory,
    fetchPackages,
    checkCredits,
  };
}
