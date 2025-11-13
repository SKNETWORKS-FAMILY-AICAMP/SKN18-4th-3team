import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signup, checkEmail } from '../api/auth';
import './SignupPage.css';

function SignupPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    username: '',
    profileImage: null,
    email: '',
    password: '',
    passwordConfirm: ''
  });
  const [emailAvailable, setEmailAvailable] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e) => {
    setFormData(prev => ({ ...prev, profileImage: e.target.files[0] }));
  };

  const handleEmailCheck = async () => {
    if (!formData.email) {
      setError('이메일을 입력해주세요.');
      return;
    }
    try {
      const data = await checkEmail(formData.email);
      setEmailAvailable(data.available);
      setError(data.available ? '' : data.message);
    } catch (err) {
      setError('이메일 확인 중 오류가 발생했습니다.');
    }
  };

  const handleStep1 = (e) => {
    e.preventDefault();
    if (!formData.username) {
      setError('사용자명을 입력해주세요.');
      return;
    }
    setError('');
    setStep(2);
  };

  const handleStep2 = (e) => {
    e.preventDefault();
    if (!emailAvailable) {
      setError('이메일 중복 확인을 해주세요.');
      return;
    }
    if (!formData.password || !formData.passwordConfirm) {
      setError('비밀번호를 입력해주세요.');
      return;
    }
    if (formData.password !== formData.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }
    setError('');
    setStep(3);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const signupData = new FormData();
      signupData.append('username', formData.username);
      signupData.append('email', formData.email);
      signupData.append('password', formData.password);
      signupData.append('password_confirm', formData.passwordConfirm);
      if (formData.profileImage) {
        signupData.append('profile_image', formData.profileImage);
      }

      const data = await signup(signupData);
      console.log('회원가입 성공:', data);
      navigate('/');  // 메인 채팅 페이지로 이동
    } catch (err) {
      setError(err.response?.data?.error || '회원가입에 실패했습니다.');
      setStep(2);  // 오류 시 2단계로 돌아가기
    }
  };

  return (
    <div className="signup-container">
      <div className="signup-box">
        <h1>MindCare</h1>
        <h2>회원가입</h2>
        <div className="step-indicator">
          <span className={step >= 1 ? 'active' : ''}>1</span>
          <span className={step >= 2 ? 'active' : ''}>2</span>
          <span className={step >= 3 ? 'active' : ''}>3</span>
        </div>

        {step === 1 && (
          <form onSubmit={handleStep1}>
            <div className="form-group">
              <label>사용자명 *</label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                placeholder="사용자명을 입력하세요"
                required
              />
            </div>
            <div className="form-group">
              <label>프로필 이미지 (선택)</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn-primary">다음</button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleStep2}>
            <div className="form-group">
              <label>이메일 *</label>
              <div className="email-check-group">
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={(e) => {
                    handleInputChange(e);
                    setEmailAvailable(null);
                  }}
                  placeholder="이메일을 입력하세요"
                  required
                />
                <button type="button" onClick={handleEmailCheck} className="btn-check">
                  중복확인
                </button>
              </div>
              {emailAvailable === true && <div className="success-message">사용 가능한 이메일입니다.</div>}
              {emailAvailable === false && <div className="error-message">이미 사용 중인 이메일입니다.</div>}
            </div>
            <div className="form-group">
              <label>비밀번호 *</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="비밀번호를 입력하세요"
                required
              />
            </div>
            <div className="form-group">
              <label>비밀번호 확인 *</label>
              <input
                type="password"
                name="passwordConfirm"
                value={formData.passwordConfirm}
                onChange={handleInputChange}
                placeholder="비밀번호를 다시 입력하세요"
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="button-group">
              <button type="button" onClick={() => setStep(1)} className="btn-secondary">이전</button>
              <button type="submit" className="btn-primary">다음</button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleSubmit}>
            <div className="signup-summary">
              <h3>가입 정보 확인</h3>
              <p><strong>사용자명:</strong> {formData.username}</p>
              <p><strong>이메일:</strong> {formData.email}</p>
              {formData.profileImage && <p><strong>프로필 이미지:</strong> {formData.profileImage.name}</p>}
            </div>
            {error && <div className="error-message">{error}</div>}
            <div className="button-group">
              <button type="button" onClick={() => setStep(2)} className="btn-secondary">이전</button>
              <button type="submit" className="btn-primary">회원가입 완료</button>
            </div>
          </form>
        )}

        <div className="signup-footer">
          <p>이미 계정이 있으신가요? <Link to="/login">로그인</Link></p>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
