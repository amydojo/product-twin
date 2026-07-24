"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

export function GlbViewer({ src }: { src: string }) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    setStatus("loading");
    setError(null);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xece9e2);
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 2000);
    camera.position.set(115, -170, 95);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.enablePan = false;
    controls.minDistance = 80;
    controls.maxDistance = 420;
    controls.target.set(0, 0, 55);

    scene.add(new THREE.HemisphereLight(0xffffff, 0x777777, 2.2));
    const key = new THREE.DirectionalLight(0xffffff, 4.2);
    key.position.set(-90, -120, 180);
    scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, 2.4);
    fill.position.set(100, 30, 90);
    scene.add(fill);

    let disposed = false;
    const loader = new GLTFLoader();
    loader.load(
      src,
      (gltf) => {
        if (disposed) return;
        const object = gltf.scene;
        const box = new THREE.Box3().setFromObject(object);
        const center = box.getCenter(new THREE.Vector3());
        object.position.sub(center);
        object.rotation.x = Math.PI / 2;
        scene.add(object);
        controls.target.set(0, 0, 0);
        controls.update();
        setStatus("ready");
      },
      undefined,
      () => {
        setStatus("error");
        setError("The GLB could not be loaded.");
      },
    );

    const resize = () => {
      const width = Math.max(1, mount.clientWidth);
      const height = Math.max(360, mount.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(mount);
    resize();

    let frame = 0;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      controls.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      scene.traverse((node) => {
        if (node instanceof THREE.Mesh) {
          node.geometry.dispose();
          const materials = Array.isArray(node.material) ? node.material : [node.material];
          materials.forEach((material) => material.dispose());
        }
      });
    };
  }, [src]);

  return (
    <div
      className="viewer"
      ref={mountRef}
      aria-busy={status === "loading"}
      aria-label="Interactive GLB product twin viewer"
    >
      <p className="sr-only" role="status">
        {status === "ready" ? "GLB model loaded." : "Loading GLB model."}
      </p>
      {error ? <p role="alert">{error}</p> : null}
    </div>
  );
}
