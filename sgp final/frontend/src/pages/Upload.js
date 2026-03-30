import React, { useState } from "react";
import API from "../services/api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState("Invoice");
  const [userId] = useState(sessionStorage.getItem("currentUserId") || "");
  const [caseId, setCaseId] = useState(sessionStorage.getItem("currentCaseId") || "");
  const [lastDocId, setLastDocId] = useState(sessionStorage.getItem("currentDocId") || "");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const docTypes = [
    "Invoice",
    "Medical Record", 
    "Legal Document",
    "Financial Statement",
    "Identity Document",
    "Contract",
    "Report",
    "Certificate",
    "Other"
  ];

  const showError = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message || fallback;
    alert(message);
  };

  const upload = async () => {
    if (!file) {
      alert("Please select a file to upload.");
      return;
    }
    if (!caseId) {
      alert("Please select a Case ID (create one in the Cases page).");
      return;
    }

    // File size validation (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      alert("File size must be less than 10MB.");
      return;
    }
    
    setUploading(true);
    setUploadSuccess(false);
    setUploadProgress(0);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await API.post("/upload", formData, {
        params: { case_id: caseId, doc_type: docType },
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      sessionStorage.setItem("currentDocId", String(res.data.document_id));
      setLastDocId(res.data.document_id);
      setUploadSuccess(true);
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('fileInput');
      if (fileInput) fileInput.value = '';
      alert(`✅ File uploaded successfully! Document ID: ${res.data.document_id}`);
    } catch (error) {
      showError(error, "Upload failed.");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div>
      <h1 className="page-title">Document Upload</h1>
      <p className="subtle">Push a document into the pipeline and generate a new processing job.</p>

      <div className="card">
        <div className="grid">
          <div className="col-4">
            <label className="subtle">Logged In User</label>
            <input
              className="input"
              type="text"
              value={userId}
              disabled
            />
          </div>
          <div className="col-4">
            <label className="subtle">Case ID</label>
            <input
              className="input"
              type="number"
              value={caseId}
              onChange={(e) => {
                const value = e.target.value;
                setCaseId(value);
                sessionStorage.setItem("currentCaseId", value);
              }}
              placeholder="Create in Cases page"
            />
          </div>
          <div className="col-4">
            <label className="subtle">Document Type</label>
            <select className="input" value={docType} onChange={(e) => setDocType(e.target.value)}>
              {docTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="col-4">
            <label className="subtle">File</label>
            <input
              id="fileInput"
              className="input"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.docx,.txt,.md,.wav,.mp3,.m4a,.flac,.aac,.ogg"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <div className="subtle" style={{ marginTop: "6px", fontSize: "12px" }}>
              Supported: PDF, images, DOCX, TXT, audio (WAV/MP3/M4A).
            </div>
          </div>
        </div>
        <div className="controls" style={{ marginTop: "12px" }}>
          <button 
            className={`button ${uploading ? 'loading' : ''}`} 
            onClick={upload}
            disabled={uploading || !file}
          >
            {uploading ? `Uploading... ${uploadProgress}%` : 'Upload Document'}
          </button>
          {uploadSuccess && (
            <div className="alert success" style={{ marginLeft: "12px", marginBottom: 0 }}>
              ✅ File uploaded successfully!
            </div>
          )}
        </div>
        
        {uploading && uploadProgress > 0 && (
          <div style={{ marginTop: "12px" }}>
            <div className="progress-bar">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <div className="subtle" style={{ marginTop: "4px", textAlign: "center" }}>
              {uploadProgress}% uploaded
            </div>
          </div>
        )}
        
        {lastDocId && (
          <div className="muted-box" style={{ marginTop: "16px" }}>
            <strong>Last Uploaded Document ID:</strong> {lastDocId}
          </div>
        )}

        <div style={{ marginTop: "16px", fontSize: "14px", color: "var(--gray-600)" }}>
          <strong>Supported formats:</strong>
          <ul style={{ margin: "8px 0", paddingLeft: "20px" }}>
            <li><strong>Documents:</strong> PDF, DOCX, TXT, MD</li>
            <li><strong>Images:</strong> PNG, JPG, JPEG, TIFF, BMP</li>
            <li><strong>Audio:</strong> WAV, MP3, M4A, FLAC, AAC, OGG</li>
          </ul>
          <p><strong>Note:</strong> Audio transcription requires FFmpeg to be installed on the server.</p>
        </div>
      </div>
    </div>
  );
}
