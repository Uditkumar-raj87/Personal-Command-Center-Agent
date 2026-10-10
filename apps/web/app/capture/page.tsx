"use client";

import { useEffect, useState } from "react";
import { taskSchema, type TaskInput } from "../../lib/schemas/task";
import FocusCore from "../components/FocusCore";

type Task = TaskInput & { id: string; status: string };

export default function CapturePage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [form, setForm] = useState<TaskInput>({ title: "", estimated_minutes: 30, energy_level: "medium", priority_tag: "routine", source: "web_form" });
  const [error, setError] = useState("");

  async function refresh() {
    const response = await fetch("/api/tasks", { cache: "no-store" });
    if (response.ok) setTasks(await response.json());
  }

  useEffect(() => { refresh().catch(() => setError("Could not load tasks.")); }, []);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const parsed = taskSchema.safeParse(form);
    if (!parsed.success) { setError(parsed.error.issues[0]?.message || "Check the task fields."); return; }
    const response = await fetch("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parsed.data) });
    if (!response.ok) { setError("The API rejected this task."); return; }
    setForm({ ...form, title: "" }); setError(""); await refresh();
  }

  async function remove(id: string) {
    const response = await fetch(`/api/tasks/${id}`, { method: "DELETE" });
    if (!response.ok) setError("Could not delete that task."); else await refresh();
  }

  return <main className="command-shell"><aside className="sidebar"><div className="brand-mark">✦</div><div className="brand-name">NOVA<span>/01</span></div><p className="side-caption">PERSONAL COMMAND CENTER</p><nav><a className="active" href="/capture">✦ Capture</a><a href="/today">◷ Today</a></nav><div className="side-footer"><div className="avatar">UR</div><div><strong>Private workspace</strong><small>Development identity</small></div></div></aside><section className="workspace"><header className="topbar"><div><span className="eyebrow">PERSONAL COMMAND CENTER</span><h1>Capture what matters.</h1></div><a className="primary-button" href="/today">Plan today</a></header><div className="dashboard-grid"><section className="inbox-panel focus-panel"><FocusCore tasks={tasks} /></section><section className="capture-panel panel-dark"><div className="panel-heading"><div><span className="eyebrow">NEW INPUT</span><h3>Capture a task</h3></div></div><form onSubmit={submit}><label>Title<input autoFocus value={form.title} onChange={event => setForm({ ...form, title: event.target.value })} placeholder="Prepare Q4 project brief" /></label><label>Description<textarea value={form.description || ""} onChange={event => setForm({ ...form, description: event.target.value })} /></label><div className="form-row"><label>Deadline<input type="datetime-local" value={form.deadline || ""} onChange={event => setForm({ ...form, deadline: event.target.value })} /></label><label>Minutes<input type="number" min="1" max="1440" value={form.estimated_minutes} onChange={event => setForm({ ...form, estimated_minutes: Number(event.target.value) })} /></label></div><div className="form-row"><label>Energy<select value={form.energy_level} onChange={event => setForm({ ...form, energy_level: event.target.value as TaskInput["energy_level"] })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label><label>Priority<select value={form.priority_tag} onChange={event => setForm({ ...form, priority_tag: event.target.value as TaskInput["priority_tag"] })}><option value="urgent_important">Urgent and important</option><option value="important">Important</option><option value="routine">Routine</option><option value="low">Low</option></select></label></div>{error && <p className="error">{error}</p>}<button className="primary-button" type="submit">Add to inbox</button></form></section><section className="inbox-panel"><div className="section-title"><div><span className="eyebrow">INBOX</span><h3>Open tasks</h3></div><span className="count-pill">{tasks.length}</span></div>{tasks.length === 0 ? <div className="empty-state"><span>✦</span><p>Your next meaningful task belongs here.</p></div> : <div className="task-list">{tasks.map(task => <div className="task-row" key={task.id}><span className={`priority-dot ${task.priority_tag}`} /><div><strong>{task.title}</strong><small>{task.estimated_minutes} min · {task.energy_level} energy · {task.status}</small></div><button className="task-arrow" title="Delete task" onClick={() => remove(task.id)}>×</button></div>)}</div>}</section></div></section></main>;
}
