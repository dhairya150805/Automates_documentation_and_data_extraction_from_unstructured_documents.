import React, { useEffect, useState } from "react";
import API from "../services/api";

export default function Admin() {
  const currentUserId = Number(sessionStorage.getItem("currentUserId") || 0);
  const [overview, setOverview] = useState({ users: 0, admins: 0, files: 0, cases: 0 });
  const [users, setUsers] = useState([]);
  const [files, setFiles] = useState([]);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState("");

  const loadOverview = async () => {
    const res = await API.get("/admin/overview");
    setOverview(res.data || { users: 0, admins: 0, files: 0, cases: 0 });
  };

  const loadUsers = async () => {
    const res = await API.get("/admin/users");
    setUsers(res.data?.users || []);
  };

  const loadFiles = async () => {
    const res = await API.get("/admin/files?page=1&limit=200");
    setFiles(res.data?.files || []);
  };

  const loadCases = async () => {
    const res = await API.get("/admin/cases?page=1&limit=200");
    setCases(res.data?.cases || []);
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      await Promise.all([loadOverview(), loadUsers(), loadFiles(), loadCases()]);
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to load admin data.";
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const deleteUser = async (targetUserId, label) => {
    if (!window.confirm(`Delete user ${label}? This will remove their files and cases.`)) {
      return;
    }
    setBusyAction(`delete-user-${targetUserId}`);
    try {
      const res = await API.delete(`/admin/users/${targetUserId}`);
      alert(res.data?.message || "User deleted.");
      await loadAll();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to delete user.";
      alert(msg);
    } finally {
      setBusyAction("");
    }
  };

  const deleteFile = async (docId, fileName) => {
    if (!window.confirm(`Delete file ${fileName}?`)) {
      return;
    }
    setBusyAction(`delete-file-${docId}`);
    try {
      const res = await API.delete(`/admin/files/${docId}`);
      alert(res.data?.message || "File deleted.");
      await loadAll();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to delete file.";
      alert(msg);
    } finally {
      setBusyAction("");
    }
  };

  const deleteCase = async (caseId, caseTitle) => {
    if (!window.confirm(`Delete case ${caseTitle}? This will remove all files in that case.`)) {
      return;
    }
    setBusyAction(`delete-case-${caseId}`);
    try {
      const res = await API.delete(`/admin/cases/${caseId}`);
      alert(res.data?.message || "Case deleted.");
      await loadAll();
    } catch (error) {
      const msg = error?.response?.data?.detail || "Failed to delete case.";
      alert(msg);
    } finally {
      setBusyAction("");
    }
  };

  return (
    <div className="fade-in">
      <div style={{ marginBottom: "24px" }}>
        <h1 className="page-title">Admin Console</h1>
        <p className="subtle">Manage users, uploaded files, and ongoing cases across the system.</p>
      </div>

      <div className="card" style={{ marginBottom: "18px" }}>
        <div className="controls" style={{ justifyContent: "space-between", width: "100%" }}>
          <h3 style={{ margin: 0 }}>System Overview</h3>
          <button className="button secondary" onClick={loadAll} disabled={loading || Boolean(busyAction)}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
        <div className="grid" style={{ marginTop: "12px" }}>
          <div className="col-3"><div className="stat primary"><h3>Total Users</h3><div className="value">{overview.users}</div></div></div>
          <div className="col-3"><div className="stat secondary"><h3>Admin Users</h3><div className="value">{overview.admins}</div></div></div>
          <div className="col-3"><div className="stat success"><h3>Total Files</h3><div className="value">{overview.files}</div></div></div>
          <div className="col-3"><div className="stat warning"><h3>Total Cases</h3><div className="value">{overview.cases}</div></div></div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Users</h3>
        <p className="subtle">View users, their uploaded file counts, and created case counts.</p>
        <table className="table" style={{ marginTop: "12px" }}>
          <thead>
            <tr>
              <th>User ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Files Uploaded</th>
              <th>Cases Created</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {users.length === 0 && (
              <tr>
                <td colSpan="7">No users found.</td>
              </tr>
            )}
            {users.map((user) => (
              <tr key={user.user_id}>
                <td>{user.user_id}</td>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.files_uploaded}</td>
                <td>{user.cases_created}</td>
                <td>
                  <button
                    className="button secondary"
                    disabled={user.user_id === currentUserId || busyAction === `delete-user-${user.user_id}`}
                    onClick={() => deleteUser(user.user_id, user.email)}
                  >
                    Delete User
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card" style={{ marginBottom: "18px" }}>
        <h3 style={{ marginTop: 0 }}>Uploaded Files</h3>
        <p className="subtle">All files uploaded by all users.</p>
        <table className="table" style={{ marginTop: "12px" }}>
          <thead>
            <tr>
              <th>Doc ID</th>
              <th>Filename</th>
              <th>Type</th>
              <th>Owner</th>
              <th>Case</th>
              <th>Uploaded At</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {files.length === 0 && (
              <tr>
                <td colSpan="7">No files found.</td>
              </tr>
            )}
            {files.map((file) => (
              <tr key={file.document_id}>
                <td>{file.document_id}</td>
                <td>{file.filename}</td>
                <td>{file.doc_type}</td>
                <td>{file.owner_name || `User ${file.owner_user_id}`}</td>
                <td>{file.case_title || `Case ${file.case_id || "-"}`}</td>
                <td>{file.upload_time}</td>
                <td>
                  <button
                    className="button secondary"
                    disabled={busyAction === `delete-file-${file.document_id}`}
                    onClick={() => deleteFile(file.document_id, file.filename)}
                  >
                    Delete File
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Ongoing Cases</h3>
        <p className="subtle">Manage all currently created cases across users.</p>
        <table className="table" style={{ marginTop: "12px" }}>
          <thead>
            <tr>
              <th>Case ID</th>
              <th>Title</th>
              <th>Owner</th>
              <th>Evidence Count</th>
              <th>Created At</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 && (
              <tr>
                <td colSpan="6">No cases found.</td>
              </tr>
            )}
            {cases.map((item) => (
              <tr key={item.case_id}>
                <td>{item.case_id}</td>
                <td>{item.title}</td>
                <td>{item.owner_name || `User ${item.owner_user_id}`}</td>
                <td>{item.evidence_count}</td>
                <td>{item.created_at}</td>
                <td>
                  <button
                    className="button secondary"
                    disabled={busyAction === `delete-case-${item.case_id}`}
                    onClick={() => deleteCase(item.case_id, item.title)}
                  >
                    Delete Case
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
