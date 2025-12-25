'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/lib/api-config';
import {
  Activity,
  TrendingUp,
  DollarSign,
  Zap,
  BarChart3,
  Star
} from 'lucide-react';

interface ProviderAnalytics {
  provider: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  average_latency: number;
  success_rate: number;
  last_used: number | null;
  total_cost?: number;
  average_quality?: number;
}

interface AnalyticsData {
  analytics: ProviderAnalytics[];
  total_generations: number;
  total_cost: number;
  average_quality: number;
  timestamp: string;
}

export default function AIAnalyticsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.sub || payload.email });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    // Load analytics data
    loadAnalytics();
  }, [router]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8080/api/ai/provider-usage-analytics', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Failed to load analytics');
        return;
      }

      // Calculate totals from the provider analytics
      const totalGenerations = data.analytics.reduce(
        (sum: number, p: ProviderAnalytics) => sum + p.total_requests,
        0
      );

      // Calculate total cost (mock calculation based on tokens)
      const totalCost = data.analytics.reduce(
        (sum: number, p: ProviderAnalytics) => {
          // Rough estimate: $0.002 per 1000 tokens
          const costEstimate = (p.total_tokens / 1000) * 0.002;
          return sum + costEstimate;
        },
        0
      );

      // Calculate average quality (mock for now)
      const avgQuality = 85.5; // Placeholder

      setAnalytics({
        analytics: data.analytics || [],
        total_generations: totalGenerations,
        total_cost: totalCost,
        average_quality: avgQuality,
        timestamp: data.timestamp
      });
    } catch (err) {
      setError('Network error. Please check if the AI service is running.');
      console.error('Load analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatLatency = (ms: number) => {
    return `${ms.toFixed(0)}ms`;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            AI Usage Analytics
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Monitor AI provider usage, costs, and performance
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading analytics...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        ) : analytics ? (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Total Generations */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Generations
                    </p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                      {formatNumber(analytics.total_generations)}
                    </p>
                  </div>
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full">
                    <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
              </div>

              {/* Total Cost */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Total Cost
                    </p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                      {formatCost(analytics.total_cost)}
                    </p>
                  </div>
                  <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-full">
                    <DollarSign className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                </div>
              </div>

              {/* Average Quality */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Avg Quality Score
                    </p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                      {analytics.average_quality.toFixed(1)}
                    </p>
                  </div>
                  <div className="bg-yellow-100 dark:bg-yellow-900/30 p-3 rounded-full">
                    <Star className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                  </div>
                </div>
              </div>

              {/* Providers */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      Active Providers
                    </p>
                    <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                      {analytics.analytics.length}
                    </p>
                  </div>
                  <div className="bg-purple-100 dark:bg-purple-900/30 p-3 rounded-full">
                    <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                </div>
              </div>
            </div>

            {/* Provider Breakdown */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                  Provider Breakdown
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Provider
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Total Requests
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Success Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Total Tokens
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Avg Latency
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Est. Cost
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {analytics.analytics.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                          No usage data available yet. Start generating diagrams with AI!
                        </td>
                      </tr>
                    ) : (
                      analytics.analytics.map((provider) => {
                        const estimatedCost = (provider.total_tokens / 1000) * 0.002;
                        return (
                          <tr key={provider.provider} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="font-medium text-gray-900 dark:text-white capitalize">
                                {provider.provider.replace('_', ' ')}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                              {formatNumber(provider.total_requests)}
                              <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                                ({provider.successful_requests} success)
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                provider.success_rate >= 0.95
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                  : provider.success_rate >= 0.8
                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                              }`}>
                                {formatPercentage(provider.success_rate)}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                              {formatNumber(provider.total_tokens)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                              {formatLatency(provider.average_latency)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                              {formatCost(estimatedCost)}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Footer Note */}
            <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
              <p>
                Last updated: {new Date(analytics.timestamp).toLocaleString()}
              </p>
              <p className="mt-1">
                * Cost estimates are approximate and based on average pricing. Actual costs may vary by provider and model.
              </p>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
