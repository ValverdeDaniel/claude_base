import { Navigate } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';

function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useUser();

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default RequireAuth;
