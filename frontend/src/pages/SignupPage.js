import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { signup, checkEmail } from "../api/auth";
import Header from "../components/Header";
import "./SignupPage.css";

function SignupPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    username: "",
    profileImage: null,
    profileImagePreview: null,
    email: "",
    password: "",
    passwordConfirm: "",
  });
  const [validation, setValidation] = useState({
    email: false,
    password: false,
    passwordConfirm: false,
  });
  const [emailStatus, setEmailStatus] = useState("idle"); // idle | invalid | checking | available | taken | error
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // 실시간 검증
    if (name === "email") {
      setEmailStatus("idle");
    } else if (name === "password") {
      setValidation((prev) => ({
        ...prev,
        password: value.length >= 8,
        passwordConfirm: formData.passwordConfirm === value,
      }));
    } else if (name === "passwordConfirm") {
      setValidation((prev) => ({
        ...prev,
        passwordConfirm: formData.password === value,
      }));
    }
  };

  useEffect(() => {
    if (!formData.email) {
      setValidation((prev) => ({ ...prev, email: false }));
      setEmailStatus("idle");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setValidation((prev) => ({ ...prev, email: false }));
      setEmailStatus("invalid");
      return;
    }

    let isMounted = true;
    setEmailStatus("checking");

    const timer = setTimeout(async () => {
      try {
        const result = await checkEmail(formData.email);
        if (!isMounted) return;
        if (result.available) {
          setValidation((prev) => ({ ...prev, email: true }));
          setEmailStatus("available");
        } else {
          setValidation((prev) => ({ ...prev, email: false }));
          setEmailStatus("taken");
        }
      } catch (err) {
        if (!isMounted) return;
        setValidation((prev) => ({ ...prev, email: false }));
        setEmailStatus("error");
        console.error("이메일 중복 확인 실패:", err);
      }
    }, 400);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [formData.email]);

  useEffect(() => {
    if (emailStatus === "available" && error) {
      setError("");
    }
  }, [emailStatus, error]);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setFormData((prev) => ({
          ...prev,
          profileImage: file,
          profileImagePreview: reader.result,
        }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleStep1 = (e) => {
    e.preventDefault();
    if (!formData.username) {
      setError("사용자명을 입력해주세요.");
      return;
    }
    setError("");
    setStep(2);
  };

  const handleStep2 = (e) => {
    e.preventDefault();
    if (emailStatus !== "available") {
      if (emailStatus === "invalid") {
        setError("올바른 이메일 형식을 입력해주세요.");
      } else if (emailStatus === "taken") {
        setError("이미 사용 중인 이메일입니다.");
      } else if (emailStatus === "checking") {
        setError("이메일 중복 확인 중입니다. 잠시 후 다시 시도해주세요.");
      } else {
        setError("이메일 확인에 실패했습니다. 다시 시도해주세요.");
      }
      return;
    }
    if (!validation.password) {
      setError("비밀번호는 최소 8자 이상이어야 합니다.");
      return;
    }
    if (!validation.passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    setError("");
    setStep(3);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const signupData = new FormData();
      signupData.append("username", formData.username);
      signupData.append("email", formData.email);
      signupData.append("password", formData.password);
      signupData.append("password_confirm", formData.passwordConfirm);
      if (formData.profileImage) {
        signupData.append("profile_image", formData.profileImage);
      }

      const data = await signup(signupData);
      console.log("회원가입 성공:", data);
      navigate("/"); // 메인 채팅 페이지로 이동
    } catch (err) {
      setError(err.response?.data?.error || "회원가입에 실패했습니다.");
      setStep(2); // 오류 시 2단계로 돌아가기
    }
  };

  return (
    <div className="signup-page">
      <Header showSidebar={false} />

      <div className="signup-container">
        <div className="signup-box">
          <div className="step-indicator">
            <span className={step >= 1 ? "active" : ""}>1</span>
            <span className={step >= 2 ? "active" : ""}>2</span>
            <span className={step >= 3 ? "active" : ""}>3</span>
          </div>

          {step === 1 && (
            <form onSubmit={handleStep1}>
              <div className="avatar-section">
                <div className="avatar-preview">
                  {formData.profileImagePreview ? (
                    <img src={formData.profileImagePreview} alt="프로필" />
                  ) : (
                    <div className="avatar-placeholder">●</div>
                  )}
                </div>
                <label className="btn-image-select">
                  IMG SELECT
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    style={{ display: "none" }}
                  />
                </label>
              </div>
              <div className="form-group">
                <label>UserName</label>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                />
              </div>
              {error && <div className="error-message">{error}</div>}
              <button type="submit" className="btn-next">
                NEXT
              </button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleStep2}>
              <div className="form-group">
                <div className="input-with-check">
                  <label>EMAIL</label>
                  {emailStatus === "available" && (
                    <span className="check-icon">✓</span>
                  )}
                </div>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
                {emailStatus === "taken" && (
                  <p className="field-message error">
                    이미 사용 중인 이메일입니다.
                  </p>
                )}
                {emailStatus === "invalid" && formData.email && (
                  <p className="field-message error">
                    이메일 형식을 확인해주세요.
                  </p>
                )}
                {emailStatus === "error" && (
                  <p className="field-message error">
                    이메일 확인 중 문제가 발생했습니다.
                  </p>
                )}
              </div>
              <div className="form-group">
                <div className="input-with-check">
                  <label>PWD</label>
                  {validation.password && <span className="check-icon">✓</span>}
                </div>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder="최소 8자 이상"
                  required
                />
              </div>
              <div className="form-group">
                <div className="input-with-check">
                  <label>PWD_check</label>
                  {validation.passwordConfirm && (
                    <span className="check-icon">✓</span>
                  )}
                </div>
                <input
                  type="password"
                  name="passwordConfirm"
                  value={formData.passwordConfirm}
                  onChange={handleInputChange}
                  required
                />
              </div>
              {error && <div className="error-message">{error}</div>}
              <div className="button-group">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn-back"
                >
                  BACK
                </button>
                <button type="submit" className="btn-next">
                  NEXT
                </button>
              </div>
            </form>
          )}

          {step === 3 && (
            <form onSubmit={handleSubmit}>
              <div className="signup-summary">
                <h3>가입 정보 확인</h3>
                <div className="summary-item">
                  <label>UserName:</label>
                  <span>{formData.username}</span>
                </div>
                <div className="summary-item">
                  <label>EMAIL:</label>
                  <span>{formData.email}</span>
                </div>
                {formData.profileImage && (
                  <div className="summary-item">
                    <label>프로필 이미지:</label>
                    <span>{formData.profileImage.name}</span>
                  </div>
                )}
              </div>
              {error && <div className="error-message">{error}</div>}
              <div className="button-group">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="btn-back"
                >
                  BACK
                </button>
                <button type="submit" className="btn-signup">
                  SIGNUP
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
