"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

type FocusTask = { id: string; title: string; priority_tag: string; status: string; deadline?: string | null };
const priorityColors: Record<string, number> = { urgent_important: 0xff7e9f, important: 0xffc86b, routine: 0x79e7c2, low: 0x8fa5d6 };

export default function FocusCore({ tasks = [], onSelect }: { tasks?: FocusTask[]; onSelect?: (task: FocusTask) => void }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tooltip, setTooltip] = useState<FocusTask | null>(null);
  const [fallback, setFallback] = useState(false);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let renderer: THREE.WebGLRenderer;
    try { renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true }); } catch { setFallback(true); return; }
    const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100); camera.position.z = 5; renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    const resize = () => { const size = Math.min(canvas.clientWidth, canvas.clientHeight); renderer.setSize(size, size, false); camera.aspect = 1; camera.updateProjectionMatrix(); }; resize(); window.addEventListener("resize", resize);
    const group = new THREE.Group(); const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.72, 2), new THREE.MeshBasicMaterial({ color: 0x7cf2c7, wireframe: true, transparent: true, opacity: 0.9 })); const inner = new THREE.Mesh(new THREE.SphereGeometry(0.38, 24, 24), new THREE.MeshBasicMaterial({ color: 0xffc86b, transparent: true, opacity: 0.85 })); group.add(core, inner); scene.add(group);
    const nodes: THREE.Mesh[] = []; const links: THREE.Line[] = []; const positions = tasks.slice(0, 12).map((_, index) => { const angle = (index / Math.max(tasks.length, 1)) * Math.PI * 2; return new THREE.Vector3(Math.cos(angle) * 1.45, Math.sin(angle) * 1.05, (index % 3 - 1) * 0.18); });
    tasks.slice(0, 12).forEach((task, index) => { const color = priorityColors[task.priority_tag] || priorityColors.routine; const node = new THREE.Mesh(new THREE.SphereGeometry(0.1 + (task.priority_tag === "urgent_important" ? 0.04 : 0), 12, 12), new THREE.MeshBasicMaterial({ color })); node.position.copy(positions[index]); node.userData.task = task; nodes.push(node); scene.add(node); const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), positions[index]]), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.35 })); links.push(line); scene.add(line); });
    const raycaster = new THREE.Raycaster(); const pointer = new THREE.Vector2(); const pick = (event: MouseEvent | PointerEvent) => { const bounds = canvas.getBoundingClientRect(); pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1; pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1; raycaster.setFromCamera(pointer, camera); const hit = raycaster.intersectObjects(nodes)[0]?.object as THREE.Mesh | undefined; setTooltip(hit?.userData.task || null); if (hit?.userData.task) onSelect?.(hit.userData.task); }; canvas.addEventListener("pointermove", pick); canvas.addEventListener("click", pick);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches; let frame = 0; const animate = () => { frame = requestAnimationFrame(animate); if (!reduced) { group.rotation.y += 0.004; nodes.forEach((node, index) => { node.position.y = positions[index].y + Math.sin(Date.now() * 0.001 + index) * 0.03; links[index].geometry.setFromPoints([new THREE.Vector3(0, 0, 0), node.position]); }); } renderer.render(scene, camera); }; animate();
    return () => { cancelAnimationFrame(frame); canvas.removeEventListener("pointermove", pick); canvas.removeEventListener("click", pick); window.removeEventListener("resize", resize); nodes.forEach(node => { node.geometry.dispose(); (node.material as THREE.Material).dispose(); }); links.forEach(line => { line.geometry.dispose(); (line.material as THREE.Material).dispose(); }); core.geometry.dispose(); (core.material as THREE.Material).dispose(); inner.geometry.dispose(); (inner.material as THREE.Material).dispose(); renderer.dispose(); };
  }, [onSelect, tasks]);
  return <div className="focus-visual"><canvas ref={canvasRef} className="focus-canvas" aria-label="Interactive task planning core" />{fallback && <div className="focus-fallback">Task focus core unavailable. Timeline remains available.</div>}{tooltip && <div className="focus-tooltip"><strong>{tooltip.title}</strong><small>{tooltip.priority_tag.replace(/_/g, " ")}{tooltip.deadline ? ` · due ${new Date(tooltip.deadline).toLocaleDateString()}` : ""}</small></div>}</div>;
}