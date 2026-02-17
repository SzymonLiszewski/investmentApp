import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './AuthForm.css';

const MIN_PASSWORD_LENGTH = 8;

const getPasswordError = (value) => {
  if (value.length < MIN_PASSWORD_LENGTH) {
    return `At least ${MIN_PASSWORD_LENGTH} characters`;
  }
  if (!/[A-Z]/.test(value)) {
    return 'At least one uppercase letter';
  }
  if (!/[a-z]/.test(value)) {
    return 'At least one lowercase letter';
  }
  if (!/\d/.test(value)) {
    return 'At least one digit';
  }
  return null;
};

const RegisterForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const registerUser = async (username, password) => {
    const response = await fetch('api/user/register/', {
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
      const msg =
        (Array.isArray(data.password) ? data.password[0] : null) ||
        (Array.isArray(data.username) ? data.username[0] : null) ||
        data.username ||
        data.detail ||
        'Registration failed';
      throw new Error(msg);
    }
    return data;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    const passwordErr = getPasswordError(password);
    if (passwordErr) {
      setError(`Password: ${passwordErr}`);
      return;
    }
    try {
      await registerUser(username, password);
      alert('Register successful');
      navigate('/login');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-card">
      <h1 className="auth-title">Register</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}
        <input
          className="auth-input"
          placeholder="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <div>
          <input
            type="password"
            className="auth-input"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <p className="auth-hint">
            Min {MIN_PASSWORD_LENGTH} characters, one uppercase, one lowercase, one digit
          </p>
        </div>
        <input
          type="password"
          className="auth-input"
          placeholder="confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
        <button type="submit" className="auth-button">
          Register
        </button>
      </form>
    </div>
  );
};

export default RegisterForm;
