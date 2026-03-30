import React, { useEffect, useRef, useState } from "react";
import { BrowserRouter as Router, Routes, Route, NavLink, Navigate, useLocation, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Cases from "./pages/Cases";
import Dashboard from "./pages/Dashboard";
import ExtractedData from "./pages/ExtractedData";
import Compliance from "./pages/Compliance";
import Reports from "./pages/Reports";
import AuditLogs from "./pages/AuditLogs";
import Admin from "./pages/Admin";
import "./styles.css";

function RequireAuth({ children }) {
  const location = useLocation();
  const userId = sessionStorage.getItem("currentUserId");
  if (!userId) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

function RequireAdmin({ children }) {
  const location = useLocation();
  const userId = sessionStorage.getItem("currentUserId");
  const userRole = (sessionStorage.getItem("currentUserRole") || "").toLowerCase();

  if (!userId) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (userRole !== "admin") {
    return <Navigate to="/" replace />;
  }
  return children;
}

function AppLayout() {
  const navigate = useNavigate();
  const isAuthenticated = Boolean(sessionStorage.getItem("currentUserId"));
  const userName = sessionStorage.getItem("currentUserName") || "User";
  const userRole = sessionStorage.getItem("currentUserRole") || "User";
  const isAdmin = userRole.toLowerCase() === "admin";
  const userInitial = (userName.trim()[0] || "U").toUpperCase();
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef(null);

  useEffect(() => {
    // Clear old persistent auth keys from previous versions.
    localStorage.removeItem("currentUserId");
    localStorage.removeItem("currentCaseId");
    localStorage.removeItem("currentDocId");
    localStorage.removeItem("lastCompliance");
  }, []);

  useEffect(() => {
    if (!profileMenuOpen) return undefined;
    const onPointerDown = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setProfileMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [profileMenuOpen]);

  const logout = () => {
    setProfileMenuOpen(false);
    sessionStorage.removeItem("currentUserId");
    sessionStorage.removeItem("currentUserName");
    sessionStorage.removeItem("currentUserEmail");
    sessionStorage.removeItem("currentUserRole");
    sessionStorage.removeItem("currentCaseId");
    sessionStorage.removeItem("currentDocId");
    sessionStorage.removeItem("lastCompliance");
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">IDP + Compliance</div>
          <nav className="nav">
            {isAuthenticated && (
              <>
                <NavLink to="/" end>Dashboard</NavLink>
                <NavLink to="/cases">Cases</NavLink>
                <NavLink to="/extract">Extracted</NavLink>
                <NavLink to="/compliance">Compliance</NavLink>
                <NavLink to="/reports">Reports</NavLink>
                {isAdmin && <NavLink to="/admin">Admin</NavLink>}
                <div className="profile-menu" ref={profileMenuRef}>
                  <button
                    className="profile-trigger"
                    type="button"
                    onClick={() => setProfileMenuOpen((prev) => !prev)}
                    aria-haspopup="menu"
                    aria-expanded={profileMenuOpen}
                    title={userName}
                  >
                    {userInitial}
                  </button>
                  {profileMenuOpen && (
                    <div className="profile-dropdown" role="menu">
                      <div className="profile-user">{userName}</div>
                      <div className="subtle" style={{ padding: "0 12px 8px" }}>
                        Role: {userRole}
                      </div>
                      <button
                        className="profile-menu-item"
                        type="button"
                        onClick={() => {
                          setProfileMenuOpen(false);
                          navigate("/logs");
                        }}
                      >
                        Logs
                      </button>
                      <button className="profile-menu-item danger" type="button" onClick={logout}>
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
            {!isAuthenticated && (
              <>
                <NavLink to="/login">Login</NavLink>
                <NavLink to="/register">Sign Up</NavLink>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/cases" element={<RequireAuth><Cases /></RequireAuth>} />
          <Route path="/upload" element={<Navigate to={{ pathname: "/cases", hash: "#upload" }} replace />} />
          <Route path="/review" element={<Navigate to={{ pathname: "/cases", hash: "#review" }} replace />} />
          <Route path="/extract" element={<RequireAuth><ExtractedData /></RequireAuth>} />
          <Route path="/compliance" element={<RequireAuth><Compliance /></RequireAuth>} />
          <Route path="/reports" element={<RequireAuth><Reports /></RequireAuth>} />
          <Route path="/admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          <Route path="/logs" element={<RequireAuth><AuditLogs /></RequireAuth>} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}
