import React, { useState } from 'react';
import { X, Sliders, Check } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  systemPrompt: string;
  onSaveSystemPrompt: (newPrompt: string) => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  systemPrompt,
  onSaveSystemPrompt,
}) => {
  const [promptText, setPromptText] = useState(systemPrompt);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveSystemPrompt(promptText);
    onClose();
  };

  const handleReset = () => {
    const defaultPrompt = 'You are a helpful, concise AI assistant.';
    setPromptText(defaultPrompt);
    onSaveSystemPrompt(defaultPrompt);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-wrap">
            <Sliders size={20} className="modal-icon" />
            <h2>Session Settings</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label htmlFor="system-prompt" className="form-label">
              Active System Prompt
            </label>
            <p className="form-description">
              Overrides the instructions given to the LLM for this session. Modifying this changes
              the cache identity since cache depends on model + complete message list.
            </p>
            <textarea
              id="system-prompt"
              data-testid="system-prompt-input"
              className="settings-textarea"
              rows={4}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="Enter system prompt (e.g. 'You are a helpful, concise AI assistant.')..."
            />
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={handleReset}>
            Reset to Default
          </button>
          <button type="button" className="btn-primary" onClick={handleSave}>
            <Check size={16} />
            <span>Save Settings</span>
          </button>
        </div>
      </div>
    </div>
  );
};
