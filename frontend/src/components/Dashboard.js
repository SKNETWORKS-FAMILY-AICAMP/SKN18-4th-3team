import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  getKpiData,
  getConversationFrequency,
  getHourlyPattern,
  getSentimentDistribution,
  getEmotionKeywords,
  getTopDiseases,
} from "../api/profile";
import "./Dashboard.css";

function Dashboard() {
  const [kpiData, setKpiData] = useState(null);
  const [conversationFrequency, setConversationFrequency] = useState(null);
  const [hourlyPattern, setHourlyPattern] = useState(null);
  const [sentimentDistribution, setSentimentDistribution] = useState(null);
  const [emotionKeywords, setEmotionKeywords] = useState(null);
  const [topDiseases, setTopDiseases] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const location = useLocation();

  // 페이지가 보일 때마다 데이터 새로고침 (대화 후 대시보드로 돌아올 때 반영)
  useEffect(() => {
    loadDashboardData();
  }, [location.pathname]);

  // 페이지 포커스 시에도 데이터 새로고침 (다른 탭에서 돌아올 때)
  useEffect(() => {
    const handleFocus = () => {
      loadDashboardData();
    };
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError("");
    try {
      const [kpi, frequency, hourly, sentiment, keywords, diseases] =
        await Promise.all([
          getKpiData(),
          getConversationFrequency(),
          getHourlyPattern(),
          getSentimentDistribution(),
          getEmotionKeywords(),
          getTopDiseases(),
        ]);

      setKpiData(kpi);
      setConversationFrequency(frequency);
      setHourlyPattern(hourly);
      setSentimentDistribution(sentiment);
      setEmotionKeywords(keywords);
      setTopDiseases(diseases);
    } catch (err) {
      console.error("대시보드 데이터 로드 실패:", err);
      setError("대시보드 데이터를 불러오는데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="dashboard-loading">로딩 중...</div>;
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  return (
    <div className="dashboard">
      <h2 className="dashboard-title">나의 대화 통계</h2>

      {/* KPI 카드 */}
      <div className="kpi-section">
        <div className="kpi-card">
          <h3>총 대화 횟수</h3>
          <p className="kpi-value">{kpiData?.total_conversations || 0}</p>
        </div>
        <div className="kpi-card">
          <h3>총 메시지 수</h3>
          <p className="kpi-value">{kpiData?.total_messages || 0}</p>
        </div>
      </div>

      {/* 차트 그리드 */}
      <div className="charts-grid">
        {/* 1. 대화 빈도 (라인 차트) */}
        <div className="chart-card">
          <LineChart data={conversationFrequency} />
        </div>

        {/* 2. 감정 분포 (파이 차트) */}
        <div className="chart-card">
          <h3>감정 분포</h3>
          <PieChart data={sentimentDistribution} />
        </div>

        {/* 3. 시간대별 패턴 (히트맵) */}
        <div className="chart-card full-width">
          <h3>시간대별 대화 패턴</h3>
          <HeatmapChart data={hourlyPattern} />
        </div>

        {/* 4. 감정 키워드 (워드 클라우드) */}
        <div className="chart-card">
          <h3>감정 키워드</h3>
          <KeywordsCloud data={emotionKeywords} />
        </div>

        {/* 5. 자주 검색한 질환 TOP 10 (바 차트) */}
        <div className="chart-card">
          <h3>자주 검색한 질환 TOP 10</h3>
          <BarChart data={topDiseases} />
        </div>
      </div>
    </div>
  );
}

// 간단한 라인 차트 컴포넌트 (Recharts 없이 SVG로 구현)
function LineChart({ data }) {
  if (!data || !data.labels || !data.values) return <div>데이터 없음</div>;

  const width = 400;
  const height = 200;
  const padding = 40;
  const maxValue = Math.max(...data.values, 1);

  const points = data.values
    .map((value, index) => {
      const x =
        padding + (index / (data.values.length - 1)) * (width - 2 * padding);
      const y = height - padding - (value / maxValue) * (height - 2 * padding);
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline points={points} fill="none" stroke="#fca5f1" strokeWidth="2" />
      {data.values.map((value, index) => {
        const x =
          padding + (index / (data.values.length - 1)) * (width - 2 * padding);
        const y =
          height - padding - (value / maxValue) * (height - 2 * padding);
        return (
          <g key={index}>
            <circle cx={x} cy={y} r="4" fill="#fca5f1" />
            <text
              x={x}
              y={y - 10}
              textAnchor="middle"
              fontSize="12"
              fill="#666"
            >
              {value}
            </text>
          </g>
        );
      })}
      {data.labels.map((label, index) => {
        const x =
          padding + (index / (data.labels.length - 1)) * (width - 2 * padding);
        return (
          <text
            key={index}
            x={x}
            y={height - 10}
            textAnchor="middle"
            fontSize="12"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}

// 간단한 파이 차트 컴포넌트
function PieChart({ data }) {
  if (!data || !data.labels || !data.values) return <div>데이터 없음</div>;

  const colors = ["#fca5f1", "#F44336", "#FFC107"];
  const actualTotal = data.values.reduce((sum, value) => sum + value, 0);
  const hasData = actualTotal > 0;
  const displayValues = hasData
    ? data.values
    : Array.from({ length: data.labels.length }, () => 1);
  const totalForSvg = displayValues.reduce((sum, value) => sum + value, 0) || 1;
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  let cumulativeFraction = 0;

  return (
    <div className="pie-chart-container">
      <svg
        width="200"
        height="200"
        viewBox="0 0 200 200"
        className="pie-chart-svg"
      >
        {displayValues.map((value, index) => {
          const fraction = value / totalForSvg;
          const dashLength = fraction * circumference;
          const gapLength = Math.max(circumference - dashLength, 0);
          const offset = cumulativeFraction * circumference;
          cumulativeFraction += fraction;
          const dashArray = `${dashLength} ${gapLength}`;

          return (
            <circle
              key={index}
              cx="100"
              cy="100"
              r={radius}
              fill="transparent"
              stroke={colors[index]}
              strokeWidth="40"
              strokeDasharray={dashArray}
              strokeDashoffset={-offset}
              transform="rotate(-90 100 100)"
            />
          );
        })}
        {!hasData && (
          <circle cx="100" cy="100" r={radius - 35} fill="#f8f8f8" stroke="#eee" />
        )}
      </svg>
      <div className="pie-legend">
        {data.labels.map((label, index) => {
          const percentage = hasData && actualTotal > 0
            ? ((data.values[index] / actualTotal) * 100).toFixed(1)
            : "0.0";

          return (
            <div key={index} className="legend-item">
              <span
                className="legend-color"
                style={{ backgroundColor: colors[index] }}
              ></span>
              <span>
                {label}: {percentage}%
              </span>
            </div>
          );
        })}
        {!hasData && <div className="pie-no-data">감정 분석 데이터가 없습니다.</div>}
      </div>
    </div>
  );
}

// 히트맵 차트
function HeatmapChart({ data }) {
  if (!data || !data.heatmap_data) return <div>데이터 없음</div>;

  const maxValue = Math.max(...data.heatmap_data.flat(), 1);
  const cellSize = 30;

  return (
    <div className="heatmap-container">
      <svg
        width={data.hours.length * cellSize + 60}
        height={data.weekdays.length * cellSize + 40}
      >
        {/* Y축 레이블 (요일) */}
        {data.weekdays.map((day, dayIndex) => (
          <text
            key={`day-${dayIndex}`}
            x="30"
            y={dayIndex * cellSize + 50}
            textAnchor="end"
            fontSize="12"
          >
            {day}
          </text>
        ))}

        {/* 히트맵 셀 */}
        {data.heatmap_data.map((row, dayIndex) =>
          row.map((value, hourIndex) => {
            const intensity = value / maxValue;
            const color = `rgba(252, 165, 241, ${intensity})`;
            return (
              <rect
                key={`${dayIndex}-${hourIndex}`}
                x={40 + hourIndex * cellSize}
                y={30 + dayIndex * cellSize}
                width={cellSize - 2}
                height={cellSize - 2}
                fill={color}
                stroke="#ddd"
              />
            );
          })
        )}

        {/* X축 레이블 (시간) - 3시간 간격 */}
        {data.hours
          .filter((_, i) => i % 3 === 0)
          .map((hour, index) => (
            <text
              key={`hour-${hour}`}
              x={40 + hour * cellSize + cellSize / 2}
              y="20"
              textAnchor="middle"
              fontSize="10"
            >
              {hour}h
            </text>
          ))}
      </svg>
    </div>
  );
}

// 키워드 클라우드 (단순 버전)
function KeywordsCloud({ data }) {
  if (!data || !data.keywords || data.keywords.length === 0) {
    return <div>데이터 없음</div>;
  }

  const maxCount = Math.max(...data.keywords.map((k) => k.count), 1);

  return (
    <div className="keywords-cloud">
      {data.keywords.map((keyword, index) => {
        const fontSize = 12 + (keyword.count / maxCount) * 20;
        const color =
          keyword.sentiment === "positive"
            ? "#fca5f1"
            : keyword.sentiment === "negative"
            ? "#F44336"
            : "#FFC107";
        return (
          <span
            key={index}
            className="keyword-item"
            style={{ fontSize: `${fontSize}px`, color }}
          >
            {keyword.text}
          </span>
        );
      })}
    </div>
  );
}

// 바 차트
function BarChart({ data }) {
  if (!data || !data.labels || !data.values) return <div>데이터 없음</div>;
  if (data.values.length === 0) return <div>데이터 없음</div>;

  const maxValue = Math.max(...data.values, 1);
  const barHeight = 30;
  const height = data.labels.length * barHeight + 40;

  return (
    <svg width="100%" height={height} viewBox={`0 0 400 ${height}`}>
      {data.labels.map((label, index) => {
        const barWidth = (data.values[index] / maxValue) * 300;
        const y = index * barHeight + 20;

        return (
          <g key={index}>
            <text x="10" y={y + 20} fontSize="12">
              {label}
            </text>
            <rect
              x="120"
              y={y + 5}
              width={barWidth}
              height={barHeight - 10}
              fill="#fca5f1"
            />
            <text x={130 + barWidth} y={y + 20} fontSize="12">
              {data.values[index]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default Dashboard;
