import api from './axios';

// 프로필 조회
export const getProfile = async () => {
  const response = await api.get('/profiles/');
  return response.data;
};

// 프로필 업데이트
export const updateProfile = async (username) => {
  const response = await api.put('/profiles/update/', { username });
  return response.data;
};

// 비밀번호 변경
export const changePassword = async (currentPassword, newPassword, newPasswordConfirm) => {
  const response = await api.put('/profiles/password/', {
    current_password: currentPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm
  });
  return response.data;
};

// 계정 삭제
export const deleteAccount = async (password) => {
  const response = await api.delete('/profiles/delete/', { data: { password } });
  return response.data;
};

// 프로필 이미지 업로드
export const uploadProfileImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('profile_image', imageFile);
  const response = await api.post('/profiles/upload-image/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// 사용자 통계 조회
export const getUserStatistics = async () => {
  const response = await api.get('/profiles/statistics/');
  return response.data;
};
