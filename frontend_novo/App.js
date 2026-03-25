"import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Toaster } from './components/ui/sonner';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import '@/App.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-primary\"></div>
      </div>
    );
  }

  return user ? children : <Navigate to=\"/\" />;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-primary\"></div>
      </div>
    );
  }

  return !user ? children : <Navigate to=\"/dashboard\" />;
};

function AppRoutes() {
  return (
    <Routes>
      <Route
        path=\"/\"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path=\"/dashboard\"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route path=\"*\" element={<Navigate to=\"/\" />} />
    </Routes>
  );
}

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <Toaster position=\"top-right\" richColors />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
"