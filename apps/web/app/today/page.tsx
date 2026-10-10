"use client";

import { useEffect, useState } from "react";

type Task = { id: string; title: string; estimated_minutes: number; status: string };
type Block = { task_id: string; proposed_start: string; proposed_end: string; reasoning: string; conflict_flag: boolean };
type Plan = { id: string; status: string; baseline: { planned_blocks: Block[] }; proposal: { planned_blocks: Block[]; deferred_tasks: string[]; conflicted_tasks: string[]; fallback_reason?: string | null } };

const localInput = (value: string) => new Date(value).toISOString().slice(0, 16);

export default function TodayPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [planningDate, setPlanningDate] = useState(new Date().toISOString().slice(0, 10));
  const [availableHours, setAvailableHours] = useState(8);
  const [energy, setEnergy] = useState("medium");
  const [review, setReview] = useState<Record<string, { completed: boolean; notes: string }>>({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadTasks() {
    const response = await fetch("/api/tasks", { cache: "no-store" });
    if (!response.ok) throw new Error("Could not load tasks.");
    setTasks(await response.json());
  }
  useEffect(() => { loadTasks().catch((cause: Error) => setError(cause.message)); }, []);

  const title = (id: string) => tasks.find(task => task.id === id)?.title || id;
  const updateBlock = (index: number, patch: Partial<Block>) => setBlocks(current => current.map((block, position) => position === index ? { ...block, ...patch } : block));
  const moveBlock = (index: number, direction: -1 | 1) => setBlocks(current => { const next = [...current]; const target = index + direction; if (target < 0 || target >= next.length) return next; [next[index], next[target]] = [next[target], next[index]]; return next; });

  async function generate() {
    setLoading(true); setError("");
    try {
      const response = await fetch("/api/plans/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ date: planningDate, available_hours: availableHours, energy_level: energy, task_ids: selected }) });
      if (!response.ok) throw new Error("Plan generation failed.");
      const nextPlan = await response.json(); setPlan(nextPlan); setBlocks(nextPlan.proposal.planned_blocks);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Plan generation failed."); } finally { setLoading(false); }
  }
  async function saveEdits() {
    if (!plan) return;
    const response = await fetch(`/api/plans/${plan.id}/blocks`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(blocks) });
    if (!response.ok) { setError(await response.text()); return; }
    const nextPlan = await response.json(); setPlan(nextPlan); setBlocks(nextPlan.proposal.planned_blocks);
  }
  async function transition(action: "approve" | "reject") {
    if (!plan || (action === "approve" && !window.confirm("Approve this edited plan?"))) return;
    const response = await fetch(`/api/plans/${plan.id}/${action}`, { method: "POST" });
    if (!response.ok) { setError(await response.text()); return; }
    setPlan(await response.json());
  }
  async function submitReview() {
    if (!plan || plan.status !== "APPROVED") return;
    const items = tasks.filter(task => selected.includes(task.id)).map(task => ({ task_id: task.id, completed: review[task.id]?.completed ?? false, notes: review[task.id]?.notes || null }));
    const response = await fetch(`/api/plans/${plan.id}/review`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(items) });
    if (!response.ok) { setError(await response.text()); return; }
    setPlan(await response.json()); await loadTasks();
  }

  return <main className="workspace"><header className="topbar"><div><span className="eyebrow">SCHEDULE REVIEW</span><h1>Today</h1></div><a className="primary-button" href="/capture">Capture</a></header><section className="panel-dark capture-panel"><div className="panel-heading"><div><span className="eyebrow">PLAN SETTINGS</span><h3>Shape a plan you can keep</h3></div><button className="primary-button" disabled={loading || selected.length === 0} onClick={generate}>{loading ? "Generating..." : "Generate plan"}</button></div><div className="form-row"><label>Date<input type="date" value={planningDate} onChange={event => setPlanningDate(event.target.value)} /></label><label>Available hours<input type="number" min="1" max="24" value={availableHours} onChange={event => setAvailableHours(Number(event.target.value))} /></label><label>Energy<select value={energy} onChange={event => setEnergy(event.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label></div><div className="task-list">{tasks.filter(task => task.status !== "completed").map(task => <label className="task-row" key={task.id}><input type="checkbox" checked={selected.includes(task.id)} onChange={event => setSelected(current => event.target.checked ? [...current, task.id] : current.filter(id => id !== task.id))} /><div><strong>{task.title}</strong><small>{task.estimated_minutes} min · {task.status}</small></div></label>)}</div>{error && <p className="error">{error}</p>}</section>{plan && <><div className="dashboard-grid"><PlanColumn title="Deterministic baseline" blocks={plan.baseline.planned_blocks} taskTitle={title} /><section className="inbox-panel"><div className="section-title"><div><span className="eyebrow">EDITABLE PROPOSAL</span><h3>{plan.proposal.fallback_reason ? "Deterministic fallback" : "Provider proposal"}</h3></div><span className="count-pill">{plan.status}</span></div>{blocks.map((block, index) => <article className="task-row" key={block.task_id}><div style={{ flex: 1 }}><strong>{title(block.task_id)}</strong><div className="form-row"><input aria-label="Block start" type="datetime-local" value={localInput(block.proposed_start)} onChange={event => updateBlock(index, { proposed_start: new Date(event.target.value).toISOString() })} /><input aria-label="Block end" type="datetime-local" value={localInput(block.proposed_end)} onChange={event => updateBlock(index, { proposed_end: new Date(event.target.value).toISOString() })} /></div><small>{block.reasoning}{block.conflict_flag ? " · conflict" : ""}</small></div><button title="Move block up" onClick={() => moveBlock(index, -1)}>↑</button><button title="Move block down" onClick={() => moveBlock(index, 1)}>↓</button></article>)}<div className="grid"><button onClick={saveEdits} disabled={plan.status === "APPROVED" || plan.status === "COMPLETED"}>Save edits</button><button className="primary-button" onClick={() => transition("approve")} disabled={plan.status === "APPROVED" || plan.status === "COMPLETED"}>Approve</button><button onClick={() => transition("reject")} disabled={plan.status === "APPROVED" || plan.status === "COMPLETED"}>Reject</button></div></section></div><section className="panel-dark capture-panel"><div className="section-title"><div><span className="eyebrow">END OF DAY</span><h3>What happened?</h3></div></div>{tasks.filter(task => selected.includes(task.id)).map(task => <label className="task-row" key={task.id}><input type="checkbox" checked={review[task.id]?.completed || false} onChange={event => setReview(current => ({ ...current, [task.id]: { completed: event.target.checked, notes: current[task.id]?.notes || "" } }))} /><div style={{ flex: 1 }}><strong>{task.title}</strong><input placeholder="Optional note" value={review[task.id]?.notes || ""} onChange={event => setReview(current => ({ ...current, [task.id]: { completed: current[task.id]?.completed || false, notes: event.target.value } }))} /></div></label>)}<button className="primary-button" disabled={plan.status !== "APPROVED"} onClick={submitReview}>Save end-of-day review</button></section></>}</main>;
}

function PlanColumn({ title, blocks, taskTitle }: { title: string; blocks: Block[]; taskTitle: (id: string) => string }) { return <section className="inbox-panel"><div className="section-title"><h3>{title}</h3></div>{blocks.map(block => <article className="task-row" key={block.task_id}><div><strong>{taskTitle(block.task_id)}</strong><small>{new Date(block.proposed_start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} to {new Date(block.proposed_end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}{block.conflict_flag ? " · conflict" : ""}</small><small>{block.reasoning}</small></div></article>)}</section>; }
