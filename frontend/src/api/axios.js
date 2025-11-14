import axios from "axios";

// Django API URL 설정
// 환경변수에서만 읽기 (하드코딩 없음)
const DJANGO_HOST = process.env.REACT_APP_DJANGO_HOST;
const DJANGO_PORT = process.env.REACT_APP_DJANGO_PORT;
const API_URL = `http://${DJANGO_HOST}:${DJANGO_PORT}`;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // 세션 쿠키 자동 전송
  headers: {
    "Content-Type": "application/json",
  },
});

// CSRF 토큰 가져오기 함수
const getCookie = (name) => {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

// 요청 인터셉터: CSRF 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      config.headers["X-CSRFToken"] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 인증 오류 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // 인증 오류 시 로그인 페이지로 리다이렉트
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
