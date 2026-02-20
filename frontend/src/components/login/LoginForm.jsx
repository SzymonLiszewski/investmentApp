import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';
import './AuthForm.css';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const loginUser = async (username, password) => {
    setError('');
    setSuccess('');
    try {
      const response = await fetch('api/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          password,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.username || data.detail || 'Invalid username or password');
      }
      setSuccess('Login successful');
      login();
      navigate('/');
      return data;
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await loginUser(username, password);
    if (result) {
      localStorage.setItem('access', result.access);
      localStorage.setItem('refresh', result.refresh);
    }
  };

  return (
    <div className="auth-card">
      <h1 className="auth-title">Login</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}
        {success && (
          <div className="auth-success" role="status">
            {success}
          </div>
        )}
        <input
          className="auth-input"
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          className="auth-input"
          placeholder="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" className="auth-button">
          Login
        </button>
      </form>
    </div>
  );
};

export default LoginForm;
