import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, updateProfile, changePassword, deleteAccount, uploadProfileImage, getUserStatistics } from '../api/profile';
import './ProfilePage.css';

function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [username, setUsername] = useState('');
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    newPasswordConfirm: ''
  });
  const [deletePassword, setDeletePassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadProfile();
    loadStatistics();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
      setUsername(data.username);
    } catch (err) {
      console.error('프로필 로드 실패:', err);
      navigate('/login');
    }
  };

  const loadStatistics = async () => {
    try {
      const data = await getUserStatistics();
      setStatistics(data);
    } catch (err) {
      console.error('통계 로드 실패:', err);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await updateProfile(username);
      setSuccess('프로필이 수정되었습니다.');
      setEditMode(false);
      loadProfile();
    } catch (err) {
      setError(err.response?.data?.error || '프로필 수정에 실패했습니다.');
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (passwordForm.newPassword !== passwordForm.newPasswordConfirm) {
      setError('새 비밀번호가 일치하지 않습니다.');
      return;
    }

    try {
      await changePassword(passwordForm.currentPassword, passwordForm.newPassword, passwordForm.newPasswordConfirm);
      setSuccess('비밀번호가 변경되었습니다.');
      setPasswordForm({ currentPassword: '', newPassword: '', newPasswordConfirm: '' });
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.current_password || '비밀번호 변경에 실패했습니다.');
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    if (!window.confirm('정말 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

    setError('');
    try {
      await deleteAccount(deletePassword);
      alert('계정이 삭제되었습니다.');
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.error || '계정 삭제에 실패했습니다.');
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError('');
    setSuccess('');
    try {
      await uploadProfileImage(file);
      setSuccess('프로필 이미지가 업로드되었습니다.');
      loadProfile();
    } catch (err) {
      setError('이미지 업로드에 실패했습니다.');
    }
  };

  if (!profile) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div className="profile-page">
      <header className="profile-header">
        <h1>마이페이지</h1>
        <button onClick={() => navigate('/')} className="btn-back">채팅으로 돌아가기</button>
      </header>

      <div className="profile-container">
        {/* 프로필 정보 */}
        <section className="profile-section">
          <h2>프로필 정보</h2>
          <div className="profile-image-section">
            <img
              src={profile.profile_image || 'https://via.placeholder.com/150'}
              alt="Profile"
              className="profile-image"
            />
            <label className="btn-upload">
              이미지 변경
              <input type="file" accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} />
            </label>
          </div>

          {editMode ? (
            <form onSubmit={handleUpdateProfile}>
              <div className="form-group">
                <label>사용자명</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="button-group">
                <button type="submit" className="btn-primary">저장</button>
                <button type="button" onClick={() => {
                  setEditMode(false);
                  setUsername(profile.username);
                }} className="btn-secondary">취소</button>
              </div>
            </form>
          ) : (
            <div className="profile-info">
              <p><strong>사용자명:</strong> {profile.username}</p>
              <p><strong>이메일:</strong> {profile.email}</p>
              <p><strong>가입일:</strong> {new Date(profile.created_at).toLocaleDateString()}</p>
              <button onClick={() => setEditMode(true)} className="btn-primary">수정</button>
            </div>
          )}

          {success && <div className="success-message">{success}</div>}
          {error && <div className="error-message">{error}</div>}
        </section>

        {/* 통계 */}
        {statistics && (
          <section className="profile-section">
            <h2>대화 통계</h2>
            <div className="statistics-grid">
              <div className="stat-card">
                <h3>주간</h3>
                <p>{statistics.weekly.conversations}개 대화</p>
                <p>{statistics.weekly.messages}개 메시지</p>
              </div>
              <div className="stat-card">
                <h3>월간</h3>
                <p>{statistics.monthly.conversations}개 대화</p>
                <p>{statistics.monthly.messages}개 메시지</p>
              </div>
              <div className="stat-card">
                <h3>전체</h3>
                <p>{statistics.total.conversations}개 대화</p>
                <p>{statistics.total.messages}개 메시지</p>
              </div>
            </div>
          </section>
        )}

        {/* 비밀번호 변경 */}
        <section className="profile-section">
          <h2>비밀번호 변경</h2>
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label>현재 비밀번호</label>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>새 비밀번호</label>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>새 비밀번호 확인</label>
              <input
                type="password"
                value={passwordForm.newPasswordConfirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPasswordConfirm: e.target.value })}
                required
              />
            </div>
            <button type="submit" className="btn-primary">비밀번호 변경</button>
          </form>
        </section>

        {/* 계정 삭제 */}
        <section className="profile-section danger-section">
          <h2>계정 삭제</h2>
          <p className="warning-text">계정을 삭제하면 모든 대화 내역이 영구적으로 삭제됩니다.</p>
          <form onSubmit={handleDeleteAccount}>
            <div className="form-group">
              <label>비밀번호 확인</label>
              <input
                type="password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                placeholder="비밀번호를 입력하세요"
                required
              />
            </div>
            <button type="submit" className="btn-danger">계정 삭제</button>
          </form>
        </section>
      </div>
    </div>
  );
}

export default ProfilePage;
