"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { taskSchema, type TaskInput } from "../../lib/schemas/task";

export default function CapturePage() {
  const [tasks, setTasks] = useState<TaskInput[]>([]);
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<TaskInput>({ resolver: zodResolver(taskSchema), defaultValues: { estimated_minutes: 30, energy_level: "medium", priority_tag: "routine", source: "web_form" } });
  useEffect(() => { fetch("/api/tasks").then((response) => response.ok ? response.json() : []).then(setTasks).catch(() => setTasks([])); }, []);
  const submit = async (input: TaskInput) => { setTasks((current) => [input, ...current]); reset(); await fetch("/api/tasks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }); };
  return <main><h1>Capture a task</h1><p>Build today&apos;s plan from explicit, reviewable inputs.</p><section className="panel"><form onSubmit={handleSubmit(submit)} className="grid">
    <label>Title<input {...register("title")} />{errors.title && <small>{errors.title.message}</small>}</label>
    <label>Deadline<input type="datetime-local" {...register("deadline")} /></label>
    <label>Estimated minutes<input type="range" min="15" max="180" step="15" {...register("estimated_minutes")} /></label>
    <label>Energy<select {...register("energy_level")}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
    <label>Priority<select {...register("priority_tag")}><option value="urgent_important">Urgent + important</option><option value="important">Important</option><option value="routine">Routine</option><option value="low">Low</option></select></label>
    <button disabled={isSubmitting} type="submit">{isSubmitting ? "Saving..." : "Add to inbox"}</button>
  </form></section><section><h2>Today&apos;s inbox</h2>{tasks.length === 0 ? <p>No unassigned tasks yet.</p> : <ul>{tasks.map((task, index) => <li key={`${task.title}-${index}`}>{task.title} · {task.estimated_minutes}m · {task.priority_tag}</li>)}</ul>}</section></main>;
}