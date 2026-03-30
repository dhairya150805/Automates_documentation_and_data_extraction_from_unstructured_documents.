import React, { useEffect, useState } from "react";
import API from "../services/api";

const audioTypes = new Set(["wav", "mp3", "m4a", "flac", "aac", "ogg", "opus", "wma", "webm", "mp4", "mpeg"]);

export default function ExtractedData() {
  const [caseId, setCaseId] = useState(sessionStorage.getItem("currentCaseId") || "");
  const [cases, setCases] = useState([]);
  const [docId, setDocId] = useState(sessionStorage.getItem("currentDocId") || "");
  const [documents, setDocuments] = useState([]);
  const [ocrText, setOcrText] = useState("");
  const [extracted, setExtracted] = useState([]);
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const showError = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message || fallback;
    alert(message);
  };

  const loadCases = async () => {
    try {
      const res = await API.get("/cases?page=1&limit=100");
      const loadedCases = res.data?.cases || res.data || [];
      setCases(loadedCases);
    } catch (error) {
      showError(error, "Failed to load case list.");
    }
  };

  const loadCaseDocuments = async (targetCaseId = caseId) => {
    if (!targetCaseId) {
      setDocuments([]);
      setDocId("");
      sessionStorage.removeItem("currentDocId");
      return;
    }
    setLoading(true);
    try {
      const res = await API.get(`/cases/${targetCaseId}/summary`);
      const evidence = res.data?.evidence || [];
      setDocuments(evidence);

      const currentDocId = sessionStorage.getItem("currentDocId");
      const hasCurrent = evidence.some((item) => String(item.doc_id) === String(currentDocId));
      if (hasCurrent) {
        setDocId(String(currentDocId));
      } else if (evidence.length > 0) {
        const firstDocId = String(evidence[0].doc_id);
        setDocId(firstDocId);
        sessionStorage.setItem("currentDocId", firstDocId);
      } else {
        setDocId("");
        sessionStorage.removeItem("currentDocId");
      }
    } catch (error) {
      setDocuments([]);
      setDocId("");
      const msg = error?.response?.data?.detail || "Failed to load files for this case.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
    if (caseId) {
      loadCaseDocuments(caseId);
    }
  }, []);

  const ensureDocId = () => {
    if (!docId) {
      alert("Please select a file first.");
      return false;
    }
    sessionStorage.setItem("currentDocId", docId);
    return true;
  };

  const runOcr = async () => {
    if (!ensureDocId()) return;
    setLoading(true);
    try {
      const res = await API.post(`/ocr?doc_id=${docId}`);
      setOcrText(res.data.text || "");
      return true;
    } catch (error) {
      showError(error, "OCR failed.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const runExtract = async () => {
    if (!ensureDocId()) return;
    const selectedDoc = documents.find((item) => String(item.doc_id) === String(docId));
    if (selectedDoc && audioTypes.has(String(selectedDoc.file_type || "").toLowerCase())) {
      setExtracted([]);
      alert("Field extraction is skipped for audio files. Transcript text is available from OCR.");
      return true;
    }
    setLoading(true);
    try {
      const res = await API.post(`/extract?doc_id=${docId}`);
      setExtracted(res.data.extracted_data || []);
      return true;
    } catch (error) {
      showError(error, "Extraction failed.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const runSummary = async () => {
    if (!ensureDocId()) return;
    setLoading(true);
    try {
      const res = await API.post(`/summary?doc_id=${docId}`);
      setSummary(res.data.summary || "");
      return true;
    } catch (error) {
      showError(error, "Summarization failed.");
      return false;
    } finally {
      setLoading(false);
    }
  };

  const runPipeline = async () => {
    const okOcr = await runOcr();
    if (!okOcr) return;
    const selectedDoc = documents.find((item) => String(item.doc_id) === String(docId));
    const isAudio = selectedDoc && audioTypes.has(String(selectedDoc.file_type || "").toLowerCase());
    if (!isAudio) {
      const okExtract = await runExtract();
      if (!okExtract) return;
    }
    await runSummary();
  };

  return (
    <div>
      <h1 className="page-title">Extraction Studio</h1>
      <p className="subtle">Run OCR, extract structured fields, and generate summaries in one place.</p>

      <div className="card">
        <div className="controls">
          <select
            className="input"
            value={caseId}
            onChange={(e) => {
              const value = e.target.value;
              setCaseId(value);
              sessionStorage.setItem("currentCaseId", value);
              loadCaseDocuments(value);
            }}
          >
            <option value="">Select case name</option>
            {cases.map((item) => (
              <option key={item.case_id} value={item.case_id}>
                {item.title}
              </option>
            ))}
          </select>
          <button className="button secondary" onClick={loadCases} disabled={loading}>Refresh Cases</button>
          <select
            className="input"
            value={docId}
            onChange={(e) => {
              const selected = e.target.value;
              setDocId(selected);
              if (selected) {
                sessionStorage.setItem("currentDocId", selected);
              }
            }}
            disabled={documents.length === 0}
          >
            <option value="">Select uploaded file</option>
            {documents.map((item) => (
              <option key={item.doc_id} value={item.doc_id}>
                {item.filename} (Doc ID: {item.doc_id})
              </option>
            ))}
          </select>
          <button className="button" onClick={runOcr} disabled={loading}>Run OCR</button>
          <button className="button secondary" onClick={runExtract} disabled={loading}>Run Extract</button>
          <button className="button secondary" onClick={runSummary} disabled={loading}>Run Summary</button>
          <button className="button" onClick={runPipeline} disabled={loading}>Run Pipeline</button>
        </div>
        {docId && (() => {
          const selectedDoc = documents.find((item) => String(item.doc_id) === String(docId));
          const isAudio = selectedDoc && audioTypes.has(String(selectedDoc.file_type || "").toLowerCase());
          if (!isAudio) return null;
          return (
            <p className="subtle" style={{ marginTop: "10px" }}>
              Audio file selected. Pipeline will run transcription + summary.
            </p>
          );
        })()}
      </div>

      <div className="grid" style={{ marginTop: "16px" }}>
        <div className="col-6">
          <div className="card">
            <h3 style={{ marginTop: 0 }}>OCR Text (Preview)</h3>
            <div className="muted-box" style={{ whiteSpace: "pre-wrap", maxHeight: "240px", overflow: "auto" }}>
              {ocrText || "No OCR output yet."}
            </div>
          </div>
        </div>
        <div className="col-12">
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Extracted Fields</h3>
            <table className="table">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {extracted.length === 0 && (
                  <tr>
                    <td colSpan="3">No extracted data yet.</td>
                  </tr>
                )}
                {extracted.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.field}</td>
                    <td>{row.value}</td>
                    <td>{row.confidence}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="col-12">
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Summary</h3>
            <div className="muted-box" style={{ whiteSpace: "pre-wrap" }}>
              {summary || "No summary yet."}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
