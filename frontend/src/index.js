import React from "react";
import ReactDOM from "react-dom/client";
import "./styles/common.css";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";
import { forceReloadFavicon } from "./utils/favicon";

// 페이지 로드 시 파비콘 강제 재로드
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", forceReloadFavicon);
} else {
  forceReloadFavicon();
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
