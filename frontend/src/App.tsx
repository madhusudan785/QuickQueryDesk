/* Main application component with routing.
 *
 * NOTE: This is the Part 1 (auth) commit. Employee/agent dashboard,
 * ticket, and metrics pages are added in Part 2 — see the commented
 * routes below for what gets wired back in then.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';

// Part 2 imports (uncomment once these pages exist):
// import ProtectedRoute from './components/layout/ProtectedRoute';
// import EmployeeDashboard from './pages/EmployeeDashboard';
// import CreateTicket from './pages/CreateTicket';
// import EmployeeTicketDetail from './pages/EmployeeTicketDetail';
// import AgentDashboard from './pages/AgentDashboard';
// import AgentTicketDetail from './pages/AgentTicketDetail';
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

            {/* Part 2: Employee routes
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
            */}

            {/* Part 2: Agent routes
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
