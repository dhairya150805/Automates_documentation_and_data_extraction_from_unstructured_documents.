import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import API from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem("currentUserId")) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const submit = async () => {
    if (!email || !password) {
      alert("Email and password are required.");
      return;
    }
    setLoading(true);
    try {
      const res = await API.post("/auth/login", { email, password });
      sessionStorage.setItem("currentUserId", String(res.data.user_id));
      sessionStorage.setItem("currentUserName", res.data.name || "User");
      sessionStorage.setItem("currentUserEmail", res.data.email || email);
      sessionStorage.setItem("currentUserRole", res.data.role || "User");
      alert(`Welcome back, ${res.data.name}.`);
      navigate("/", { replace: true });
    } catch (error) {
      const msg = error?.response?.data?.detail || "Login failed.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Login</h1>
      <p className="subtle">Access your compliance workspace.</p>

      <div className="card" style={{ maxWidth: "520px" }}>
        <div style={{ marginTop: "6px" }}>
          <label className="subtle">Email</label>
          <input
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
        <div style={{ marginTop: "12px" }}>
          <label className="subtle">Password</label>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>
        <div style={{ marginTop: "16px" }} className="controls">
          <button className="button" onClick={submit} disabled={loading}>Login</button>
          <span className="subtle">
            New here? <Link to="/register">Create an account</Link>
          </span>
        </div>
      </div>
    </div>
  );
}
