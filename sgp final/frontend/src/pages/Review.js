import React, { useState } from "react";
import API from "../services/api";

const emptyRow = () => ({ field: "", value: "", confidence: 0.5 });

export default function Review() {
  const [caseId, setCaseId] = useState(sessionStorage.getItem("currentCaseId") || "");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadSummary = async () => {
    if (!caseId) {
      alert("Enter a Case ID.");
      return;
    }
    setLoading(true);
    try {
      const res = await API.get(`/cases/${caseId}/summary`);
      setSummary(res.data);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to load case summary.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const updateField = (docIndex, rowIndex, key, value) => {
    setSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.evidence = [...prev.evidence];
      const doc = { ...next.evidence[docIndex] };
      const extracted = [...doc.extracted_data];
      extracted[rowIndex] = { ...extracted[rowIndex], [key]: value };
      doc.extracted_data = extracted;
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const addRow = (docIndex) => {
    setSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.evidence = [...prev.evidence];
      const doc = { ...next.evidence[docIndex] };
      doc.extracted_data = [...doc.extracted_data, emptyRow()];
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const removeRow = (docIndex, rowIndex) => {
    setSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev };
      next.evidence = [...prev.evidence];
      const doc = { ...next.evidence[docIndex] };
      doc.extracted_data = doc.extracted_data.filter((_, idx) => idx !== rowIndex);
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const saveDoc = async (doc) => {
    setLoading(true);
    try {
      await API.put(`/extract?doc_id=${doc.doc_id}`, {
        extracted_data: doc.extracted_data.map((row) => ({
          field: row.field,
          value: row.value,
          confidence: Number(row.confidence) || 0,
        })),
      });
      alert(`Saved corrections for document ${doc.doc_id}.`);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to save corrections.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Human Review</h1>
      <p className="subtle">Review and correct extracted fields before final reporting.</p>

      <div className="card">
        <div className="controls">
          <input
            className="input"
            type="number"
            value={caseId}
            onChange={(e) => {
              const value = e.target.value;
              setCaseId(value);
              sessionStorage.setItem("currentCaseId", value);
            }}
            placeholder="Case ID"
          />
          <button className="button" onClick={loadSummary} disabled={loading}>Load Case</button>
        </div>
      </div>

      {summary && summary.evidence.map((doc, docIndex) => (
        <div className="card" style={{ marginTop: "18px" }} key={doc.doc_id}>
          <div className="controls" style={{ justifyContent: "space-between", width: "100%" }}>
            <div>
              <strong>Doc {doc.doc_id}</strong> — {doc.filename} ({doc.file_type || "unknown"})
            </div>
            <div className="controls">
              <button className="button secondary" onClick={() => addRow(docIndex)}>Add Field</button>
              <button className="button" onClick={() => saveDoc(doc)} disabled={loading}>Save</button>
            </div>
          </div>

          <table className="table" style={{ marginTop: "12px" }}>
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {doc.extracted_data.length === 0 && (
                <tr>
                  <td colSpan="4">No extracted data.</td>
                </tr>
              )}
              {doc.extracted_data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  <td>
                    <input
                      className="input"
                      value={row.field}
                      onChange={(e) => updateField(docIndex, rowIndex, "field", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="input"
                      value={row.value}
                      onChange={(e) => updateField(docIndex, rowIndex, "value", e.target.value)}
                    />
                  </td>
                  <td style={{ maxWidth: "140px" }}>
                    <input
                      className="input"
                      type="number"
                      step="0.01"
                      value={row.confidence}
                      onChange={(e) => updateField(docIndex, rowIndex, "confidence", e.target.value)}
                    />
                  </td>
                  <td>
                    <button className="button secondary" onClick={() => removeRow(docIndex, rowIndex)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
