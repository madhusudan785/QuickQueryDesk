/* Agent Dashboard - All Tickets with Search & Filters */

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ticketService } from '../services/tickets';
import type { TicketListItem } from '../types';
import { CATEGORIES, PRIORITIES } from '../types';
import { useWebSocket } from '../hooks/useWebSocket';
import {
  LayoutDashboard,
  Search,
  Filter,
  Clock,
  CheckCircle2,
  AlertCircle,
  Inbox,
  X,
  User,
} from 'lucide-react';

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

export default function AgentDashboard() {
  const [tickets, setTickets] = useState<TicketListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');

  const loadTickets = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (categoryFilter) params.category = categoryFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const data = await ticketService.getAllTickets(params);
      setTickets(data);
    } catch {
      setError('Failed to load tickets');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, categoryFilter, priorityFilter, searchQuery]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  // Live updates: when an employee submits a new ticket, refresh the list
  // so it appears without a manual page refresh. Re-fetching (rather than
  // splicing the event payload into local state) keeps this consistent
  // with whatever filters are currently active.
  useWebSocket('/ws/agent', useCallback((event) => {
    if (event === 'ticket_created' || event === 'ticket_ai_ready') {
      loadTickets();
    }
  }, [loadTickets]));

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('');
    setCategoryFilter('');
    setPriorityFilter('');
  };

  const hasActiveFilters = searchQuery || statusFilter || categoryFilter || priorityFilter;

  const openCount = tickets.filter((t) => t.status === 'open').length;
  const resolvedCount = tickets.filter((t) => t.status === 'resolved').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary-50 rounded-xl">
            <LayoutDashboard className="h-6 w-6 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-surface-900">Agent Dashboard</h1>
            <p className="text-surface-500 text-sm">Manage and resolve support tickets</p>
          </div>
        </div>
        {/* Stats */}
        <div className="hidden sm:flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg">
            <Clock className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-semibold text-amber-700">{openCount} Open</span>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <span className="text-sm font-semibold text-green-700">{resolvedCount} Resolved</span>
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-surface-200 shadow-sm p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex items-center flex-1 bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
            <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
              <Search className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search tickets by title..."
              className="w-full pr-4 py-2 bg-transparent text-surface-900 placeholder-surface-400 focus:outline-none border-none text-sm"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
            <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
              <Filter className="h-4 w-4" />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="pr-8 py-2 bg-transparent text-surface-700 text-sm focus:outline-none border-none appearance-none cursor-pointer"
            >
              <option value="">All Status</option>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-lg text-surface-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none cursor-pointer"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>

          {/* Priority Filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-lg text-surface-700 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none cursor-pointer"
          >
            <option value="">All Priorities</option>
            {PRIORITIES.map((pri) => (
              <option key={pri} value={pri}>{pri}</option>
            ))}
          </select>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 px-3 py-2.5 text-sm text-surface-500 hover:text-danger hover:bg-red-50 rounded-lg transition-all"
            >
              <X className="h-4 w-4" />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 border border-red-200 rounded-xl text-red-700">
          <AlertCircle className="h-5 w-5 shrink-0" />
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-surface-500">Loading tickets...</p>
        </div>
      ) : tickets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 bg-white rounded-2xl border border-surface-200">
          <div className="p-4 bg-surface-100 rounded-full mb-4">
            <Inbox className="h-10 w-10 text-surface-400" />
          </div>
          <h3 className="text-lg font-semibold text-surface-900 mb-1">
            {hasActiveFilters ? 'No matching tickets' : 'No tickets yet'}
          </h3>
          <p className="text-surface-500">
            {hasActiveFilters ? 'Try adjusting your filters' : 'Tickets will appear here when employees submit them'}
          </p>
          {hasActiveFilters && (
            <button onClick={clearFilters} className="mt-4 text-sm text-primary-600 hover:text-primary-700 font-medium">
              Clear filters
            </button>
          )}
        </div>
      ) : (
        /* Ticket Table */
        <div className="bg-white rounded-2xl border border-surface-200 shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="hidden sm:grid grid-cols-12 gap-4 px-5 py-3 bg-surface-50 border-b border-surface-200 text-xs font-semibold text-surface-500 uppercase tracking-wider">
            <div className="col-span-3">Title</div>
            <div className="col-span-2">Employee</div>
            <div className="col-span-2">Status</div>
            <div className="col-span-2">Category</div>
            <div className="col-span-1">Priority</div>
            <div className="col-span-2 text-right">Created</div>
          </div>

          {/* Table Body */}
          <div className="divide-y divide-surface-100">
            {tickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/agent/tickets/${ticket.id}`}
                className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:gap-4 px-5 py-4 hover:bg-surface-50 transition-colors group items-center"
              >
                {/* Title */}
                <div className="col-span-3 min-w-0">
                  <h3 className="text-sm font-semibold text-surface-900 group-hover:text-primary-600 transition-colors truncate">
                    {ticket.title}
                  </h3>
                </div>

                {/* Employee */}
                <div className="col-span-2 flex items-center gap-1.5 min-w-0">
                  <User className="h-3.5 w-3.5 text-surface-400 shrink-0" />
                  <span className="text-sm text-surface-600 truncate">{ticket.employee_name || 'Unknown'}</span>
                </div>

                {/* Status */}
                <div className="col-span-2">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${
                      ticket.status === 'open'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-green-50 text-green-700 border border-green-200'
                    }`}
                  >
                    {ticket.status === 'open' ? (
                      <Clock className="h-3 w-3 shrink-0" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3 shrink-0" />
                    )}
                    {ticket.status === 'open' ? 'Open' : 'Resolved'}
                  </span>
                </div>

                {/* Category */}
                <div className="col-span-2">
                  {ticket.current_category && (
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${categoryColors[ticket.current_category] || categoryColors.Other}`}>
                      {ticket.current_category}
                    </span>
                  )}
                </div>

                {/* Priority */}
                <div className="col-span-1">
                  {ticket.current_priority && (
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border whitespace-nowrap ${priorityColors[ticket.current_priority] || ''}`}>
                      {ticket.current_priority}
                    </span>
                  )}
                </div>

                {/* Created Date */}
                <div className="col-span-2 text-xs text-surface-400 sm:text-right whitespace-nowrap">
                  {new Date(ticket.created_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
