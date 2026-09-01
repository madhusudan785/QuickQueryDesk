/* Main application component with routing.
 *
 * NOTE: This is the Part 3 (agent dashboard + overrides + WebSocket real-time updates)
 * commit. Employee and agent routes are both active. The metrics dashboard is
 * added in a later commit — see the commented route below.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import ProtectedRoute from './components/layout/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import EmployeeDashboard from './pages/EmployeeDashboard';
import CreateTicket from './pages/CreateTicket';
import EmployeeTicketDetail from './pages/EmployeeTicketDetail';
import AgentDashboard from './pages/AgentDashboard';
import AgentTicketDetail from './pages/AgentTicketDetail';

// Part 4 import (uncomment once this page exists):
// import MetricsDashboard from './pages/MetricsDashboard';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-surface-50">
          <Navbar />
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Employee routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute requiredRole="employee">
                  <EmployeeDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tickets/new"
              element={
                <ProtectedRoute requiredRole="employee">
                  <CreateTicket />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tickets/:id"
              element={
                <ProtectedRoute requiredRole="employee">
                  <EmployeeTicketDetail />
                </ProtectedRoute>
              }
            />

            {/* Agent routes */}
            <Route
              path="/agent/dashboard"
              element={
                <ProtectedRoute requiredRole="agent">
                  <AgentDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/agent/tickets/:id"
              element={
                <ProtectedRoute requiredRole="agent">
                  <AgentTicketDetail />
                </ProtectedRoute>
              }
            />

            {/* Part 4: Metrics route
            <Route
              path="/agent/metrics"
              element={
                <ProtectedRoute requiredRole="agent">
                  <MetricsDashboard />
                </ProtectedRoute>
              }
            />
            */}

            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
