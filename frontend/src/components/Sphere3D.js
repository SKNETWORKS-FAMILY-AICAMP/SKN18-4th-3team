import React, { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

function AnimatedSphere() {
  const meshRef = useRef();
  const colorA = useMemo(() => new THREE.Color("#ff9cf9"), []);
  const colorB = useMemo(() => new THREE.Color("#a0e7ff"), []);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime();
    meshRef.current.rotation.y = t * 0.25;
    meshRef.current.rotation.x = Math.sin(t * 0.15) * 0.2;
    const lerped = colorA.clone().lerp(colorB, (Math.sin(t) + 1) / 2);
    meshRef.current.material.color.copy(lerped);
  });

  return (
    <mesh ref={meshRef} scale={1.2}>
      <sphereGeometry args={[1, 64, 64]} />
      <meshStandardMaterial roughness={0.35} metalness={0.5} color={colorA} />
    </mesh>
  );
}

export default function Sphere3D({ onClick }) {
  return (
    <div
      style={{ width: "150px", height: "150px", cursor: "pointer" }}
      onClick={onClick}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[3, 3, 2]} intensity={1.2} />
        <pointLight position={[-4, -2, -3]} intensity={0.5} />
        <AnimatedSphere />
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>
    </div>
  );
}
