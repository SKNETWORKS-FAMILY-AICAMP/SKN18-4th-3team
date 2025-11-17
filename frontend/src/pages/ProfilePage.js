import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  getProfile,
  updateProfile,
  changePassword,
  deleteAccount,
  uploadProfileImage,
} from "../api/profile";
import { buildAbsoluteMediaUrl } from "../utils/media";
import Header from "../components/Header";
import Dashboard from "../components/Dashboard";
import "./ProfilePage.css";

function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [activeSection, setActiveSection] = useState(null); // 'username', 'password', 'delete'
  const [username, setUsername] = useState("");
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    newPasswordConfirm: "",
  });
  const [deletePassword, setDeletePassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [imageError, setImageError] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await getProfile();
      setProfile(data);
      setUsername(data.username);
      setImageError(false);
    } catch (err) {
      console.error("프로필 로드 실패:", err);
      navigate("/login");
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      await updateProfile(username);
      setSuccess("사용자명이 변경되었습니다.");
      setActiveSection(null);
      loadProfile();
    } catch (err) {
      setError(err.response?.data?.error || "사용자명 변경에 실패했습니다.");
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (passwordForm.newPassword !== passwordForm.newPasswordConfirm) {
      setError("새 비밀번호가 일치하지 않습니다.");
      return;
    }

    try {
      await changePassword(
        passwordForm.currentPassword,
        passwordForm.newPassword,
        passwordForm.newPasswordConfirm
      );
      setSuccess("비밀번호가 변경되었습니다.");
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        newPasswordConfirm: "",
      });
      setActiveSection(null);
    } catch (err) {
      setError(
        err.response?.data?.error ||
          err.response?.data?.current_password ||
          "비밀번호 변경에 실패했습니다."
      );
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    if (
      !window.confirm(
        "정말 계정을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
      )
    )
      return;

    setError("");
    try {
      await deleteAccount(deletePassword);
      alert("계정이 삭제되었습니다.");
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.error || "계정 삭제에 실패했습니다.");
    }
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError("");
    setSuccess("");
    try {
      await uploadProfileImage(file);
      setSuccess("프로필 이미지가 업로드되었습니다.");
      setImageError(false);
      loadProfile();
    } catch (err) {
      setError("이미지 업로드에 실패했습니다.");
    }
  };

  if (!profile) {
    return <div className="loading">로딩 중...</div>;
  }

  const profileImageSrc = buildAbsoluteMediaUrl(profile.profile_image);

  const menuItems = [
    { key: "username", label: "사용자명 변경" },
    { key: "password", label: "비밀번호 변경" },
    { key: "delete", label: "탈퇴하기", isDanger: true },
  ];

  const renderActiveSection = () => {
    if (!activeSection) {
      return null;
    }

    if (activeSection === "username") {
      return (
        <div className="profile-card">
          <h3 className="card-title">사용자명 변경</h3>
          <form onSubmit={handleUpdateProfile} className="settings-form">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="새로운 사용자명"
              required
            />
            <div className="button-group">
              <button type="submit" className="btn-save">
                저장
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveSection(null);
                  setUsername(profile.username);
                }}
                className="btn-cancel"
              >
                취소
              </button>
            </div>
          </form>
        </div>
      );
    }

    if (activeSection === "password") {
      return (
        <div className="profile-card">
          <h3 className="card-title">비밀번호 변경</h3>
          <form onSubmit={handleChangePassword} className="settings-form">
            <input
              type="password"
              value={passwordForm.currentPassword}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
                  currentPassword: e.target.value,
                })
              }
              placeholder="현재 비밀번호"
              required
            />
            <input
              type="password"
              value={passwordForm.newPassword}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
                  newPassword: e.target.value,
                })
              }
              placeholder="새 비밀번호"
              required
            />
            <input
              type="password"
              value={passwordForm.newPasswordConfirm}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
                  newPasswordConfirm: e.target.value,
                })
              }
              placeholder="새 비밀번호 확인"
              required
            />
            <div className="button-group">
              <button type="submit" className="btn-save">
                저장
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveSection(null);
                  setPasswordForm({
                    currentPassword: "",
                    newPassword: "",
                    newPasswordConfirm: "",
                  });
                }}
                className="btn-cancel"
              >
                취소
              </button>
            </div>
          </form>
        </div>
      );
    }

    if (activeSection === "delete") {
      return (
        <div className="profile-card danger-card">
          <h3 className="card-title">탈퇴하기</h3>
          <form onSubmit={handleDeleteAccount} className="settings-form">
            <p className="warning-text">
              계정을 삭제하면 모든 대화 내역이 영구적으로 삭제됩니다.
            </p>
            <input
              type="password"
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              placeholder="비밀번호 확인"
              required
            />
            <div className="button-group">
              <button type="submit" className="btn-delete">
                탈퇴하기
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveSection(null);
                  setDeletePassword("");
                }}
                className="btn-cancel"
              >
                취소
              </button>
            </div>
          </form>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="profile-page">
      <Header showSidebar={false} />

      <div className="profile-container">
        <div className="profile-main">
          <div className="profile-avatar-block">
            <div className="avatar-section">
              <div className="avatar-large">
                {profileImageSrc && !imageError ? (
                  <img
                    src={profileImageSrc}
                    alt="프로필"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <div className="avatar-placeholder">●</div>
                )}
              </div>
              <label className="btn-image-select">
                IMG SELECT
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  style={{ display: "none" }}
                />
              </label>
            </div>
          </div>

          <div className="profile-greeting">
            <h2>
              <span className="username">{profile.username}</span>님,
            </h2>
            <p>안녕하세요</p>
          </div>

          <nav className="profile-actions">
            {menuItems.map((item) => (
              <button
                key={item.key}
                type="button"
                className={`profile-action ${
                  activeSection === item.key ? "active" : ""
                } ${item.isDanger ? "danger" : ""}`}
                onClick={() =>
                  setActiveSection(activeSection === item.key ? null : item.key)
                }
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="profile-detail">
          {success && <div className="success-message">{success}</div>}
          {error && <div className="error-message">{error}</div>}
          {renderActiveSection()}
        </div>
      </div>

      {/* 대시보드 내용을 프로필 하단에 통합 */}
      <Dashboard />
    </div>
  );
}

export default ProfilePage;
