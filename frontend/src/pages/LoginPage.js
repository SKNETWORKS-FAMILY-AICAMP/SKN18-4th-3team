import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import Header from '../components/Header';
import './LoginPage.css';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || '로그인에 실패했습니다.');
    }
  };

  return (
    <div className="login-page">
      {/* Header - 페이지 최상단 고정 */}
      <Header showSidebar={false} />

      {/* Main Content - 헤더 아래 중앙 배치 */}
      <main className="login-main">
        <div className="login-container">
          <div className="login-box">
            <form onSubmit={handleLogin} className="login-form">
              <div className="form-group">
                <label>EMAIL</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label>PWD</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {error && <div className="error-message">{error}</div>}
              <div className="button-group">
                <button type="submit" className="btn-login">LOGIN</button>
                <button type="button" className="btn-signup" onClick={() => navigate('/signup')}>
                  SIGNUP
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default LoginPage;
