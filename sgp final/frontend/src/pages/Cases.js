import React, { useEffect, useState } from "react";
import API from "../services/api";

const defaultRules = {
  required_fields: ["Invoice No", "Date", "Amount"],
  patterns: { Date: "^\\d{2}/\\d{2}/\\d{4}$" },
  value_constraints: { Amount: { min: 1, max: 100000 } },
};

const docTypes = [
  "Invoice",
  "Medical Record",
  "Legal Document",
  "Audio Evidence",
  "Financial Statement",
  "Identity Document",
  "Contract",
  "Report",
  "Certificate",
  "Other",
];

const emptyReviewRow = () => ({ field: "", value: "", confidence: 0.5 });

export default function Cases() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);

  const [currentCaseId, setCurrentCaseId] = useState(sessionStorage.getItem("currentCaseId") || "");
  const [summaryCaseId, setSummaryCaseId] = useState(sessionStorage.getItem("currentCaseId") || "");
  const [caseSummary, setCaseSummary] = useState(null);
  const [reviewSummary, setReviewSummary] = useState(null);

  const [rulesText, setRulesText] = useState(JSON.stringify(defaultRules, null, 2));
  const [runCompliance, setRunCompliance] = useState(false);
  const [forceProcess, setForceProcess] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [totalCases, setTotalCases] = useState(0);
  const casesPerPage = 10;

  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDocType, setUploadDocType] = useState("Invoice");
  const [uploadDisplayName, setUploadDisplayName] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [lastDocId, setLastDocId] = useState(sessionStorage.getItem("currentDocId") || "");
  const [fileInputKey, setFileInputKey] = useState(0);

  const showNotification = (message, type = "info") => {
    const prefixByType = {
      success: "[OK]",
      error: "[ERROR]",
      warning: "[WARN]",
      info: "[INFO]",
    };
    const notification = document.createElement("div");
    notification.className = `alert ${type}`;
    notification.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span>${prefixByType[type] || "[INFO]"}</span>
        <span>${message}</span>
      </div>
    `;
    notification.style.cssText = `
      position: fixed; top: 20px; right: 20px; z-index: 1000;
      min-width: 300px; animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 4000);
  };

  const loadCases = async (page = 1) => {
    setLoading(true);
    try {
      const res = await API.get(`/cases?page=${page}&limit=${casesPerPage}`);
      const loadedCases = res.data?.cases || res.data || [];
      setCases(loadedCases);
      setTotalCases(res.data?.total || loadedCases.length);
      setCurrentPage(page);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to load cases.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, []);

  const createCase = async () => {
    if (!title.trim()) {
      showNotification("Case title is required.", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await API.post("/cases", {
        title: title.trim(),
        description: description.trim(),
      });
      const createdCaseId = String(res.data.case_id);
      setTitle("");
      setDescription("");
      sessionStorage.setItem("currentCaseId", createdCaseId);
      setCurrentCaseId(createdCaseId);
      setSummaryCaseId(createdCaseId);
      await loadCases();
      showNotification(`Case created: ${res.data.title} (ID: ${createdCaseId})`, "success");
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to create case.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const setActiveCase = (caseId) => {
    const value = String(caseId);
    sessionStorage.setItem("currentCaseId", value);
    setCurrentCaseId(value);
    setSummaryCaseId(value);
    setReviewSummary(null);
    setCaseSummary(null);
  };

  const loadSummary = async () => {
    if (!summaryCaseId) {
      showNotification("Select a case name to load summary.", "warning");
      return;
    }
    setLoading(true);
    try {
      const res = await API.get(`/cases/${summaryCaseId}/summary`);
      setCaseSummary(res.data);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to load case summary.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const loadReviewWorkspace = async () => {
    if (!summaryCaseId) {
      showNotification("Select a case name to load review workspace.", "warning");
      return;
    }
    setLoading(true);
    try {
      const res = await API.get(`/cases/${summaryCaseId}/summary`);
      setReviewSummary(res.data);
      sessionStorage.setItem("currentCaseId", String(summaryCaseId));
      setCurrentCaseId(String(summaryCaseId));
      showNotification("Review workspace loaded.", "success");
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to load review workspace.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const processCase = async () => {
    if (!currentCaseId) {
      showNotification("Please select a case first.", "warning");
      return;
    }

    let rulesObj = null;
    if (runCompliance) {
      try {
        rulesObj = JSON.parse(rulesText);
      } catch (_) {
        showNotification("Invalid JSON format in compliance rules.", "error");
        return;
      }
    }

    setLoading(true);
    try {
      const res = await API.post(`/cases/${currentCaseId}/process`, {
        run_compliance: runCompliance,
        rules: rulesObj,
        force: forceProcess,
      });
      const successCount = res.data.processed?.filter((p) => !p.error)?.length || 0;
      const errorCount = res.data.processed?.filter((p) => p.error)?.length || 0;
      if (errorCount > 0) {
        showNotification(
          `Processing completed with ${successCount} successful, ${errorCount} failed documents.`,
          "warning"
        );
      } else {
        showNotification(`Case processed successfully. ${successCount} documents processed.`, "success");
      }
      await loadReviewWorkspace();
      await loadSummary();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to process case.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const downloadCaseReport = async (format) => {
    if (!currentCaseId) {
      showNotification("Select a case first.", "warning");
      return;
    }
    setLoading(true);
    try {
      const res = await API.get(`/cases/${currentCaseId}/report?format=${format}`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `case_${currentCaseId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to download case report.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const uploadEvidence = async () => {
    if (!currentCaseId) {
      showNotification("Please choose a case before uploading.", "warning");
      return;
    }
    if (!uploadFile) {
      showNotification("Please select a file to upload.", "warning");
      return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (uploadFile.size > maxSize) {
      showNotification("File size must be less than 10MB.", "error");
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);

      const res = await API.post("/upload", formData, {
        params: {
          case_id: Number(currentCaseId),
          doc_type: uploadDocType,
          display_name: uploadDisplayName.trim() || undefined,
        },
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total || 1;
          setUploadProgress(Math.round((progressEvent.loaded * 100) / total));
        },
      });

      const docId = String(res.data.document_id);
      sessionStorage.setItem("currentDocId", docId);
      setLastDocId(docId);
      setUploadFile(null);
      setUploadDisplayName("");
      setFileInputKey((prev) => prev + 1);
      showNotification(`Document uploaded successfully (Doc ID: ${docId}).`, "success");
      await loadReviewWorkspace();
      await loadSummary();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Upload failed.";
      showNotification(msg, "error");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const updateReviewField = (docIndex, rowIndex, key, value) => {
    setReviewSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev, evidence: [...prev.evidence] };
      const doc = { ...next.evidence[docIndex] };
      const extracted = [...(doc.extracted_data || [])];
      extracted[rowIndex] = { ...extracted[rowIndex], [key]: value };
      doc.extracted_data = extracted;
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const addReviewRow = (docIndex) => {
    setReviewSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev, evidence: [...prev.evidence] };
      const doc = { ...next.evidence[docIndex] };
      doc.extracted_data = [...(doc.extracted_data || []), emptyReviewRow()];
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const removeReviewRow = (docIndex, rowIndex) => {
    setReviewSummary((prev) => {
      if (!prev) return prev;
      const next = { ...prev, evidence: [...prev.evidence] };
      const doc = { ...next.evidence[docIndex] };
      doc.extracted_data = (doc.extracted_data || []).filter((_, idx) => idx !== rowIndex);
      next.evidence[docIndex] = doc;
      return next;
    });
  };

  const saveReviewedDoc = async (doc) => {
    setLoading(true);
    try {
      await API.put(`/extract?doc_id=${doc.doc_id}`, {
        extracted_data: (doc.extracted_data || [])
          .filter((row) => (row.field || "").trim())
          .map((row) => ({
            field: (row.field || "").trim(),
            value: (row.value || "").trim(),
            confidence: Number(row.confidence) || 0,
          })),
      });
      showNotification(`Saved review for document ${doc.doc_id}.`, "success");
      await loadReviewWorkspace();
      await loadSummary();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to save reviewed data.";
      showNotification(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const activeCase = cases.find((row) => String(row.case_id) === String(currentCaseId));
  const activeCaseLabel = activeCase
    ? activeCase.title
    : (currentCaseId ? `Case ID: ${currentCaseId}` : "Not set");

  return (
    <div className="fade-in">
      <div style={{ marginBottom: "32px" }}>
        <h1 className="page-title">Case Workspace</h1>
        <p className="subtle">
          Single-page workflow for case creation, evidence upload, processing, and human review.
        </p>
      </div>

      <div className="card" style={{ maxWidth: "680px" }}>
        <div style={{ marginTop: "6px" }}>
          <label className="subtle">Case Title</label>
          <input
            className="input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Patient 1023 - MRI Review"
          />
        </div>
        <div style={{ marginTop: "12px" }}>
          <label className="subtle">Description (optional)</label>
          <textarea
            className="textarea"
            rows="3"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add brief context for the case."
            style={{ width: "100%" }}
          />
        </div>
        <div style={{ marginTop: "14px" }} className="controls">
          <button className="button" onClick={createCase} disabled={loading}>Create Case</button>
          <span className="subtle">Active Case: {activeCaseLabel}</span>
        </div>
      </div>

      <div className="card" style={{ marginTop: "18px" }}>
        <div className="controls" style={{ justifyContent: "space-between", width: "100%" }}>
          <h3 style={{ margin: 0 }}>Recent Cases</h3>
          <button className="button secondary" onClick={() => loadCases(currentPage)} disabled={loading}>Refresh</button>
        </div>
        <table className="table" style={{ marginTop: "12px" }}>
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Title</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 && (
              <tr>
                <td colSpan="4">No cases yet.</td>
              </tr>
            )}
            {cases.map((row) => (
              <tr key={row.case_id}>
                <td>{row.case_id}</td>
                <td>{row.title}</td>
                <td>{row.created_at}</td>
                <td>
                  <button className="button secondary" onClick={() => setActiveCase(row.case_id)}>
                    Use Case
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {totalCases > casesPerPage && (
          <div className="pagination" style={{ marginTop: "16px", display: "flex", justifyContent: "center", alignItems: "center", gap: "8px" }}>
            <button
              className="button secondary"
              onClick={() => loadCases(currentPage - 1)}
              disabled={currentPage === 1 || loading}
            >
              Previous
            </button>
            <span className="pagination-info">
              Page {currentPage} of {Math.ceil(totalCases / casesPerPage)} ({totalCases} total cases)
            </span>
            <button
              className="button secondary"
              onClick={() => loadCases(currentPage + 1)}
              disabled={currentPage >= Math.ceil(totalCases / casesPerPage) || loading}
            >
              Next
            </button>
          </div>
        )}
      </div>

      <div id="upload" className="card" style={{ marginTop: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Upload Evidence</h3>
        <p className="subtle">Upload documents directly into the currently active case.</p>
        <div className="grid">
          <div className="col-3">
            <label className="subtle">Case Name</label>
            <select
              className="input"
              value={currentCaseId}
              onChange={(e) => setActiveCase(e.target.value)}
            >
              <option value="">Select case</option>
              {cases.map((row) => (
                <option key={row.case_id} value={row.case_id}>
                  {row.title}
                </option>
              ))}
            </select>
          </div>
          <div className="col-3">
            <label className="subtle">Document Type</label>
            <select className="input" value={uploadDocType} onChange={(e) => setUploadDocType(e.target.value)}>
              {docTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="col-3">
            <label className="subtle">Custom File Name (optional)</label>
            <input
              className="input"
              type="text"
              value={uploadDisplayName}
              onChange={(e) => setUploadDisplayName(e.target.value)}
              placeholder="e.g., Invoice_Apr_2026"
            />
          </div>
          <div className="col-3">
            <label className="subtle">File</label>
            <input
              key={fileInputKey}
              className="input"
              type="file"
              onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            />
          </div>
        </div>
        <div className="controls" style={{ marginTop: "12px" }}>
          <button className="button" onClick={uploadEvidence} disabled={uploading || loading || !uploadFile}>
            {uploading ? `Uploading... ${uploadProgress}%` : "Upload Document"}
          </button>
          <span className="subtle">Last Uploaded Doc ID: {lastDocId || "None"}</span>
        </div>
      </div>

      <div className="card" style={{ marginTop: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Case Pipeline</h3>
        <p className="subtle">Process all documents in the active case and download report exports.</p>
        <div className="controls">
          <button className="button" onClick={processCase} disabled={loading}>Process Case</button>
          <button className="button secondary" onClick={() => downloadCaseReport("csv")} disabled={loading}>Download CSV</button>
          <button className="button secondary" onClick={() => downloadCaseReport("pdf")} disabled={loading}>Download PDF</button>
        </div>
        <div style={{ marginTop: "12px" }}>
          <label className="subtle">
            <input
              type="checkbox"
              checked={runCompliance}
              onChange={(e) => setRunCompliance(e.target.checked)}
              style={{ marginRight: "6px" }}
            />
            Run compliance checks
          </label>
        </div>
        <div style={{ marginTop: "8px" }}>
          <label className="subtle">
            <input
              type="checkbox"
              checked={forceProcess}
              onChange={(e) => setForceProcess(e.target.checked)}
              style={{ marginRight: "6px" }}
            />
            Force reprocess (overwrite OCR/extraction/summary)
          </label>
        </div>
        {runCompliance && (
          <div style={{ marginTop: "10px" }}>
            <label className="subtle">Rules (JSON)</label>
            <textarea
              className="textarea"
              rows="6"
              value={rulesText}
              onChange={(e) => setRulesText(e.target.value)}
              style={{ width: "100%" }}
            />
          </div>
        )}
      </div>

      <div id="review" className="card" style={{ marginTop: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Review Workspace</h3>
        <div className="controls" style={{ marginTop: "10px" }}>
          <select
            className="input"
            value={summaryCaseId}
            onChange={(e) => setSummaryCaseId(e.target.value)}
          >
            <option value="">Select case</option>
            {cases.map((row) => (
              <option key={row.case_id} value={row.case_id}>
                {row.title}
              </option>
            ))}
          </select>
          <button className="button secondary" onClick={loadReviewWorkspace} disabled={loading}>Load Review</button>
          <button className="button secondary" onClick={loadSummary} disabled={loading}>Load JSON Summary</button>
        </div>

        {!reviewSummary && (
          <p className="subtle" style={{ marginTop: "12px" }}>
            No review data loaded yet. Select a case and click "Load Review".
          </p>
        )}
      </div>

      {reviewSummary && reviewSummary.evidence?.map((doc, docIndex) => (
        <div className="card" style={{ marginTop: "18px" }} key={doc.doc_id}>
          <div className="controls" style={{ justifyContent: "space-between", width: "100%" }}>
            <div>
              <strong>Doc {doc.doc_id}</strong> - {doc.filename} ({doc.file_type || "unknown"})
            </div>
            <div className="controls">
              <button className="button secondary" onClick={() => addReviewRow(docIndex)}>Add Field</button>
              <button className="button" onClick={() => saveReviewedDoc(doc)} disabled={loading}>Save</button>
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
              {(!doc.extracted_data || doc.extracted_data.length === 0) && (
                <tr>
                  <td colSpan="4">No extracted data.</td>
                </tr>
              )}
              {(doc.extracted_data || []).map((row, rowIndex) => (
                <tr key={rowIndex}>
                  <td>
                    <input
                      className="input"
                      value={row.field || ""}
                      onChange={(e) => updateReviewField(docIndex, rowIndex, "field", e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      className="input"
                      value={row.value || ""}
                      onChange={(e) => updateReviewField(docIndex, rowIndex, "value", e.target.value)}
                    />
                  </td>
                  <td style={{ maxWidth: "140px" }}>
                    <input
                      className="input"
                      type="number"
                      step="0.01"
                      value={row.confidence ?? 0}
                      onChange={(e) => updateReviewField(docIndex, rowIndex, "confidence", e.target.value)}
                    />
                  </td>
                  <td>
                    <button className="button secondary" onClick={() => removeReviewRow(docIndex, rowIndex)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      <div className="card" style={{ marginTop: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Structured Case Summary</h3>
        <div className="muted-box" style={{ marginTop: "12px", maxHeight: "320px", overflow: "auto" }}>
          <pre style={{ margin: 0 }}>
            {caseSummary ? JSON.stringify(caseSummary, null, 2) : "No summary loaded yet."}
          </pre>
        </div>
      </div>
    </div>
  );
}
