import React, { useState } from "react";
import { loginUser, registerUser } from "../services/api";

export default function AuthPage({ onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      if (isRegister) {
        // Register then automatically log in
        await registerUser(email, password);
        const loginRes = await loginUser(email, password);
        if (loginRes.access_token) {
          localStorage.setItem("access_token", loginRes.access_token);
          onAuthSuccess(loginRes.user);
        }
      } else {
        const loginRes = await loginUser(email, password);
        if (loginRes.access_token) {
          localStorage.setItem("access_token", loginRes.access_token);
          onAuthSuccess(loginRes.user);
        }
      }
    } catch (err) {
      setError(err.message || "An error occurred during authentication.");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setError(null);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <svg
              className="logo-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          </div>
          <h1 className="auth-title">AI Software Engineer</h1>
          <p className="auth-subtitle">
            {isRegister
              ? "Create your account to start building"
              : "Welcome back! Sign in to continue"}
          </p>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${!isRegister ? "active" : ""}`}
            onClick={() => {
              if (isRegister) toggleMode();
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${isRegister ? "active" : ""}`}
            onClick={() => {
              if (!isRegister) toggleMode();
            }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="auth-error-banner">
            <svg
              className="error-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-wrapper">
              <input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <div className="input-wrapper">
                <input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? (
              <span className="btn-spinner"></span>
            ) : isRegister ? (
              "Create Account"
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {isRegister
              ? "Already have an account?"
              : "Don't have an account?"}{" "}
            <button
              type="button"
              className="toggle-btn"
              onClick={toggleMode}
            >
              {isRegister ? "Sign In" : "Register now"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
