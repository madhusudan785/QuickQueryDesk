/* Employee Dashboard - My Tickets */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ticketService } from '../services/tickets';
import type { TicketListItem } from '../types';
import { useAuth } from '../hooks/useAuth';
import { Ticket, Clock, CheckCircle2, AlertCircle, Plus, Inbox } from 'lucide-react';

const priorityColors: Record<string, string> = {
  High: 'bg-red-100 text-red-700 border-red-200',
  Medium: 'bg-amber-100 text-amber-700 border-amber-200',
  Low: 'bg-green-100 text-green-700 border-green-200',
};

const categoryColors: Record<string, string> = {
  IT: 'bg-blue-100 text-blue-700',
  HR: 'bg-purple-100 text-purple-700',
  Finance: 'bg-emerald-100 text-emerald-700',
  Admin: 'bg-orange-100 text-orange-700',
  Other: 'bg-surface-100 text-surface-700',
};

export default function EmployeeDashboard() {
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    loadTickets();
  }, []);

  const loadTickets = async () => {
    try {
      setIsLoading(true);
      const data = await ticketService.getMyTickets();
      setTickets(data);
    } catch {
      setError('Failed to load tickets');
    } finally {
      setIsLoading(false);
    }
  };

  const openCount = tickets.filter((t) => t.status === 'open').length;
  const resolvedCount = tickets.filter((t) => t.status === 'resolved').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">
            Welcome back, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-surface-500 mt-1">Track and manage your support requests</p>
        </div>
        <Link
          to="/tickets/new"
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40"
        >
          <Plus className="h-4 w-4" />
          New Ticket
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary-50 rounded-lg">
              <Ticket className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-surface-900">{tickets.length}</p>
              <p className="text-sm text-surface-500">Total Tickets</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-50 rounded-lg">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-surface-900">{openCount}</p>
              <p className="text-sm text-surface-500">Open</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-50 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-surface-900">{resolvedCount}</p>
              <p className="text-sm text-surface-500">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-surface-500">Loading your tickets...</p>
        </div>
      ) : tickets.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-surface-200">
          <div className="p-4 bg-surface-100 rounded-full mb-4">
            <Inbox className="h-10 w-10 text-surface-400" />
          </div>
          <h3 className="text-lg font-semibold text-surface-900 mb-1">No tickets yet</h3>
          <p className="text-surface-500 mb-6">Submit your first support request to get started</p>
          <Link
            to="/tickets/new"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Ticket
          </Link>
        </div>
      ) : (
        /* Ticket List */
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm overflow-hidden">
          <div className="divide-y divide-surface-100">
            {tickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/tickets/${ticket.id}`}
                className="flex items-center justify-between p-5 hover:bg-surface-50 transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-sm font-semibold text-surface-900 truncate group-hover:text-primary-600 transition-colors">
                      {ticket.title}
                    </h3>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
                        ticket.status === 'open'
                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                          : 'bg-green-50 text-green-700 border-green-200'
                      }`}
                    >
                      {ticket.status === 'open' ? (
                        <Clock className="h-3 w-3 mr-1" />
                      ) : (
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                      )}
                      {ticket.status.charAt(0).toUpperCase() + ticket.status.slice(1)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-surface-500 flex-wrap">
                    {ticket.current_category && (
                      <span className={`px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${categoryColors[ticket.current_category] || categoryColors.Other}`}>
                        {ticket.current_category}
                      </span>
                    )}
                    {ticket.current_priority && (
                      <span className={`px-2 py-0.5 rounded-full font-medium border whitespace-nowrap ${priorityColors[ticket.current_priority] || ''}`}>
                        {ticket.current_priority}
                      </span>
                    )}
                    <span className="text-surface-400 whitespace-nowrap">
                      Created {new Date(ticket.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <svg className="h-5 w-5 text-surface-400 group-hover:text-primary-500 transition-colors shrink-0 ml-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
