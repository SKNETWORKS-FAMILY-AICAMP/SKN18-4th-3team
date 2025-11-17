import React, { useEffect, useRef } from "react";
import "./SphereAvatar.css";

// 정적 Sphere 아바타 (애니메이션 없음)
export default function SphereAvatar({ size = 40 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const pixelRatio = window.devicePixelRatio || 1;
    const canvasSize = size * pixelRatio;

    canvas.width = canvasSize;
    canvas.height = canvasSize;
    ctx.scale(pixelRatio, pixelRatio);

    const centerX = size / 2;
    const centerY = size / 2;
    const baseBlobRadius = size * 0.35;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Background
    ctx.fillStyle = "#f7f7f8";
    ctx.fillRect(0, 0, size, size);

    // 첫 번째 원의 위치 (왼쪽 위쪽)
    const orbitCenterX1 = centerX - size * 0.08;
    const orbitCenterY1 = centerY - size * 0.06;
    const orbitRadius1 = size * 0.08;
    const angle1 = 0; // 정적 위치
    const x1 = orbitCenterX1 + Math.cos(angle1) * orbitRadius1;
    const y1 = orbitCenterY1 + Math.sin(angle1) * orbitRadius1;

    // 두 번째 원의 위치 (오른쪽 아래쪽)
    const orbitCenterX2 = centerX + size * 0.09;
    const orbitCenterY2 = centerY + size * 0.08;
    const orbitRadius2 = size * 0.12;
    const angle2 = Math.PI; // 정적 위치
    const x2 = orbitCenterX2 + Math.cos(angle2) * orbitRadius2;
    const y2 = orbitCenterY2 + Math.sin(angle2) * orbitRadius2;

    // Sky blue blob
    ctx.save();
    ctx.translate(x1, y1);
    ctx.shadowBlur = 30;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    ctx.shadowColor = "rgba(109, 213, 250, 0.3)";
    const skyBlueGradient = ctx.createRadialGradient(
      0,
      0,
      0,
      0,
      0,
      baseBlobRadius
    );
    skyBlueGradient.addColorStop(0, "rgba(109, 213, 250, 0.9)");
    skyBlueGradient.addColorStop(0.5, "rgba(109, 213, 250, 0.65)");
    skyBlueGradient.addColorStop(0.65, "rgba(109, 213, 250, 0.4)");
    skyBlueGradient.addColorStop(0.8, "rgba(109, 213, 250, 0.2)");
    skyBlueGradient.addColorStop(0.9, "rgba(109, 213, 250, 0.1)");
    skyBlueGradient.addColorStop(1, "rgba(109, 213, 250, 0)");
    ctx.fillStyle = skyBlueGradient;
    ctx.fillRect(-size, -size, size * 2, size * 2);
    ctx.restore();

    // Pink blob
    ctx.save();
    ctx.translate(x2, y2);
    ctx.shadowBlur = 30;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    ctx.shadowColor = "rgba(252, 165, 241, 0.3)";
    const pinkGradient = ctx.createRadialGradient(
      0,
      0,
      0,
      0,
      0,
      baseBlobRadius
    );
    pinkGradient.addColorStop(0, "rgba(252, 165, 241, 0.9)");
    pinkGradient.addColorStop(0.5, "rgba(252, 165, 241, 0.65)");
    pinkGradient.addColorStop(0.65, "rgba(252, 165, 241, 0.4)");
    pinkGradient.addColorStop(0.8, "rgba(252, 165, 241, 0.2)");
    pinkGradient.addColorStop(0.9, "rgba(252, 165, 241, 0.1)");
    pinkGradient.addColorStop(1, "rgba(252, 165, 241, 0)");
    ctx.fillStyle = pinkGradient;
    ctx.fillRect(-size, -size, size * 2, size * 2);
    ctx.restore();

    // Glass effect
    ctx.save();
    ctx.fillStyle = "rgba(255, 255, 255, 0.05)";
    ctx.fillRect(0, 0, size, size);
    ctx.restore();
  }, [size]);

  return (
    <div
      className="sphere-avatar-container"
      style={{ width: size, height: size }}
    >
      <canvas
        ref={canvasRef}
        className="sphere-avatar-canvas"
        style={{ width: size, height: size }}
      />
      <div
        className="sphere-avatar-glass"
        style={{ width: size, height: size }}
      />
    </div>
  );
}

