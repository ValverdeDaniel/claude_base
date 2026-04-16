import { useState } from 'react';
import { Link } from 'react-router-dom';
import { requestPasswordReset } from '../services/api';

function RequestPasswordReset() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
    } catch {
      setError('Something went wrong. Please try again.');
    }
  }

  if (submitted) {
    return (
      <div className="card">
        <h2>Check Your Email</h2>
        <div className="success-message">
          If an account with that email exists, we've sent a password reset link.
        </div>
        <div className="form-footer">
          <Link to="/login">Back to login</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Reset Password</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">Send Reset Link</button>
      </form>
      <div className="form-footer">
        <Link to="/login">Back to login</Link>
      </div>
    </div>
  );
}

export default RequestPasswordReset;
