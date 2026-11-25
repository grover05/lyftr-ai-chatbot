import React from 'react';
import { X, ShieldAlert, Check, HelpCircle } from 'lucide-react';

interface DevModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentSimulation: string;
  onSelectSimulation: (simValue: string) => void;
}

const SIMULATION_OPTIONS = [
  {
    id: 'none',
    value: '',
    label: 'No simulation (Normal operation)',
    desc: 'Requests hit key_1 and resolve normally or via LiteLLM cache.',
  },
  {
    id: 'key_1_429',
    value: 'key_1=429',
    label: 'Simulate key_1 Rate Limit (429)',
    desc: 'Simulates key_1 receiving HTTP 429. Automatically fails over to key_2 (fallback_attempts: 1).',
  },
  {
    id: 'key_1_500',
    value: 'key_1=500',
    label: 'Simulate key_1 Server Error (500)',
    desc: 'Simulates key_1 receiving HTTP 500. Automatically fails over to key_2 (fallback_attempts: 1).',
  },
  {
    id: 'multi_fail',
    value: 'key_1=429,key_2=500',
    label: 'Simulate key_1=429, key_2=500',
    desc: 'Simulates cascading failures across both primary keys.',
  },
  {
    id: 'all_fail',
    value: '*=429',
    label: 'Simulate All Keys Failing (*=429)',
    desc: 'Every key in the pool fails. Backend returns 503 {"detail": "all providers unavailable"} and aborts DB persistence.',
  },
];

export const DevModeModal: React.FC<DevModeModalProps> = ({
  isOpen,
  onClose,
  currentSimulation,
  onSelectSimulation,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog dev-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-wrap">
            <ShieldAlert size={20} className="modal-icon warning-icon" />
            <h2>Developer Mode: Key Failover Simulation</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body">
          <div className="info-callout">
            <HelpCircle size={16} />
            <p>
              Select a scenario below to attach the <code>X-Simulate-Failure</code> header on your next
              chat request. This allows demonstrating automatic key pool failover and 503 resilience on demand.
            </p>
          </div>

          <div className="sim-options-list">
            {SIMULATION_OPTIONS.map((opt) => (
              <label
                key={opt.id}
                className={`sim-option-card ${currentSimulation === opt.value ? 'selected' : ''}`}
              >
                <div className="sim-radio-wrap">
                  <input
                    type="radio"
                    name="failure-simulation"
                    value={opt.value}
                    checked={currentSimulation === opt.value}
                    onChange={() => onSelectSimulation(opt.value)}
                  />
                </div>
                <div className="sim-info">
                  <div className="sim-title">
                    <strong>{opt.label}</strong>
                    {opt.value && <code className="header-tag">X-Simulate-Failure: {opt.value}</code>}
                  </div>
                  <div className="sim-desc">{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => {
              onSelectSimulation('');
              onClose();
            }}
          >
            Clear Simulation
          </button>
          <button type="button" className="btn-primary" onClick={onClose}>
            <Check size={16} />
            <span>Apply & Close</span>
          </button>
        </div>
      </div>
    </div>
  );
};
