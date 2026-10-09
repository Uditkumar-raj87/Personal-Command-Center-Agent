"use client";

import { useState } from "react";

export default function TodayPage() {
  const [approved, setApproved] = useState(false);
  return <main><h1>Today</h1><p>Review every proposed block before it becomes a commitment.</p><section className="panel"><h2>{approved ? "Schedule approved" : "Proposed schedule"}</h2><p>No plan generated yet. Capture tasks, then compare the deterministic baseline with the structured proposal.</p><div className="grid"><button onClick={() => setApproved(true)}>Approve Schedule</button><button onClick={() => setApproved(false)}>Reject and Revert to Baseline</button></div></section></main>;
}