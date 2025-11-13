import api from './axios';

// 회원가입
export const signup = async (userData) => {
  const response = await api.post('/users/signup/', userData);
  return response.data;
};

// 이메일 중복 체크
export const checkEmail = async (email) => {
  const response = await api.post('/users/signup/check-email/', { email });
  return response.data;
};

// 로그인
export const login = async (email, password) => {
  const response = await api.post('/users/login/', { email, password });
  return response.data;
};

// 로그아웃
export const logout = async () => {
  const response = await api.post('/users/logout/');
  return response.data;
};
