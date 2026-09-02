/* Metrics Dashboard — Agent-only analytics page */

import { useState, useEffect } from 'react';
import { ticketService } from '../services/tickets';
import type { Metrics } from '../types';
import { CATEGORIES } from '../types';
import {
  BarChart3,
  TicketCheck,
  Clock,
  CheckCircle2,
  Brain,
  Timer,
  AlertCircle,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

const categoryColors: Record<string, string> = {
  IT: '#3b82f6',
  HR: '#8b5cf6',
  Finance: '#10b981',
  Admin: '#f97316',
  Other: '#64748b',
};

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        setIsLoading(true);
        setError('');
        const data = await ticketService.getMetrics();
        setMetrics(data);
      } catch {
        setError('Failed to load metrics');
      } finally {
        setIsLoading(false);
      }
    };
    loadMetrics();
  }, []);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mb-4"></div>
        <p className="text-surface-500">Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {error}
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  // Prepare chart data
  const categoryData = CATEGORIES.map((cat) => ({
    name: cat,
    count: metrics.category_distribution[cat] ?? 0,
    fill: categoryColors[cat] || categoryColors.Other,
  }));

  const statusData = [
    { name: 'Open', value: metrics.status_counts.open, fill: '#f59e0b' },
    { name: 'Resolved', value: metrics.status_counts.resolved, fill: '#10b981' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="p-2.5 bg-primary-50 rounded-xl">
          <BarChart3 className="h-6 w-6 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Metrics Dashboard</h1>
          <p className="text-surface-500 text-sm">Ticket analytics and AI performance</p>
        </div>
      </div>

      {/* Summary Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Total Tickets */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-primary-50 rounded-lg">
              <TicketCheck className="h-5 w-5 text-primary-600" />
            </div>
            <span className="text-sm font-medium text-surface-500">Total Tickets</span>
          </div>
          <p className="text-3xl font-bold text-surface-900">{metrics.total_tickets}</p>
        </div>

        {/* Open Tickets */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-amber-50 rounded-lg">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
            <span className="text-sm font-medium text-surface-500">Open</span>
          </div>
          <p className="text-3xl font-bold text-amber-600">{metrics.status_counts.open}</p>
        </div>

        {/* Resolved Tickets */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <span className="text-sm font-medium text-surface-500">Resolved</span>
          </div>
          <p className="text-3xl font-bold text-green-600">{metrics.status_counts.resolved}</p>
        </div>

        {/* Median Resolution Time */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-indigo-50 rounded-lg">
              <Timer className="h-5 w-5 text-indigo-600" />
            </div>
            <span className="text-sm font-medium text-surface-500">Median Resolution Time</span>
          </div>
          {metrics.median_resolution_hours !== null ? (
            <p className="text-3xl font-bold text-indigo-600">
              {metrics.median_resolution_hours}
              <span className="text-base font-medium text-surface-400 ml-1">hours</span>
            </p>
          ) : (
            <p className="text-sm text-surface-400 mt-1">No resolved tickets yet</p>
          )}
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Tickets by Category — Bar Chart */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-surface-900 mb-4">Tickets by Category</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fill: '#64748b', fontSize: 12 }}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                    fontSize: '13px',
                  }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={48}>
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Tickets by Status — Donut Chart */}
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-surface-900 mb-4">Tickets by Status</h2>
          <div className="h-64 flex items-center justify-center">
            {metrics.total_tickets > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e2e8f0',
                      borderRadius: '12px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                      fontSize: '13px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-surface-400 text-sm">No tickets yet</p>
            )}
          </div>
          {/* Legend */}
          <div className="flex items-center justify-center gap-6 mt-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-400"></div>
              <span className="text-sm text-surface-600">Open ({metrics.status_counts.open})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm text-surface-600">Resolved ({metrics.status_counts.resolved})</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Override Card */}
      <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-violet-50 rounded-lg">
            <Brain className="h-5 w-5 text-violet-600" />
          </div>
          <h2 className="text-lg font-semibold text-surface-900">AI Category Override Rate</h2>
        </div>
        <div className="flex items-baseline gap-3 mb-2">
          <p className="text-4xl font-bold text-violet-600">{metrics.ai_override_percentage}%</p>
          <span className="text-sm text-surface-400">
            ({metrics.total_overridden} of {metrics.total_classified} classified tickets)
          </span>
        </div>
        <p className="text-sm text-surface-500">
          Percentage of tickets where agents changed the AI-suggested category.
        </p>
      </div>
    </div>
  );
}
