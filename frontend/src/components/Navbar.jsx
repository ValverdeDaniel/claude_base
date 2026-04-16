import { Link } from 'react-router-dom';
import { useUser } from '../contexts/UserContext';

function Navbar() {
  const { user, isAuthenticated, logout } = useUser();

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">Notes</Link>
      {isAuthenticated ? (
        <div className="navbar-user">
          <Link to="/admin">Admin</Link>
          <Link to="/profile">{user?.username}</Link>
          <button onClick={logout} className="btn btn-danger">
            Logout
          </button>
        </div>
      ) : (
        <div className="navbar-links">
          <Link to="/login">Log In</Link>
          <Link to="/signup">Sign Up</Link>
        </div>
      )}
    </nav>
  );
}

export default Navbar;
