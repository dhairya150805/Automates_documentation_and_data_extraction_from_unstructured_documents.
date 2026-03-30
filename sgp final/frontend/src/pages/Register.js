import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import API from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("User");
  const [adminKey, setAdminKey] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (sessionStorage.getItem("currentUserId")) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const submit = async () => {
    if (!name || !email || !password) {
      alert("Name, email, and password are required.");
      return;
    }
    if (role === "Admin" && !adminKey.trim()) {
      alert("Admin key is required to create an admin account.");
      return;
    }
    setLoading(true);
    try {
      const payload = { name, email, role, password };
      if (role === "Admin") {
        payload.admin_key = adminKey.trim();
      }
      const res = await API.post("/auth/register", payload);
      sessionStorage.setItem("currentUserId", String(res.data.user_id));
      sessionStorage.setItem("currentUserName", res.data.name || name);
      sessionStorage.setItem("currentUserEmail", res.data.email || email);
      sessionStorage.setItem("currentUserRole", res.data.role || role);
      alert(`Registered: ${res.data.name}`);
      navigate("/", { replace: true });
    } catch (error) {
      const msg = error?.response?.data?.detail || "Registration failed.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Register</h1>
      <p className="subtle">Create a user profile for audit tracking.</p>

      <div className="card" style={{ maxWidth: "560px" }}>
        <div style={{ marginTop: "6px" }}>
          <label className="subtle">Full Name</label>
          <input
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Doe"
          />
        </div>
        <div style={{ marginTop: "12px" }}>
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
            placeholder="Create a strong password"
          />
        </div>
        <div style={{ marginTop: "12px" }}>
          <label className="subtle">Role</label>
          <select className="select" value={role} onChange={(e) => setRole(e.target.value)}>
            <option>Admin</option>
            <option>User</option>
          </select>
        </div>
        {role === "Admin" && (
          <div style={{ marginTop: "12px" }}>
            <label className="subtle">Admin Key</label>
            <input
              className="input"
              type="password"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Enter admin setup key"
            />
          </div>
        )}
        <div style={{ marginTop: "16px" }} className="controls">
          <button className="button" onClick={submit} disabled={loading}>Create Account</button>
          <span className="subtle">
            Already registered? <Link to="/login">Login</Link>
          </span>
        </div>
      </div>
    </div>
  );
}
