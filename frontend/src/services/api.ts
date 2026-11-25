import { ChatRequest, ChatResponse, HealthResponse, SessionHistoryResponse } from '../types/chat';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new ApiError(res.status, `Health check failed with status ${res.status}`);
    }
    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, 'Unable to connect to the server.');
  }
}

export async function sendChatMessage(
  payload: ChatRequest,
  simulateFailureHeader?: string | null
): Promise<ChatResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (simulateFailureHeader && simulateFailureHeader.trim() !== '') {
    headers['X-Simulate-Failure'] = simulateFailureHeader.trim();
  }

  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let detailMsg = 'An error occurred while processing your request.';
      try {
        const errorData = await res.json();
        if (typeof errorData.detail === 'string') {
          detailMsg = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          detailMsg = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
        }
      } catch {
        // Fallback to status text
        detailMsg = res.statusText || detailMsg;
      }

      if (res.status === 422) {
        detailMsg = `Validation Error: ${detailMsg}`;
      } else if (res.status === 503) {
        detailMsg = 'AI providers are temporarily unavailable. Please try again.';
      }

      throw new ApiError(res.status, detailMsg);
    }

    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, 'Unable to connect to the server.');
  }
}

export async function fetchSessionMessages(sessionId: string): Promise<SessionHistoryResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new ApiError(res.status, errorData.detail || 'Failed to load session history');
    }
    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(0, 'Unable to connect to the server.');
  }
}
