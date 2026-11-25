import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ChatMessage as ChatMessageType } from '../types/chat';
import { Bot, User, Zap, Database, ArrowUpRight, ArrowDownLeft, Key, RefreshCw, AlertCircle } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const meta = message.metadata;

  if (isUser) {
    return (
      <div className="message-row user-row">
        <div className="message-bubble user-bubble">
          <div className="message-content user-text">{message.content}</div>
          <div className="message-time">{message.timestamp}</div>
        </div>
        <div className="avatar user-avatar" title="You">
          <User size={16} />
        </div>
      </div>
    );
  }

  // Assistant Message Container with required data-testid="assistant-message"
  return (
    <div className="message-row assistant-row" data-testid="assistant-message">
      <div className={`avatar assistant-avatar ${isError ? 'error-avatar' : ''}`} title="Lyftr AI">
        {isError ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>

      <div className={`message-bubble assistant-bubble ${isError ? 'error-bubble' : ''}`}>
        {isError ? (
          <div className="error-content">
            <span className="error-title">Notice:</span>
            <p className="error-text">{message.content}</p>
          </div>
        ) : (
          <div className="message-content markdown-body">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

        {meta && (
          <div className="metadata-container">
            {/* Resolution source: data-testid="meta-source" */}
            <div
              className={`meta-badge source-badge ${
                meta.resolution_source === 'LLM_CACHE' ? 'badge-cache' : 'badge-live'
              }`}
              title="Resolution Source"
            >
              {meta.resolution_source === 'LLM_CACHE' ? (
                <>
                  <Database size={12} />
                  <span data-testid="meta-source">LLM_CACHE</span>
                </>
              ) : (
                <>
                  <Zap size={12} />
                  <span data-testid="meta-source">LIVE_INFERENCE</span>
                </>
              )}
            </div>

            {/* Model: data-testid="meta-model" */}
            <div className="meta-badge model-badge" title="Model Used">
              <span data-testid="meta-model">{meta.model}</span>
            </div>

            {/* Latency: data-testid="meta-latency" */}
            <div className="meta-badge latency-badge" title="Resolution Latency">
              <span data-testid="meta-latency">{meta.latency_ms} ms</span>
            </div>

            {/* Input tokens: data-testid="meta-input-tokens" */}
            <div className="meta-badge token-badge" title="Input Tokens">
              <ArrowUpRight size={12} />
              <span>
                <strong data-testid="meta-input-tokens">{meta.input_tokens}</strong> in
              </span>
            </div>

            {/* Output tokens: data-testid="meta-output-tokens" */}
            <div className="meta-badge token-badge" title="Output Tokens">
              <ArrowDownLeft size={12} />
              <span>
                <strong data-testid="meta-output-tokens">{meta.output_tokens}</strong> out
              </span>
            </div>

            {/* Key ID badge */}
            <div className="meta-badge key-badge" title="API Key Used">
              <Key size={12} />
              <span>{meta.key_id ? meta.key_id : 'cached'}</span>
            </div>

            {/* Fallback attempts badge */}
            <div
              className={`meta-badge fallback-badge ${
                meta.fallback_attempts > 0 ? 'fallback-warning' : ''
              }`}
              title="Failed keys before success"
            >
              <RefreshCw size={12} />
              <span>fallbacks: {meta.fallback_attempts}</span>
            </div>
          </div>
        )}

        <div className="message-time">{message.timestamp}</div>
      </div>
    </div>
  );
};
