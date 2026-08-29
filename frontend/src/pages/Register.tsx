/* Register page */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { TicketCheck, Mail, Lock, User, ArrowRight, AlertCircle } from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'employee' | 'agent'>('employee');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await register(name, email, password, role);
      navigate(role === 'agent' ? '/agent/dashboard' : '/dashboard');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Registration failed');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-surface-900 via-surface-800 to-primary-950 flex flex-col justify-center items-center py-10 px-4 sm:px-6 relative overflow-y-auto">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary-500/10 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary-400/10 blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md my-auto">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/25 mb-3">
            <TicketCheck className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">QuickQueryDesk</h1>
          <p className="text-surface-400 mt-1 text-sm">Create your account</p>
        </div>

        <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 sm:p-8 border border-white/20">
          <h2 className="text-2xl font-bold text-surface-900 mb-1">Get started</h2>
          <p className="text-surface-500 text-sm mb-6">Register a new account</p>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-surface-700 mb-1">
                Full Name
              </label>
              <div className="flex items-center w-full bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
                <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
                  <User className="h-4 w-4" />
                </div>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pr-4 py-2 bg-transparent text-surface-900 placeholder-surface-400 focus:outline-none border-none text-sm"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-surface-700 mb-1">
                Email
              </label>
              <div className="flex items-center w-full bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
                <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
                  <Mail className="h-4 w-4" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pr-4 py-2 bg-transparent text-surface-900 placeholder-surface-400 focus:outline-none border-none text-sm"
                  placeholder="you@company.com"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-surface-700 mb-1">
                Password
              </label>
              <div className="flex items-center w-full bg-surface-50 border border-surface-200 rounded-lg focus-within:ring-2 focus-within:ring-primary-500 focus-within:border-transparent transition-all">
                <div className="pl-3 pr-2 flex items-center justify-center text-surface-400 shrink-0 pointer-events-none">
                  <Lock className="h-4 w-4" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pr-4 py-2 bg-transparent text-surface-900 placeholder-surface-400 focus:outline-none border-none text-sm"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>
              <p className="text-xs text-surface-400 mt-1">Minimum 6 characters</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-surface-700 mb-2">Select Role</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRole('employee')}
                  className={`p-3 rounded-xl border-2 flex flex-col items-center justify-center min-h-[72px] transition-all duration-200 ${
                    role === 'employee'
                      ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                      : 'border-surface-200 bg-white text-surface-600 hover:border-surface-300'
                  }`}
                >
                  <span className="text-sm font-semibold">Employee</span>
                  <span className="text-[11px] opacity-80 mt-0.5 whitespace-nowrap">Submit tickets</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('agent')}
                  className={`p-3 rounded-xl border-2 flex flex-col items-center justify-center min-h-[72px] transition-all duration-200 ${
                    role === 'agent'
                      ? 'border-primary-500 bg-primary-50 text-primary-700 shadow-sm'
                      : 'border-surface-200 bg-white text-surface-600 hover:border-surface-300'
                  }`}
                >
                  <span className="text-sm font-semibold">Agent</span>
                  <span className="text-[11px] opacity-80 mt-0.5 whitespace-nowrap">Resolve tickets</span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 disabled:opacity-50 disabled:cursor-not-allowed text-sm mt-2"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Create Account
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-surface-500">
              Already have an account?{' '}
              <Link to="/login" className="text-primary-600 hover:text-primary-700 font-semibold">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
