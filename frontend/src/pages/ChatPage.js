import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  getChatInfo,
  getConversations,
  createConversation,
  getConversationDetail,
  sendMessage,
  sendGuestMessage,
  deleteConversation,
} from "../api/chat";
import { buildAbsoluteMediaUrl } from "../utils/media";
import { useToast } from "../contexts/ToastContext";
import Header from "../components/Header";
import SphereAvatar from "../components/SphereAvatar";
import "./ChatPage.css";

const RelatedImageCard = ({ image, index }) => {
  const [hasError, setHasError] = useState(false);
  const imageUrl = buildAbsoluteMediaUrl(
    image?.image_url || image?.url || image?.imageUrl
  );

  // 테이블 안의 이미지는 column_header를 우선 사용
  const displayTitle = image?.table_context?.column_header
    ? image.table_context.column_header
    : image?.disease_name;

  const altText =
    image?.alt_text ||
    image?.caption ||
    displayTitle ||
    `관련 이미지 ${index + 1}`;

  const handleError = () => setHasError(true);

  return (
    <div className="related-image-item">
      {!hasError && imageUrl ? (
        <img
          src={imageUrl}
          alt={altText}
          className="related-image"
          onError={handleError}
        />
      ) : (
        <div className="image-error">이미지를 불러오지 못했습니다.</div>
      )}
      {(displayTitle || image?.caption) && (
        <div className="image-caption">
          {displayTitle && <strong>{displayTitle}</strong>}
          {image?.caption && <p>{image.caption}</p>}
        </div>
      )}
    </div>
  );
};

function ChatPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [guestHistory, setGuestHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStopped, setIsStopped] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const messagesEndRef = useRef(null);
  const sidebarListRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();
  const [conversationState, setConversationState] = useState(null);
  const [requiresAnswer, setRequiresAnswer] = useState(false);
  const pendingRequestRef = useRef(null); // 백그라운드 요청 추적
  const [streamingMessages, setStreamingMessages] = useState({}); // 스트리밍 중인 메시지들 (index -> displayedText)
  const streamingRefs = useRef({}); // 스트리밍 타이머 참조 저장
  const previousMessagesLengthRef = useRef(0); // 이전 메시지 개수 추적
  const wasOnChatPageRef = useRef(true); // 메시지 전송 시 ChatPage에 있었는지 추적
  const { showToast } = useToast(); // 전역 토스트 사용
  const resetConversationFlow = () => {
    setConversationState(null);
    setRequiresAnswer(false);
  };

  useEffect(() => {
    loadChatInfo();
    // 메인에서 사이드바 토글을 통해 넘어온 경우
    if (location.state?.openSidebar) {
      setIsSidebarOpen(true);
    }
    // createNew로 넘어온 경우에도 사이드바 열기
    if (location.state?.createNew) {
      setIsSidebarOpen(true);
    }
  }, [location]);

  // 페이지 가시성 변경 감지 (탭 전환 또는 페이지 이동)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 페이지가 숨겨졌을 때 (다른 탭으로 이동하거나 페이지를 떠남)
        wasOnChatPageRef.current = false;
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  // Route 변경 감지 (다른 페이지로 이동)
  useEffect(() => {
    // ChatPage가 언마운트될 때 (다른 페이지로 이동)
    return () => {
      wasOnChatPageRef.current = false;
    };
  }, []);

  // MainPage에서 대화 세션을 선택해서 넘어온 경우 자동으로 대화 로드
  useEffect(() => {
    const conversationId = location.state?.conversationId;
    const createNew = location.state?.createNew;

    // createNew가 true이면 대화를 로드하지 않음
    if (createNew) {
      return;
    }

    if (
      conversationId &&
      isAuthenticated &&
      selectedConversation?.id !== conversationId
    ) {
      handleConversationClick(conversationId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    location.state?.conversationId,
    location.state?.createNew,
    isAuthenticated,
    selectedConversation?.id,
  ]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 스트리밍 효과: 새로 추가된 assistant 메시지만 글자 하나씩 표시
  useEffect(() => {
    const currentMessagesLength = messages.length;
    const isNewMessage =
      currentMessagesLength > previousMessagesLengthRef.current;

    // 메시지가 새로 추가된 경우에만 스트리밍 처리
    if (isNewMessage) {
      const lastMessage = messages[messages.length - 1];
      const lastIndex = messages.length - 1;

      // 마지막 메시지가 assistant 메시지이고, 아직 스트리밍이 시작되지 않은 경우
      if (
        lastMessage &&
        lastMessage.role === "assistant" &&
        lastMessage.content &&
        !streamingRefs.current[lastIndex]
      ) {
        const fullText = lastMessage.content;
        let currentIndex = 0;

        // 스트리밍 시작
        const streamInterval = setInterval(() => {
          if (currentIndex < fullText.length) {
            setStreamingMessages((prev) => ({
              ...prev,
              [lastIndex]: fullText.substring(0, currentIndex + 1),
            }));
            currentIndex++;
            scrollToBottom(); // 스트리밍 중에도 스크롤 유지
          } else {
            // 스트리밍 완료
            clearInterval(streamInterval);
            streamingRefs.current[lastIndex] = null;
          }
        }, 30); // 30ms마다 한 글자씩 (조절 가능)

        streamingRefs.current[lastIndex] = streamInterval;
      }
    }

    // 이전 메시지 개수 업데이트
    previousMessagesLengthRef.current = currentMessagesLength;

    // cleanup: 컴포넌트 언마운트 시 모든 타이머 정리
    return () => {
      Object.values(streamingRefs.current).forEach((interval) => {
        if (interval) clearInterval(interval);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages]);

  // 로딩 상태가 변경될 때도 스크롤 (응답 시작 시)
  useEffect(() => {
    if (isLoading) {
      // 약간의 지연 후 스크롤 (DOM 업데이트 대기)
      const timeout1 = setTimeout(() => {
        scrollToBottom();
      }, 100);
      // 추가로 한 번 더 스크롤 (로딩 인디케이터가 완전히 렌더링된 후)
      const timeout2 = setTimeout(() => {
        scrollToBottom();
      }, 300);

      return () => {
        clearTimeout(timeout1);
        clearTimeout(timeout2);
      };
    }
  }, [isLoading]);

  // 사이드바가 열릴 때 리스트 상단으로 스크롤
  useEffect(() => {
    if (isSidebarOpen && sidebarListRef.current) {
      sidebarListRef.current.scrollTop = 0;
    }
  }, [isSidebarOpen]);

  // 대화 목록이 업데이트될 때 리스트 상단으로 스크롤
  useEffect(() => {
    if (isSidebarOpen && sidebarListRef.current) {
      sidebarListRef.current.scrollTop = 0;
    }
  }, [conversations, isSidebarOpen]);

  // 페이지 포커스 시 현재 대화 세션의 최신 메시지 확인 (백그라운드 응답 확인용)
  useEffect(() => {
    let pollingInterval = null;

    const checkMessages = async () => {
      // selectedConversation이 null이면 폴링 중지
      if (!selectedConversation?.id) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        return;
      }

      if (isAuthenticated && selectedConversation?.id) {
        try {
          const data = await getConversationDetail(selectedConversation.id);
          const lastMessage = data.messages[data.messages.length - 1];

          // 메시지 수가 증가했으면 업데이트 (백그라운드에서 응답이 완료된 경우)
          if (data.messages.length > messages.length) {
            setMessages(data.messages);
            setSelectedConversation(data);
            previousMessagesLengthRef.current = data.messages.length; // 백그라운드 응답은 스트리밍하지 않음
            setIsLoading(false); // 응답 완료 시 로딩 상태 해제

            // 사이드바 대화 목록 갱신 (응답 완료된 대화가 사이드바에 표시되도록)
            loadConversations();

            // 응답 완료 시 사용자가 ChatPage에 없었으면 토스트 표시
            if (!wasOnChatPageRef.current) {
              showToast("답변이 준비되었습니다!", "success");
            }

            // 토스트 표시 후 다시 ChatPage에 있는 것으로 설정
            wasOnChatPageRef.current = true;

            // 대화 상태는 백엔드에 저장되지 않으므로 복원 불가
            // 사용자가 다시 대화를 시작하면 상태가 초기화됨
            // 마지막 메시지가 assistant의 일반 답변이면 대화 상태 초기화
            if (
              lastMessage.role === "assistant" &&
              !lastMessage.content.includes("?")
            ) {
              // 질문이 아닌 일반 답변이면 대화 상태 초기화
              resetConversationFlow();
            }

            // 폴링 중지 (응답 완료)
            if (pollingInterval) {
              clearInterval(pollingInterval);
              pollingInterval = null;
            }
          } else if (
            // 아직 응답이 완료되지 않았고, 마지막 메시지가 사용자 메시지인 경우
            data.messages.length === messages.length &&
            lastMessage &&
            lastMessage.role === "user" &&
            pendingRequestRef.current !== null
          ) {
            // 백그라운드 요청이 진행 중이면 로딩 상태 표시
            setIsLoading(true);
          } else if (pendingRequestRef.current === null) {
            // 백그라운드 요청이 없으면 로딩 상태 해제
            setIsLoading(false);
            if (pollingInterval) {
              clearInterval(pollingInterval);
              pollingInterval = null;
            }
          }
        } catch (err) {
          console.error("대화 세션 새로고침 실패:", err);
          setIsLoading(false);
          if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
          }
        }
      }
    };

    const handleFocus = async () => {
      // selectedConversation이 없으면 폴링 시작하지 않음
      if (!selectedConversation?.id) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
        return;
      }

      // 백그라운드 요청이 진행 중이면 로딩 상태 표시
      if (pendingRequestRef.current !== null) {
        setIsLoading(true);
      }

      // 즉시 확인
      await checkMessages();

      // 백그라운드 요청이 진행 중이고 selectedConversation이 있으면 주기적으로 확인 (2초마다)
      if (pendingRequestRef.current !== null && selectedConversation?.id) {
        if (pollingInterval) {
          clearInterval(pollingInterval);
        }
        pollingInterval = setInterval(checkMessages, 2000);
      }
    };

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        handleFocus();
      } else {
        // 페이지가 숨겨지면 폴링 중지
        if (pollingInterval) {
          clearInterval(pollingInterval);
          pollingInterval = null;
        }
      }
    };

    window.addEventListener("focus", handleFocus);
    // 페이지 가시성 변경 시에도 확인 (다른 탭에서 돌아올 때)
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // 컴포넌트가 마운트되고 ChatPage에 있을 때도 확인
    if (
      window.location.pathname === "/chat" &&
      isAuthenticated &&
      selectedConversation?.id
    ) {
      handleFocus();
    }

    return () => {
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [isAuthenticated, selectedConversation?.id, messages.length]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  };

  const loadChatInfo = async () => {
    try {
      const data = await getChatInfo();
      setIsAuthenticated(data.is_authenticated);
      setUser(data.user);
      if (data.is_authenticated) {
        loadConversations();
      }
    } catch (err) {
      console.error("채팅 정보 로드 실패:", err);
    }
  };

  const loadConversations = async () => {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (err) {
      console.error("대화 목록 로드 실패:", err);
    }
  };

  const handleConversationClick = async (conversationId) => {
    try {
      const data = await getConversationDetail(conversationId);
      setSelectedConversation(data);
      setMessages(data.messages);
      // 스트리밍 상태 초기화 (기존 대화 로드 시)
      setStreamingMessages({});
      // 기존 스트리밍 타이머 정리
      Object.values(streamingRefs.current).forEach((interval) => {
        if (interval) clearInterval(interval);
      });
      streamingRefs.current = {};
      previousMessagesLengthRef.current = data.messages.length; // 기존 대화는 스트리밍하지 않음
      resetConversationFlow();

      // 대화를 로드한 후, 마지막 메시지가 사용자 메시지인지 확인
      const lastMessage = data.messages[data.messages.length - 1];
      if (lastMessage && lastMessage.role === "user") {
        // 마지막 메시지가 사용자 메시지면 응답이 진행 중일 수 있음
        // 잠시 후 다시 확인하여 assistant 메시지가 있는지 체크
        setTimeout(async () => {
          try {
            const updatedData = await getConversationDetail(conversationId);
            const updatedLastMessage =
              updatedData.messages[updatedData.messages.length - 1];

            // 아직 assistant 메시지가 없으면 로딩 상태 표시
            if (updatedLastMessage && updatedLastMessage.role === "user") {
              setIsLoading(true);
              // 주기적으로 확인 (2초마다)
              const checkInterval = setInterval(async () => {
                try {
                  const checkData = await getConversationDetail(conversationId);
                  if (checkData.messages.length > data.messages.length) {
                    // 새로운 메시지가 있으면 업데이트
                    setMessages(checkData.messages);
                    setSelectedConversation(checkData);
                    previousMessagesLengthRef.current =
                      checkData.messages.length; // 기존 메시지는 스트리밍하지 않음
                    setIsLoading(false);
                    clearInterval(checkInterval);
                  }
                } catch (err) {
                  console.error("대화 확인 실패:", err);
                  clearInterval(checkInterval);
                  setIsLoading(false);
                }
              }, 2000);

              // 30초 후 타임아웃
              setTimeout(() => {
                clearInterval(checkInterval);
                setIsLoading(false);
              }, 30000);
            } else {
              // 이미 assistant 메시지가 있으면 로딩 상태 해제
              setMessages(updatedData.messages);
              setSelectedConversation(updatedData);
              previousMessagesLengthRef.current = updatedData.messages.length; // 기존 메시지는 스트리밍하지 않음
              setIsLoading(false);
            }
          } catch (err) {
            console.error("대화 확인 실패:", err);
            setIsLoading(false);
          }
        }, 500);
      } else {
        setIsLoading(false);
      }
    } catch (err) {
      console.error("대화 세션 로드 실패:", err);
      setIsLoading(false);
    }
  };

  const handleNewConversation = async (e) => {
    // 기본 동작 방지 (새로고침 방지)
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // 백그라운드 요청 취소
    if (pendingRequestRef.current) {
      // Promise가 취소 가능한 경우 취소 처리
      pendingRequestRef.current = null;
    }

    // location.state 초기화 (이전 대화 선택 상태 제거)
    // navigate를 사용하여 location.state를 명확하게 초기화
    navigate("/chat", {
      replace: true,
      state: { createNew: true, openSidebar: isSidebarOpen },
    });

    // 대화 세션은 실제 메시지 전송 시 생성되므로 여기서는 초기화만
    // 상태 업데이트를 배치로 처리하여 즉시 반영되도록 함
    setSelectedConversation(null);
    setMessages([]);
    // 스트리밍 상태 초기화
    setStreamingMessages({});
    // 기존 스트리밍 타이머 정리
    Object.values(streamingRefs.current).forEach((interval) => {
      if (interval) clearInterval(interval);
    });
    streamingRefs.current = {};
    previousMessagesLengthRef.current = 0; // 메시지 개수 초기화
    resetConversationFlow();
    setIsLoading(false); // 로딩 상태 초기화
    setIsStopped(false); // 중지 상태 초기화
    setInputMessage(""); // 입력 메시지 초기화

    // 로그인 사용자인 경우 대화 목록 갱신
    if (isAuthenticated) {
      try {
        await loadConversations();
      } catch (err) {
        console.error("대화 목록 갱신 실패:", err);
      }
    }
  };

  const handleDeleteConversation = async (conversationId) => {
    if (!window.confirm("정말 이 대화를 삭제하시겠습니까?")) return;
    try {
      await deleteConversation(conversationId);
      setConversations(conversations.filter((c) => c.id !== conversationId));
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
        setMessages([]);
        resetConversationFlow();
      }
    } catch (err) {
      console.error("대화 삭제 실패:", err);
    }
  };

  const handleStop = () => {
    setIsStopped(true);
    setIsLoading(false);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    setIsStopped(false);
    const messageContent = inputMessage;
    const isAnswerMode = requiresAnswer;
    const statePayload = conversationState;
    setInputMessage("");

    // 메시지 전송 시 현재 위치 기록 (응답 완료 시 비교하기 위해)
    const wasOnChatPageAtStart = true; // 메시지 전송 시점에는 항상 ChatPage에 있음
    wasOnChatPageRef.current = true;

    try {
      if (isAuthenticated) {
        // 로그인 사용자
        const userMessage = {
          role: "user",
          content: messageContent,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // 백그라운드에서 응답 처리 (페이지를 벗어나도 계속 진행)
        const processResponse = async () => {
          let conversationId = null;
          const startedOnChatPage = wasOnChatPageAtStart; // 클로저로 시작 위치 캡처
          try {
            if (!selectedConversation) {
              // 대화 세션이 없으면 먼저 생성하지 않고, 메시지 전송 시 백엔드에서 자동 생성되도록
              // 임시 대화 세션 생성 (나중에 실제 대화 세션으로 교체)
              const tempConv = await createConversation();
              conversationId = tempConv.id;
              setSelectedConversation(tempConv);

              // localStorage에 백그라운드 요청 저장 (메시지 전송 전 카운트)
              localStorage.setItem(
                "pendingChatRequest",
                JSON.stringify({
                  conversationId: tempConv.id,
                  messageCount: messages.length + 1, // user 메시지 추가된 상태
                })
              );

              const data = await sendMessage(
                tempConv.id,
                messageContent,
                statePayload,
                isAnswerMode
              );
              if (!isStopped) {
                const updatedConvs = await getConversations();
                setConversations(updatedConvs);
                const actualConv =
                  updatedConvs.find((c) => c.id === tempConv.id) || tempConv;
                conversationId = actualConv.id;
                setSelectedConversation(actualConv);
                if (data?.assistant_message) {
                  setMessages((prev) => [...prev, data.assistant_message]);
                  // 응답 완료 시 사용자가 ChatPage를 떠났으면 토스트 표시
                  // startedOnChatPage가 true이고 현재 wasOnChatPageRef.current가 false이면 토스트 표시
                  if (startedOnChatPage && !wasOnChatPageRef.current) {
                    showToast("답변이 준비되었습니다!", "success");
                  }
                  // localStorage에서 제거 (응답 완료)
                  localStorage.removeItem("pendingChatRequest");
                }
                setConversationState(data?.conversation_state || null);
                setRequiresAnswer(!!data?.requires_answer);
              }
            } else {
              conversationId = selectedConversation.id;

              // localStorage에 백그라운드 요청 저장 (메시지 전송 전 카운트)
              localStorage.setItem(
                "pendingChatRequest",
                JSON.stringify({
                  conversationId: selectedConversation.id,
                  messageCount: messages.length + 1, // user 메시지 추가된 상태
                })
              );

              const data = await sendMessage(
                selectedConversation.id,
                messageContent,
                statePayload,
                isAnswerMode
              );
              if (!isStopped) {
                if (data?.assistant_message) {
                  setMessages((prev) => [...prev, data.assistant_message]);
                  // 응답 완료 시 사용자가 ChatPage를 떠났으면 토스트 표시
                  // startedOnChatPage가 true이고 현재 wasOnChatPageRef.current가 false이면 토스트 표시
                  if (startedOnChatPage && !wasOnChatPageRef.current) {
                    showToast("답변이 준비되었습니다!", "success");
                  }
                  // localStorage에서 제거 (응답 완료)
                  localStorage.removeItem("pendingChatRequest");
                }
                setConversationState(data?.conversation_state || null);
                setRequiresAnswer(!!data?.requires_answer);
                loadConversations(); // 대화 목록 갱신
              }
            }
          } catch (err) {
            console.error("백그라운드 메시지 처리 실패:", err);
            // 에러가 발생해도 사용자 메시지는 이미 표시되었으므로 계속 진행
            // localStorage에서 제거 (에러 발생 시)
            localStorage.removeItem("pendingChatRequest");
          } finally {
            setIsLoading(false);
            pendingRequestRef.current = null;
          }
        };

        // 즉시 로딩 상태 해제 (사용자가 다른 페이지로 이동할 수 있도록)
        setIsLoading(false);
        // 백그라운드에서 비동기로 처리 (페이지를 벗어나도 계속 진행)
        pendingRequestRef.current = processResponse();
      } else {
        // 게스트 사용자 (게스트는 백그라운드 처리 불필요, 즉시 응답 필요)
        const userMessage = {
          role: "user",
          content: messageContent,
          created_at: new Date().toISOString(),
        };
        const newHistory = [...guestHistory, userMessage];
        setMessages((prev) => [...prev, userMessage]);

        if (!isStopped) {
          const data = await sendGuestMessage(
            messageContent,
            statePayload,
            isAnswerMode,
            guestHistory
          );
          const assistantMessage = {
            role: "assistant",
            content: data.response,
            thinking_process: data.thinking_process,
            related_images: data.related_images || [],
            created_at: new Date().toISOString(),
          };

          setMessages((prev) => [...prev, assistantMessage]);
          setGuestHistory([...newHistory, assistantMessage]);
          setConversationState(data?.conversation_state || null);
          setRequiresAnswer(!!data?.requires_answer);
        }
        setIsLoading(false);
      }
    } catch (err) {
      console.error("메시지 전송 실패:", err);
      alert("메시지 전송에 실패했습니다.");
      setIsLoading(false);
      pendingRequestRef.current = null;
    }
  };

  const handleToggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="chat-page">
      {/* Header - 페이지 최상단 고정 */}
      <Header
        showSidebar={true}
        onToggleSidebar={handleToggleSidebar}
        isSidebarOpen={isSidebarOpen}
      />

      {/* Sidebar - 헤더 아래 고정 */}
      {isSidebarOpen && (
        <aside className="chat-sidebar">
          <button
            type="button"
            onClick={handleNewConversation}
            className="sidebar-new"
          >
            New Counseling
            <span className="material-symbols-outlined paper-plane-icon">
              send
            </span>
          </button>

          {/* 검색 기능 - 로그인 사용자만 */}
          {isAuthenticated && (
            <div className="sidebar-search">
              <input
                type="text"
                placeholder="대화 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <span className="material-symbols-outlined search-icon">
                search
              </span>
            </div>
          )}

          <div className="sidebar-list" ref={sidebarListRef}>
            {!isAuthenticated ? (
              <div className="sidebar-empty">
                게스트 모드: 대화 내용이 저장되지 않습니다.
              </div>
            ) : conversations.length === 0 ? (
              <div className="sidebar-empty">대화 기록이 없습니다.</div>
            ) : (
              conversations
                .filter((conv) =>
                  searchQuery
                    ? conv.title
                        ?.toLowerCase()
                        .includes(searchQuery.toLowerCase()) ||
                      conv.last_message_preview
                        ?.toLowerCase()
                        .includes(searchQuery.toLowerCase())
                    : true
                )
                .map((conv) => (
                  <div
                    key={conv.id}
                    className={`sidebar-item ${
                      selectedConversation?.id === conv.id ? "active" : ""
                    }`}
                    onClick={() => handleConversationClick(conv.id)}
                  >
                    <strong>{conv.title || "제목 없음"}</strong>
                    <span className="sidebar-meta">
                      {conv.updated_at
                        ? new Date(conv.updated_at).toLocaleString()
                        : ""}
                    </span>
                    {/* 감정 퍼센테이지 바 */}
                    {conv.sentiment_percentages && (
                      <div className="sidebar-sentiment-bar">
                        <div className="sentiment-tooltip">
                          <strong>나쁨</strong>{" "}
                          {conv.sentiment_percentages.negative}% |{" "}
                          <strong>중립</strong>{" "}
                          {conv.sentiment_percentages.neutral}% |{" "}
                          <strong>기쁨</strong>{" "}
                          {conv.sentiment_percentages.positive}%
                        </div>
                        {conv.sentiment_percentages.negative > 0 && (
                          <div
                            className="sentiment-segment negative"
                            style={{
                              width: `${conv.sentiment_percentages.negative}%`,
                            }}
                          />
                        )}
                        {conv.sentiment_percentages.neutral > 0 && (
                          <div
                            className="sentiment-segment neutral"
                            style={{
                              width: `${conv.sentiment_percentages.neutral}%`,
                            }}
                          />
                        )}
                        {conv.sentiment_percentages.positive > 0 && (
                          <div
                            className="sentiment-segment positive"
                            style={{
                              width: `${conv.sentiment_percentages.positive}%`,
                            }}
                          />
                        )}
                      </div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteConversation(conv.id);
                      }}
                      className="sidebar-delete-btn"
                      aria-label="삭제"
                    >
                      <span className="material-symbols-outlined">delete</span>
                    </button>
                  </div>
                ))
            )}
          </div>
        </aside>
      )}

      {/* Main Chat Area - 헤더 아래, 사이드바 옆 */}
      <main className={`chat-main ${isSidebarOpen ? "sidebar-open" : ""}`}>
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>안녕하세요! MindCare입니다.</h2>
              <p>무엇을 도와드릴까요?</p>
              {!isAuthenticated && (
                <p className="guest-warning">
                  게스트 모드: 대화 내용이 저장되지 않습니다.
                </p>
              )}
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                {/* Message Avatar */}
                <div className="message-avatar">
                  {msg.role === "user" ? (
                    user?.profile_image ? (
                      <img
                        src={buildAbsoluteMediaUrl(user.profile_image)}
                        alt="user"
                        className="avatar-image"
                      />
                    ) : (
                      <div className="avatar-placeholder">
                        {user?.username?.charAt(0).toUpperCase() || "U"}
                      </div>
                    )
                  ) : (
                    <SphereAvatar size={40} />
                  )}
                </div>

                {/* Message Content */}
                <div className="message-content-wrapper">
                  {msg.role === "assistant" && msg.thinking_process && (
                    <div className="thinking-process">
                      {msg.thinking_process.map((node, i) => (
                        <div key={i} className="thinking-node">
                          <span className="material-symbols-outlined thinking-icon">
                            cloud
                          </span>
                          <span>{node.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="message-content">
                    {streamingMessages[idx] !== undefined
                      ? streamingMessages[idx]
                      : msg.content}
                    {streamingMessages[idx] !== undefined &&
                      streamingMessages[idx].length < msg.content.length && (
                        <span className="streaming-cursor">|</span>
                      )}
                  </div>
                  <div className="message-time">
                    {new Date(msg.created_at).toLocaleTimeString("ko-KR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                  {msg.role === "assistant" &&
                    msg.related_images &&
                    msg.related_images.length > 0 && (
                      <div className="related-images">
                        <div className="related-images-title">관련 이미지</div>
                        <div className="related-images-grid">
                          {msg.related_images.map((image, imageIdx) => (
                            <RelatedImageCard
                              key={`${msg.id || idx}-related-${imageIdx}`}
                              image={image}
                              index={imageIdx}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">
                <SphereAvatar size={40} />
              </div>
              <div className="message-content-wrapper">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input form - 하단 고정 */}
        <div
          className={`message-input-container ${
            messages.length === 0 ? "center" : ""
          }`}
        >
          <form onSubmit={handleSendMessage} className="message-input-form">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="메시지를 입력하세요..."
              disabled={isLoading}
            />
            <button
              type={isLoading ? "button" : "submit"}
              disabled={!inputMessage.trim() && !isLoading}
              onClick={isLoading ? handleStop : undefined}
              className={isLoading ? "loading" : ""}
            >
              {isLoading ? <span className="stop-icon">■</span> : "전송"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default ChatPage;
