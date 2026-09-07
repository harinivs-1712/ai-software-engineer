import React, { useState, useEffect } from "react";
import ChatPage from "./pages/ChatPage";
import AuthPage from "./pages/AuthPage";
import { getCurrentUser } from "./services/api";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (err) {
        console.error("Failed to authenticate session:", err);
        localStorage.removeItem("access_token");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          width: "100vw",
          backgroundColor: "#030712",
          color: "#9ca3af",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div className="btn-spinner" style={{ width: 36, height: 36, margin: "0 auto 12px" }}></div>
          <p>Loading application...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuthSuccess={(userData) => setUser(userData)} />;
  }

  return <ChatPage user={user} onLogout={handleLogout} />;
}

export default App;
