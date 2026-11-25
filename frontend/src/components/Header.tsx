import React from 'react';
import { HealthResponse } from '../types/chat';
import { Sparkles, Plus, Settings as SettingsIcon, Cpu, CheckCircle2, AlertTriangle } from 'lucide-react';

interface HeaderProps {
  sessionId: string;
  health: HealthResponse | null;
  healthError: string | null;
  failureSimulation: string;
  onNewChat: () => void;
  onOpenSettings: () => void;
  onOpenDevMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  sessionId,
  health,
  healthError,
  failureSimulation,
  onNewChat,
  onOpenSettings,
  onOpenDevMode,
}) => {
  return (
    <header className="app-header">
      <div className="header-left">
        <div className="logo-container">
          <div className="logo-icon-wrapper">
            <Sparkles className="logo-icon" size={20} />
          </div>
          <div className="logo-text-block">
            <h1 className="logo-title">Lyftr AI</h1>
            <span className="logo-subtitle">LLM Gateway & Caching</span>
          </div>
        </div>

        <div className="status-badge-container">
          {health ? (
            <div className="status-pill status-online" title={`Keys: ${health.keys_configured}, Cache: ${health.cache_enabled ? 'Active' : 'Disabled'}`}>
              <CheckCircle2 size={12} className="status-dot" />
              <span>Online ({health.keys_configured} Keys)</span>
              {health.cache_enabled && <span className="cache-indicator">Cache Ready</span>}
            </div>
          ) : (
            <div className="status-pill status-offline" title={healthError || 'Connecting...'}>
              <AlertTriangle size={12} className="status-dot" />
              <span>{healthError ? 'Backend Offline' : 'Connecting...'}</span>
            </div>
          )}
          <span className="session-id-pill" title={`Session ID: ${sessionId}`}>
            {sessionId}
          </span>
        </div>
      </div>

      <div className="header-actions">
        {failureSimulation && (
          <button 
            className="sim-active-pill" 
            onClick={onOpenDevMode}
            title="Failure simulation active. Click to adjust."
          >
            <span className="pulse-dot"></span>
            Simulating: <code>{failureSimulation}</code>
          </button>
        )}

        <button 
          className="header-btn secondary-btn" 
          onClick={onOpenDevMode}
          title="Developer Mode: Simulate Key Failures"
        >
          <Cpu size={16} />
          <span className="btn-label">Dev Mode</span>
        </button>

        <button 
          className="header-btn secondary-btn" 
          onClick={onOpenSettings}
          title="Configure System Prompt"
        >
          <SettingsIcon size={16} />
          <span className="btn-label">Settings</span>
        </button>

        <button 
          className="header-btn primary-btn" 
          onClick={onNewChat}
          title="Start a new chat session"
        >
          <Plus size={16} />
          <span>New Chat</span>
        </button>
      </div>
    </header>
  );
};
