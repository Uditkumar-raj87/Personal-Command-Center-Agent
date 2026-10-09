"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function FocusCore() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.z = 4.8;
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
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
    const stars = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ color: 0xc5d4ff, size: 0.025, transparent: true, opacity: 0.65 }));
    const positions = new Float32Array(180 * 3);
    for (let i = 0; i < positions.length; i += 3) { positions[i] = (Math.random() - 0.5) * 5; positions[i + 1] = (Math.random() - 0.5) * 5; positions[i + 2] = (Math.random() - 0.5) * 3; }
    stars.geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3)); scene.add(stars);
    let frame = 0;
    const animate = () => { frame = requestAnimationFrame(animate); group.rotation.y += 0.004; group.rotation.x = Math.sin(Date.now() * 0.0005) * 0.12; ring.rotation.z += 0.008; ringTwo.rotation.z -= 0.005; stars.rotation.y -= 0.0005; renderer.render(scene, camera); };
    animate();
    return () => { cancelAnimationFrame(frame); window.removeEventListener("resize", resize); renderer.dispose(); };
  }, []);
  return <canvas ref={canvasRef} className="focus-canvas" aria-label="Animated planning focus core" />;
}