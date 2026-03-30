import React, { useEffect, useState } from "react";
import API from "../services/api";

export default function Dashboard() {
  const [stats, setStats] = useState({ total_docs: 0, pass: 0, fail: 0, warning: 0, cases: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const res = await API.get("/stats");
        setStats(res.data);
      } catch (error) {
        console.error("Failed to load stats:", error);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  const statCards = [
    { 
      title: "Total Documents", 
      value: stats.total_docs, 
      icon: "📄",
      color: "primary" 
    },
    { 
      title: "Compliant", 
      value: stats.pass, 
      icon: "✅", 
      color: "success" 
    },
    { 
      title: "Failed", 
      value: stats.fail, 
      icon: "❌", 
      color: "danger" 
    },
    { 
      title: "Warnings", 
      value: stats.warning, 
      icon: "⚠️", 
      color: "warning" 
    },
    { 
      title: "Total Cases", 
      value: stats.cases, 
      icon: "📁", 
      color: "secondary" 
    }
  ];

  if (loading) {
    return (
      <div className="fade-in">
        <h1 className="page-title">Dashboard</h1>
        <div className="card">
          <div className="loading" style={{ height: "200px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            Loading dashboard data...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div style={{ marginBottom: "32px" }}>
        <h1 className="page-title">AI Document Processing Dashboard</h1>
        <p className="subtle">
          Monitor your document processing pipeline, compliance status, and system health in real-time.
        </p>
      </div>

      {/* Key Metrics */}
      <div className="card" style={{ marginBottom: "32px" }}>
        <h3 style={{ marginBottom: "24px", fontSize: "20px", fontWeight: "600" }}>
          📊 Key Metrics
        </h3>
        <div className="grid">
          {statCards.map((stat, index) => (
            <div key={stat.title} className="col-3">
              <div className={`stat ${stat.color}`} style={{ animationDelay: `${index * 100}ms` }}>
                <div style={{ fontSize: "24px", marginBottom: "8px" }}>{stat.icon}</div>
                <h3>{stat.title}</h3>
                <div className="value">{stat.value.toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", gap: "24px" }}>
        <div className="card">
          <h3 style={{ marginBottom: "20px", fontSize: "18px", fontWeight: "600" }}>
            🔍 Processing Overview
          </h3>
          
          <div style={{ marginBottom: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
              <span style={{ fontSize: "14px", color: "var(--gray-600)" }}>Compliance Rate</span>
              <span style={{ fontSize: "14px", fontWeight: "600" }}>
                {stats.total_docs > 0 ? Math.round((stats.pass / stats.total_docs) * 100) : 0}%
              </span>
            </div>
            <div className="progress">
              <div 
                className="progress-bar" 
                style={{ 
                  width: stats.total_docs > 0 ? `${(stats.pass / stats.total_docs) * 100}%` : "0%",
                  background: "var(--success)"
                }}
              ></div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
            <div style={{ textAlign: "center", padding: "16px", background: "var(--gray-50)", borderRadius: "8px" }}>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--success)" }}>
                {stats.pass}
              </div>
              <div style={{ fontSize: "12px", color: "var(--gray-600)", textTransform: "uppercase" }}>
                Passed
              </div>
            </div>
            <div style={{ textAlign: "center", padding: "16px", background: "var(--gray-50)", borderRadius: "8px" }}>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--warning)" }}>
                {stats.warning}
              </div>
              <div style={{ fontSize: "12px", color: "var(--gray-600)", textTransform: "uppercase" }}>
                Warnings
              </div>
            </div>
            <div style={{ textAlign: "center", padding: "16px", background: "var(--gray-50)", borderRadius: "8px" }}>
              <div style={{ fontSize: "24px", fontWeight: "700", color: "var(--danger)" }}>
                {stats.fail}
              </div>
              <div style={{ fontSize: "12px", color: "var(--gray-600)", textTransform: "uppercase" }}>
                Failed
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: "20px", fontSize: "18px", fontWeight: "600" }}>
            🚀 Quick Actions
          </h3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <button 
              className="button" 
              onClick={() => window.location.href = "/cases"}
              style={{ justifyContent: "flex-start" }}
            >
              <span style={{ fontSize: "16px" }}>📁</span>
              Create New Case
            </button>
            
            <button 
              className="button secondary" 
              onClick={() => window.location.href = "/cases#upload"}
              style={{ justifyContent: "flex-start" }}
            >
              <span style={{ fontSize: "16px" }}>📤</span>
              Upload Documents
            </button>
            
            <button 
              className="button secondary" 
              onClick={() => window.location.href = "/cases#review"}
              style={{ justifyContent: "flex-start" }}
            >
              <span style={{ fontSize: "16px" }}>👥</span>
              Review Data
            </button>
            
            <button 
              className="button secondary" 
              onClick={() => window.location.href = "/reports"}
              style={{ justifyContent: "flex-start" }}
            >
              <span style={{ fontSize: "16px" }}>📊</span>
              Generate Reports
            </button>
          </div>
        </div>
      </div>

      {/* System Info */}
      <div className="card" style={{ marginTop: "24px" }}>
        <h3 style={{ marginBottom: "16px", fontSize: "18px", fontWeight: "600" }}>
          ℹ️ System Information
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", fontSize: "14px" }}>
          <div>
            <div style={{ color: "var(--gray-600)", marginBottom: "4px" }}>System Status</div>
            <div style={{ fontWeight: "600", color: "var(--success)" }}>🟢 Online</div>
          </div>
          <div>
            <div style={{ color: "var(--gray-600)", marginBottom: "4px" }}>AI Models</div>
            <div style={{ fontWeight: "600" }}>OCR, LayoutLM, Summarization</div>
          </div>
          <div>
            <div style={{ color: "var(--gray-600)", marginBottom: "4px" }}>Supported Formats</div>
            <div style={{ fontWeight: "600" }}>PDF, Images, DOCX, Audio</div>
          </div>
          <div>
            <div style={{ color: "var(--gray-600)", marginBottom: "4px" }}>Last Updated</div>
            <div style={{ fontWeight: "600" }}>{new Date().toLocaleString()}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
