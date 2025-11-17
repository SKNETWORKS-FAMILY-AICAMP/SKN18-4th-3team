import React, { useEffect, useRef } from "react";
import "./Sphere2D.css";

export default function Sphere2D({ onClick }) {
  const canvasRef = useRef(null);
  const timeRef = useRef(0);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    function resizeCanvas() {
      const container = canvas.parentElement;
      const size = container.offsetWidth;
      canvas.width = size * window.devicePixelRatio;
      canvas.height = size * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    function animate() {
      const width = canvas.width / window.devicePixelRatio;
      const height = canvas.height / window.devicePixelRatio;
      const centerX = width / 2;
      const centerY = height / 2;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Background
      ctx.fillStyle = "#f7f7f8";
      ctx.fillRect(0, 0, width, height);

      // Orbit parameters - 각 원마다 다른 중심과 반지름
      const baseBlobRadius = width * 0.35;

      // 첫 번째 원의 기본 궤도 중심 (왼쪽 위쪽)
      const baseOrbitCenterX1 = centerX - width * 0.08;
      const baseOrbitCenterY1 = centerY - width * 0.06;
      const baseOrbitRadius1 = width * 0.08; // 궤도 반지름 줄임

      // 두 번째 원의 기본 궤도 중심 (오른쪽 아래쪽)
      const baseOrbitCenterX2 = centerX + width * 0.09;
      const baseOrbitCenterY2 = centerY + width * 0.08;
      const baseOrbitRadius2 = width * 0.12; // 궤도 반지름 줄임

      // 궤도 중심 변화 (첫 번째는 위아래, 두 번째는 좌우, 타이밍 엇나가게)
      const centerVariation = width * 0.03; // 중심 변화 폭 (3%)
      const centerSpeed1 = 0.5; // 첫 번째 원의 중심 변화 속도 (위아래)
      const centerSpeed2 = 0.3; // 두 번째 원의 중심 변화 속도 (좌우)
      const centerPhaseOffset = Math.PI * 0.7; // 타이밍을 엇나가게 하는 phase offset

      // 첫 번째 원: 위아래로 움직임 (Y축만 변화)
      const orbitCenterX1 = baseOrbitCenterX1;
      const orbitCenterY1 =
        baseOrbitCenterY1 +
        Math.sin(timeRef.current * centerSpeed1) * centerVariation;

      // 두 번째 원: 좌우로 움직임 (X축만 변화, 타이밍 엇나가게)
      const orbitCenterX2 =
        baseOrbitCenterX2 +
        Math.cos(timeRef.current * centerSpeed2 + centerPhaseOffset) *
          centerVariation;
      const orbitCenterY2 = baseOrbitCenterY2;

      // 궤도 반지름을 짧은 범위 내에서 변화 (각 원마다 다른 주기)
      const orbitVariation1 = 0.09; // 변화 폭 (8%)
      const orbitVariation2 = 0.12; // 변화 폭 (10%)
      const orbitSpeed1 = 0.6; // 첫 번째 원의 궤도 반지름 변화 속도
      const orbitSpeed2 = 0.4; // 두 번째 원의 궤도 반지름 변화 속도

      const orbitRadius1 =
        baseOrbitRadius1 *
        (1 + Math.sin(timeRef.current * orbitSpeed1) * orbitVariation1);
      const orbitRadius2 =
        baseOrbitRadius2 *
        (1 + Math.cos(timeRef.current * orbitSpeed2) * orbitVariation2);

      // Calculate positions (속도 조정)
      const angle1 = timeRef.current * 1.8;
      const angle2 = -timeRef.current * 2.4 + Math.PI;

      const x1 = orbitCenterX1 + Math.cos(angle1) * orbitRadius1;
      const y1 = orbitCenterY1 + Math.sin(angle1) * orbitRadius1;

      const x2 = orbitCenterX2 + Math.cos(angle2) * orbitRadius2;
      const y2 = orbitCenterY2 + Math.sin(angle2) * orbitRadius2;

      // 원의 크기를 시간에 따라 불규칙적으로 변화 (각 원마다 다른 주기)
      const sizeVariation1 = 0.15; // 변화 폭 (15%)
      const sizeVariation2 = 0.2; // 변화 폭 (20%)
      const speed1 = 1.2; // 첫 번째 원의 크기 변화 속도
      const speed2 = 0.8; // 두 번째 원의 크기 변화 속도
      const phaseOffset = Math.PI * 0.6; // 타이밍을 엇나가게 하는 phase offset (약 60도)

      // 타원 비율 (1.0이면 완전한 원, 1.0이 아니면 타원)
      const ellipseRatio1X = 1.0 + Math.sin(timeRef.current * 0.5) * 0.15; // X축 변화
      const ellipseRatio1Y = 1.0 + Math.cos(timeRef.current * 0.7) * 0.15; // Y축 변화
      const ellipseRatio2X = 1.0 + Math.sin(timeRef.current * 0.6) * 0.2;
      const ellipseRatio2Y = 1.0 + Math.cos(timeRef.current * 0.4) * 0.2;

      const blobRadius1 =
        baseBlobRadius *
        (1 + Math.sin(timeRef.current * speed1) * sizeVariation1);
      const blobRadius2 =
        baseBlobRadius *
        (1 + Math.cos(timeRef.current * speed2 + phaseOffset) * sizeVariation2);

      // Sky blue blob (타원형) - 메인 컬러 #6dd5fa 계열
      ctx.save();
      ctx.translate(x1, y1);
      ctx.scale(ellipseRatio1X, ellipseRatio1Y);
      // 그림자 효과 추가 (더 부드러운 페이드 아웃)
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
        blobRadius1
      );
      skyBlueGradient.addColorStop(0, "rgba(109, 213, 250, 0.9)"); // #6dd5fa, 더 진하게
      skyBlueGradient.addColorStop(0.5, "rgba(109, 213, 250, 0.65)"); // 중간 부분도 더 진하게
      skyBlueGradient.addColorStop(0.65, "rgba(109, 213, 250, 0.4)"); // 경계 시작
      skyBlueGradient.addColorStop(0.8, "rgba(109, 213, 250, 0.2)"); // 부드러운 페이드
      skyBlueGradient.addColorStop(0.9, "rgba(109, 213, 250, 0.1)"); // 더 부드러운 페이드
      skyBlueGradient.addColorStop(1, "rgba(109, 213, 250, 0)");
      ctx.fillStyle = skyBlueGradient;
      ctx.fillRect(-width, -height, width * 2, height * 2);
      ctx.restore();

      // Pink blob (타원형) - 메인 컬러 #fca5f1 계열
      ctx.save();
      ctx.translate(x2, y2);
      ctx.scale(ellipseRatio2X, ellipseRatio2Y);
      // 그림자 효과 추가 (더 부드러운 페이드 아웃)
      ctx.shadowBlur = 30;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;
      ctx.shadowColor = "rgba(252, 165, 241, 0.3)";
      const pinkGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, blobRadius2);
      pinkGradient.addColorStop(0, "rgba(252, 165, 241, 0.9)"); // #fca5f1, 더 진하게
      pinkGradient.addColorStop(0.5, "rgba(252, 165, 241, 0.65)"); // 중간 부분도 더 진하게
      pinkGradient.addColorStop(0.65, "rgba(252, 165, 241, 0.4)"); // 경계 시작
      pinkGradient.addColorStop(0.8, "rgba(252, 165, 241, 0.2)"); // 부드러운 페이드
      pinkGradient.addColorStop(0.9, "rgba(252, 165, 241, 0.1)"); // 더 부드러운 페이드
      pinkGradient.addColorStop(1, "rgba(252, 165, 241, 0)");
      ctx.fillStyle = pinkGradient;
      ctx.fillRect(-width, -height, width * 2, height * 2);
      ctx.restore();

      timeRef.current += 0.01;
      animationFrameRef.current = requestAnimationFrame(animate);
    }

    // Start animation after a delay
    const timeout = setTimeout(() => {
      animate();
    }, 500);

    return () => {
      clearTimeout(timeout);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  return (
    <div className="sphere2d-container" onClick={onClick}>
      <div className="sphere2d">
        <div className="sphere2d-canvas-wrapper">
          <canvas ref={canvasRef} id="sphere-canvas"></canvas>
        </div>
        <div className="sphere2d-glass"></div>
      </div>
    </div>
  );
}
