import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getChatInfo } from "../api/chat";
import { logout } from "../api/auth";
import { buildAbsoluteMediaUrl } from "../utils/media";
import "./Header.css";

function Header({
  showSidebar = false,
  onToggleSidebar = null,
  isSidebarOpen = false,
}) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [avatarError, setAvatarError] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadUserInfo();
  }, []);

  useEffect(() => {
    setAvatarError(false);
  }, [user?.profile_image]);

  const loadUserInfo = async () => {
    try {
      const data = await getChatInfo();
      setIsAuthenticated(data.is_authenticated);
      setUser(data.user);
    } catch (err) {
      console.error("사용자 정보 로드 실패:", err);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      // 페이지 새로고침하여 모든 상태 초기화 및 메인 페이지로 이동
      window.location.href = "/";
    } catch (err) {
      console.error("로그아웃 실패:", err);
      // 에러가 발생해도 메인 페이지로 이동
      window.location.href = "/";
    }
  };

  const avatarSrc = buildAbsoluteMediaUrl(user?.profile_image);
  const showAvatarImage = Boolean(avatarSrc) && !avatarError;
  const fallbackName = user?.username
    ? user.username
    : isAuthenticated
    ? "User"
    : "Guest";
  const userInitial = fallbackName.charAt(0).toUpperCase();

  return (
    <header className={`app-header ${isSidebarOpen ? "sidebar-open" : ""}`}>
      <div className="header-left">
        {showSidebar && onToggleSidebar && (
          <button className="sidebar-toggle-btn" onClick={onToggleSidebar}>
            ≡
          </button>
        )}
        <h1 className="header-logo" onClick={() => navigate("/")}>
          MindCare ∞
        </h1>
      </div>
      <div className="header-right">
        {isAuthenticated ? (
          <button className="btn-logout-header" onClick={handleLogout}>
            LOGOUT
          </button>
        ) : (
          <button
            className="btn-login-header"
            onClick={() => navigate("/login")}
          >
            LOGIN
          </button>
        )}
        <div
          className="user-info"
          onClick={() => isAuthenticated && navigate("/profile")}
          style={{ cursor: isAuthenticated ? "pointer" : "default" }}
        >
          <div className={`user-avatar ${showAvatarImage ? "has-image" : ""}`}>
            {showAvatarImage ? (
              <img
                src={avatarSrc}
                alt="프로필"
                onError={() => setAvatarError(true)}
              />
            ) : (
              <span>{userInitial}</span>
            )}
          </div>
          <span className="user-name">{fallbackName}</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
