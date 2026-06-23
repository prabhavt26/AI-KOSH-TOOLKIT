import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export const RegisterPage = ({ onRegisterSuccess, onSwitchToLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Dynamic Password Validation State
  const [checks, setChecks] = useState({
    length: false,
    upper: false,
    lower: false,
    number: false,
    special: false,
  });

  useEffect(() => {
    setChecks({
      length: password.length >= 8,
      upper: /[A-Z]/.test(password),
      lower: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[@$!%*?&]/.test(password),
    });
  }, [password]);

  const isPasswordValid = Object.values(checks).every(Boolean);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid) {
      setError('Password does not meet all complexity requirements.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);

    try {
      await apiClient.register(email, password);
      onRegisterSuccess();
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.message || 'Registration failed. User may already exist.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-card auth-card" style={{ maxWidth: '500px' }}>
        <div className="auth-header">
          <h2 className="auth-title">Create Account</h2>
          <p className="auth-subtitle">Register to begin scanning your dataset quality</p>
        </div>

        {error && (
          <div className="error-banner">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              className="input-field"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
            
            {/* Dynamic Password Validation UI */}
            {password.length > 0 && (
              <div className="password-requirements">
                <div className={`requirement-item ${checks.length ? 'valid' : 'invalid'}`}>
                  <span>{checks.length ? '✓' : '✗'}</span> At least 8 characters
                </div>
                <div className={`requirement-item ${checks.upper ? 'valid' : 'invalid'}`}>
                  <span>{checks.upper ? '✓' : '✗'}</span> One uppercase letter (A-Z)
                </div>
                <div className={`requirement-item ${checks.lower ? 'valid' : 'invalid'}`}>
                  <span>{checks.lower ? '✓' : '✗'}</span> One lowercase letter (a-z)
                </div>
                <div className={`requirement-item ${checks.number ? 'valid' : 'invalid'}`}>
                  <span>{checks.number ? '✓' : '✗'}</span> One numeric digit (0-9)
                </div>
                <div className={`requirement-item ${checks.special ? 'valid' : 'invalid'}`}>
                  <span>{checks.special ? '✓' : '✗'}</span> One special character (@, $, !, %, *, ?, &)
                </div>
              </div>
            )}
          </div>

          <div className="form-group" style={{ marginBottom: '2rem' }}>
            <label className="form-label" htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              className="input-field"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '0.8rem' }}
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? 
          <a href="#" className="auth-link" onClick={(e) => { e.preventDefault(); onSwitchToLogin(); }}>
            Sign in here
          </a>
        </div>
      </div>
    </div>
  );
};
