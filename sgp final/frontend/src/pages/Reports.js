import React, { useState } from "react";
import API from "../services/api";

export default function Reports() {
  const [docId, setDocId] = useState(sessionStorage.getItem("currentDocId") || "");
  const [loading, setLoading] = useState(false);

  const showError = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message || fallback;
    alert(message);
  };

  const downloadReport = async (format) => {
    if (!docId) {
      alert("Please enter a Document ID.");
      return;
    }
    sessionStorage.setItem("currentDocId", docId);
    setLoading(true);
    try {
      const res = await API.get(`/reports?doc_id=${docId}&format=${format}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `report_${docId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      showError(error, "Report download failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Reports Download</h1>
      <p className="subtle">Export compliance results and extracted fields for audit and review.</p>

      <div className="card">
        <div className="controls">
          <input
            className="input"
            type="number"
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="Document ID"
          />
          <button className="button" onClick={() => downloadReport("csv")} disabled={loading}>Download CSV</button>
          <button className="button secondary" onClick={() => downloadReport("pdf")} disabled={loading}>Download PDF</button>
        </div>
      </div>
    </div>
  );
}
