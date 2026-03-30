import React, { useEffect, useState } from "react";
import API from "../services/api";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await API.get("/logs");
        setLogs(res.data || []);
      } catch (e) {
        console.error(e);
      }
    };
    load();
  }, []);

  return (
    <div>
      <h1 className="page-title">Audit Logs</h1>
      <p className="subtle">Every action is recorded with timestamps for compliance tracking.</p>

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Action</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 && (
              <tr>
                <td colSpan="3">No logs yet.</td>
              </tr>
            )}
            {logs.map((log, idx) => (
              <tr key={idx}>
                <td>{log.user_id}</td>
                <td>{log.action}</td>
                <td>{log.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
