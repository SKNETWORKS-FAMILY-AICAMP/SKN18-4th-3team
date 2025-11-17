import api from "./axios";

// 회원가입
export const signup = async (userData) => {
  const config =
    typeof FormData !== "undefined" && userData instanceof FormData
      ? { headers: { "Content-Type": "multipart/form-data" } }
      : undefined;

  const response = await api.post("/users/signup/", userData, config);
  return response.data;
};

// 이메일 중복 체크
export const checkEmail = async (email) => {
  const response = await api.post("/users/signup/check-email/", { email });
  return response.data;
};

// 로그인
export const login = async (email, password) => {
  const response = await api.post("/users/login/", { email, password });
  return response.data;
};

// 로그아웃
export const logout = async () => {
  const response = await api.post("/users/logout/");
  return response.data;
};
