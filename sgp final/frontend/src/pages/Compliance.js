import React, { useState } from "react";
import API from "../services/api";
import StatusBadge from "../components/StatusBadge";

const defaultRules = {
  required_fields: ["Invoice No", "Date", "Amount"],
  patterns: { Date: "^\\d{2}/\\d{2}/\\d{4}$" },
  value_constraints: { Amount: { min: 1, max: 100000 } }
};

export default function Compliance() {
  const [docId, setDocId] = useState(sessionStorage.getItem("currentDocId") || "");
  const [rulesText, setRulesText] = useState(JSON.stringify(defaultRules, null, 2));
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const showError = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message || fallback;
    alert(message);
  };

  const runCompliance = async () => {
    if (!docId) {
      alert("Please enter a Document ID.");
      return;
    }
    sessionStorage.setItem("currentDocId", docId);
    let rulesObj;
    try {
      rulesObj = JSON.parse(rulesText);
    } catch (e) {
      alert("Rules JSON is invalid.");
      return;
    }
    setLoading(true);
    try {
      const res = await API.post(`/compliance?doc_id=${docId}`, rulesObj);
      setResult(res.data.compliance);
      sessionStorage.setItem("lastCompliance", JSON.stringify(res.data.compliance));
    } catch (error) {
      showError(error, "Compliance check failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Compliance Center</h1>
      <p className="subtle">Apply deterministic rules and capture audit-ready decisions.</p>

      <div className="card">
        <div className="controls">
          <input
            className="input"
            type="number"
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="Document ID"
          />
          <button className="button" onClick={runCompliance} disabled={loading}>Run Compliance</button>
        </div>
      </div>

      <div className="grid" style={{ marginTop: "16px" }}>
        <div className="col-8">
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Rules (JSON)</h3>
            <textarea
              className="textarea"
              rows="12"
              value={rulesText}
              onChange={(e) => setRulesText(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>
        </div>
        <div className="col-4">
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Result</h3>
            {result ? (
              <div>
                <StatusBadge status={result.status} />
                <div className="muted-box" style={{ marginTop: "10px" }}>
                  {result.remarks}
                </div>
              </div>
            ) : (
              <p className="subtle">No compliance run yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
