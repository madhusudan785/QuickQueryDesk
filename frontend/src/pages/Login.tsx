/* Login page */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { TicketCheck, Mail, Lock, ArrowRight, AlertCircle } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      // Navigate based on role from stored user
      const stored = localStorage.getItem('user');
      if (stored) {
        const user = JSON.parse(stored);
        navigate(user.role === 'agent' ? '/agent/dashboard' : '/dashboard');
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Login failed');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-surface-900 via-surface-800 to-primary-950 flex flex-col justify-center items-center py-10 px-4 sm:px-6 relative overflow-y-auto">
      {/* Background decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary-500/10 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary-400/10 blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md my-auto">
        {/* Logo */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/25 mb-3">
            <TicketCheck className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">QuickQueryDesk</h1>
          <p className="text-surface-400 mt-1 text-sm">AI-Powered Helpdesk System</p>
        </div>

        {/* Login Card */}
        <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 sm:p-8 border border-white/20">
          <h2 className="text-2xl font-bold text-surface-900 mb-1">Welcome back</h2>
          <p className="text-surface-500 text-sm mb-6">Sign in to your account</p>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
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
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-medium rounded-lg transition-all duration-200 shadow-lg shadow-primary-500/25 hover:shadow-primary-500/40 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-surface-500">
              Don't have an account?{' '}
              <Link to="/register" className="text-primary-600 hover:text-primary-700 font-semibold">
                Register here
              </Link>
            </p>
          </div>
        </div>

        {/* Demo credentials */}
        <div className="mt-5 p-4 bg-slate-900/80 backdrop-blur-md rounded-xl border border-white/10 shadow-lg space-y-2">
          <p className="text-xs font-semibold text-surface-300 text-center tracking-wider uppercase">
            Demo Login Credentials
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="bg-white/5 p-2 rounded-lg border border-white/5 text-center">
              <span className="text-primary-400 font-semibold block">Agent</span>
              <code className="text-slate-200 select-all font-mono text-[11px]">agent@example.com</code>
              <span className="text-slate-400 block text-[10px] mt-0.5">pass: agent123</span>
            </div>
            <div className="bg-white/5 p-2 rounded-lg border border-white/5 text-center">
              <span className="text-primary-400 font-semibold block">Employee</span>
              <code className="text-slate-200 select-all font-mono text-[11px]">employee@example.com</code>
              <span className="text-slate-400 block text-[10px] mt-0.5">pass: employee123</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
