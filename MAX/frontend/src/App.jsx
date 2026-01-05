import { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import keycloak from './lib/keycloak';
import { useAuthStore } from './store';
import apiClient from './services/api';

// Pages
import LoginPage from './pages/LoginPage';
import InboxPage from './pages/InboxPage';
import LoadingPage from './pages/LoadingPage';

function App() {
  const { setUser, clearUser, setLoading, isAuthenticated, isLoading } = useAuthStore();
  const [keycloakReady, setKeycloakReady] = useState(false);

  useEffect(() => {
    // Initialize Keycloak
    keycloak
      .init({
        onLoad: 'check-sso',
        checkLoginIframe: false,
      })
      .then(async (authenticated) => {
        setKeycloakReady(true);

        if (authenticated) {
          try {
            // Get user info from backend
            const response = await apiClient.get('/api/v1/auth/me');
            setUser(response.data);
          } catch (error) {
            console.error('Error fetching user info:', error);
            clearUser();
          }
        } else {
          setLoading(false);
        }
      })
      .catch((error) => {
        console.error('Keycloak init error:', error);
        setLoading(false);
      });

    // Token refresh
    const interval = setInterval(() => {
      keycloak.updateToken(70).catch(() => {
        console.error('Failed to refresh token');
        keycloak.login();
      });
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [setUser, clearUser, setLoading]);

  if (!keycloakReady || isLoading) {
    return <LoadingPage />;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />}
      />
      <Route
        path="/*"
        element={isAuthenticated ? <InboxPage /> : <Navigate to="/login" />}
      />
    </Routes>
  );
}

export default App;
