import React, { useState, useRef, useEffect } from 'react';
import { useChat } from './hooks/useChat';
import { Header } from './components/Header';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { SettingsModal } from './components/SettingsModal';
import { DevModeModal } from './components/DevModeModal';
import { Sparkles, ShieldAlert, Database, Zap, Cpu } from 'lucide-react';
import './App.css';

export const App: React.FC = () => {
  const {
    sessionId,
    messages,
    isLoading,
    systemPrompt,
    setSystemPrompt,
    failureSimulation,
    setFailureSimulation,
    health,
    healthError,
    startNewChat,
    sendMessage,
  } = useChat();

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDevModeOpen, setIsDevModeOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="app-container">
      <Header
        sessionId={sessionId}
        health={health}
        healthError={healthError}
        failureSimulation={failureSimulation}
        onNewChat={startNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenDevMode={() => setIsDevModeOpen(true)}
      />

      {failureSimulation && (
        <div className="active-simulation-banner">
          <ShieldAlert size={16} />
          <span>
            Developer Mode Active: <strong>X-Simulate-Failure: {failureSimulation}</strong> will be
            applied to your requests.
          </span>
          <button className="banner-dismiss-btn" onClick={() => setFailureSimulation('')}>
            Disable Simulation
          </button>
        </div>
      )}

      <main className="chat-main">
        <div className="messages-viewport">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon-wrapper">
                <Sparkles size={36} className="empty-icon" />
              </div>
              <h2 className="empty-title">Lyftr AI Chatbot</h2>
              <p className="empty-subtitle">
                High-performance LLM gateway with automated key pool failover, persistent SQLite multi-turn memory,
                and LiteLLM response caching.
              </p>

              <div className="quick-suggestions-grid">
                <button
                  className="suggestion-card"
                  onClick={() => sendMessage('What is the capital of France?')}
                >
                  <div className="suggestion-icon"><Zap size={16} /></div>
                  <div className="suggestion-text">
                    <strong>Test Inference</strong>
                    <span>"What is the capital of France?"</span>
                  </div>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() => sendMessage('Explain machine learning in one short paragraph.')}
                >
                  <div className="suggestion-icon"><Database size={16} /></div>
                  <div className="suggestion-text">
                    <strong>Test Response Caching</strong>
                    <span>"Explain machine learning in one short paragraph."</span>
                  </div>
                </button>

                <button
                  className="suggestion-card"
                  onClick={() => {
                    setFailureSimulation('key_1=429');
                    sendMessage('Explain quantum computing briefly.');
                  }}
                >
                  <div className="suggestion-icon"><Cpu size={16} /></div>
                  <div className="suggestion-text">
                    <strong>Test Key Failover (429)</strong>
                    <span>Simulates key_1 rate limit failover to key_2</span>
                  </div>
                </button>
              </div>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="loading-indicator-row">
                  <div className="avatar assistant-avatar pulse-avatar">
                    <Sparkles size={16} />
                  </div>
                  <div className="loading-bubbles">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="chat-footer">
          <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
        </div>
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        systemPrompt={systemPrompt}
        onSaveSystemPrompt={setSystemPrompt}
      />

      <DevModeModal
        isOpen={isDevModeOpen}
        onClose={() => setIsDevModeOpen(false)}
        currentSimulation={failureSimulation}
        onSelectSimulation={setFailureSimulation}
      />
    </div>
  );
};

export default App;
