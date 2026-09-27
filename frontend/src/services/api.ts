export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';

export interface HealthResponse {
  status: string;
}

export interface ReadinessResponse {
  mcp: boolean;
  tts: boolean;
  voice_1: boolean;
  audio_store: boolean;
  ready: boolean;
}

export interface VoiceMetadata {
  voice_id: string;
  name: string;
  reference_file: string;
  transcript?: string;
  sample_rate: number;
  channels?: number;
  duration_seconds?: number;
  created_at: string;
  status: 'ready' | 'missing' | 'processing' | 'error';
}

export interface AudioItem {
  audio_id: string;
  text: string;
  voice_id: string;
  format: 'wav' | 'mp3';
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  created_at: string;
  audio_url: string;
  file_url: string;
  status?: string;
}

export interface PaginatedAudioResponse {
  total: number;
  page: number;
  limit: number;
  items: AudioItem[];
}

export interface SpeakRequest {
  text: string;
  voice_id?: string;
  speed?: number;
  format?: 'wav' | 'mp3';
}

export interface SpeakResponse {
  audio_id: string;
  status: string;
  duration_seconds: number;
  format: string;
  created_at: string;
  audio_url: string;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  async getReadiness(): Promise<ReadinessResponse> {
    const res = await fetch(`${API_BASE}/ready`);
    return res.json();
  },

  async listVoices(): Promise<VoiceMetadata[]> {
    const res = await fetch(`${API_BASE}/api/v1/voices`);
    return res.json();
  },

  async uploadVoice(formData: FormData): Promise<VoiceMetadata> {
    const res = await fetch(`${API_BASE}/api/v1/voices`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload voice');
    return res.json();
  },

  async deleteVoice1(): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/voices/1`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete voice 1');
  },

  async speak(req: SpeakRequest): Promise<SpeakResponse> {
    const res = await fetch(`${API_BASE}/api/v1/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) throw new Error('Speech synthesis failed');
    return res.json();
  },

  async listAudio(page = 1, limit = 20): Promise<PaginatedAudioResponse> {
    const res = await fetch(`${API_BASE}/api/v1/audio?page=${page}&limit=${limit}`);
    return res.json();
  },

  async deleteAudio(audioId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/v1/audio/${audioId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete audio');
  },

  async cleanupAudio(days?: number): Promise<{ status: string; deleted_count: number }> {
    const query = days !== undefined ? `?days=${days}` : '';
    const res = await fetch(`${API_BASE}/api/v1/audio/cleanup${query}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to trigger retention cleanup');
    return res.json();
  },

  getAudioFileUrl(audioId: string): string {
    return `${API_BASE}/api/v1/audio/${audioId}/file`;
  }
};
