import React from "react";

export default function StatusBadge({ status }) {
  const normalized = (status || "").toUpperCase();
  const cls = normalized === "PASS" ? "pass" : normalized === "FAIL" ? "fail" : "warn";
  return <span className={`badge ${cls}`}>{normalized || "N/A"}</span>;
}
