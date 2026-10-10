"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

type FocusTask = {
  id: string;
  title: string;
  priority_tag?: string;
  status?: string;
};

type FocusCoreProps = {
  tasks?: FocusTask[];
  onSelect?: (task: FocusTask) => void;
};

const priorityColors: Record<string, number> = {
  urgent_important: 0xff7e9f,
  important: 0xffc86b,
  routine: 0x7cf2c7,
  low: 0x8f9bb5,
};

export default function FocusCore({ tasks = [], onSelect }: FocusCoreProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [webglUnavailable, setWebglUnavailable] = useState(false);
  const [hoveredTask, setHoveredTask] = useState<FocusTask | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.z = 4.8;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    } catch {
      setWebglUnavailable(true);
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    const resize = () => { const size = Math.min(canvas.clientWidth, canvas.clientHeight); renderer.setSize(size, size, false); camera.aspect = 1; camera.updateProjectionMatrix(); };
    resize();
    window.addEventListener("resize", resize);
    const group = new THREE.Group();
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.72, 2), new THREE.MeshBasicMaterial({ color: 0x7cf2c7, wireframe: true, transparent: true, opacity: 0.9 }));
    const inner = new THREE.Mesh(new THREE.SphereGeometry(0.38, 32, 32), new THREE.MeshBasicMaterial({ color: 0xffc86b, transparent: true, opacity: 0.85 }));
    const ring = new THREE.Mesh(new THREE.TorusGeometry(1.02, 0.015, 8, 96), new THREE.MeshBasicMaterial({ color: 0x6a8cff, transparent: true, opacity: 0.75 }));
    const ringTwo = new THREE.Mesh(new THREE.TorusGeometry(1.34, 0.01, 8, 96), new THREE.MeshBasicMaterial({ color: 0xff7e9f, transparent: true, opacity: 0.55 }));
    ring.rotation.x = Math.PI / 2.5; ringTwo.rotation.x = -Math.PI / 3;
    group.add(core, inner, ring, ringTwo); scene.add(group);
    const nodeMeshes: THREE.Mesh[] = [];
    tasks.forEach((task, index) => {
      const angle = (index / Math.max(tasks.length, 1)) * Math.PI * 2;
      const radius = 1.65 + (index % 2) * 0.18;
      const node = new THREE.Mesh(
        new THREE.SphereGeometry(task.status === "completed" ? 0.07 : 0.1, 12, 12),
        new THREE.MeshBasicMaterial({ color: priorityColors[task.priority_tag || "routine"] || priorityColors.routine, transparent: true, opacity: 0.95 }),
      );
      node.position.set(Math.cos(angle) * radius, Math.sin(angle) * radius, (index % 3 - 1) * 0.12);
      node.userData.task = task;
      nodeMeshes.push(node);
      scene.add(node);
    });
    const stars = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xc5d4ff, size: 0.025, transparent: true, opacity: 0.65 }));
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const particleCount = window.innerWidth < 600 ? 70 : 180;
    const positions = new Float32Array(particleCount * 3);
    for (let i = 0; i < positions.length; i += 3) { positions[i] = (Math.random() - 0.5) * 5; positions[i + 1] = (Math.random() - 0.5) * 5; positions[i + 2] = (Math.random() - 0.5) * 3; }
    stars.geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3)); scene.add(stars);
    const pointer = new THREE.Vector2();
    const raycaster = new THREE.Raycaster();
    const updatePointer = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(nodeMeshes)[0]?.object as THREE.Mesh | undefined;
      setHoveredTask((hit?.userData.task as FocusTask | undefined) || null);
    };
    const selectTask = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(pointer, camera);
      const task = (raycaster.intersectObjects(nodeMeshes)[0]?.object.userData.task as FocusTask | undefined);
      if (task) onSelect?.(task);
    };
    canvas.addEventListener("pointermove", updatePointer);
    canvas.addEventListener("click", selectTask);
    let frame = 0;
    const animate = () => {
      if (!prefersReducedMotion) {
        frame = requestAnimationFrame(animate);
        group.rotation.y += 0.004;
        group.rotation.x = Math.sin(Date.now() * 0.0005) * 0.12;
        ring.rotation.z += 0.008;
        ringTwo.rotation.z -= 0.005;
        stars.rotation.y -= 0.0005;
      }
      renderer.render(scene, camera);
    };
    animate();
    return () => {
      cancelAnimationFrame(frame);
      canvas.removeEventListener("pointermove", updatePointer);
      canvas.removeEventListener("click", selectTask);
      window.removeEventListener("resize", resize);
      scene.traverse(object => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Points) {
          object.geometry.dispose();
          const material = object.material;
          if (Array.isArray(material)) material.forEach(item => item.dispose());
          else material.dispose();
        }
      });
      renderer.dispose();
    };
  }, [onSelect, tasks]);

  if (webglUnavailable) {
    return <div className="focus-fallback" role="img" aria-label="Planning core unavailable without WebGL"><span>✦</span><strong>Planning core</strong><small>WebGL is unavailable</small></div>;
  }
  return <div className="focus-scene"><canvas ref={canvasRef} className="focus-canvas" aria-label="Interactive animated planning focus core" />{hoveredTask && <div className="node-tooltip"><strong>{hoveredTask.title}</strong><small>{hoveredTask.priority_tag || "routine"} · {hoveredTask.status || "inbox"}</small></div>}</div>;
}