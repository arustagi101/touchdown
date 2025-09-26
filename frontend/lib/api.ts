import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Video {
  id: string;
  title: string;
  status: string;
  video_type: string;
  duration?: number;
  fps?: number;
  width?: number;
  height?: number;
  processing_progress: number;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface Highlight {
  id: string;
  start_time: number;
  end_time: number;
  duration: number;
  score: number;
  category?: string;
  description?: string;
  is_included: boolean;
  order_index: number;
}

export const videoApi = {
  uploadVideo: async (file: File, title: string, sportType: string = 'general') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('sport_type', sportType);

    const response = await api.post('/api/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  processFromUrl: async (url: string, title: string, sportType: string = 'general') => {
    const response = await api.post('/api/videos/from-url', { url, title, sport_type: sportType });
    return response.data;
  },

  getVideo: async (videoId: string): Promise<Video> => {
    const response = await api.get(`/api/videos/${videoId}`);
    return response.data;
  },

  getVideoStatus: async (videoId: string) => {
    const response = await api.get(`/api/videos/${videoId}/status`);
    return response.data;
  },

  getHighlights: async (videoId: string): Promise<Highlight[]> => {
    const response = await api.get(`/api/videos/${videoId}/highlights`);
    return response.data;
  },

  generateReel: async (videoId: string, highlightIds?: string[], maxDuration?: number, includeTransitions: boolean = true) => {
    const response = await api.post(`/api/videos/${videoId}/generate-reel`, {
      highlight_ids: highlightIds,
      max_duration: maxDuration,
      include_transitions: includeTransitions,
    });
    return response.data;
  },

  updateHighlight: async (highlightId: string, data: Partial<Highlight>) => {
    const response = await api.patch(`/api/highlights/${highlightId}`, data);
    return response.data;
  },

  reorderHighlights: async (videoId: string, highlightOrder: string[]) => {
    const response = await api.post(`/api/highlights/${videoId}/reorder`, { highlight_order: highlightOrder });
    return response.data;
  },

  autoSelectHighlights: async (videoId: string, targetDuration: number = 120, minScore: number = 60) => {
    const response = await api.post(`/api/highlights/${videoId}/auto-select`, {
      target_duration: targetDuration,
      min_score: minScore,
    });
    return response.data;
  },
};

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private videoId: string | null = null;
  private clientId: string;
  private onMessageCallbacks: ((data: any) => void)[] = [];

  constructor() {
    this.clientId = Math.random().toString(36).substring(7);
  }

  connect(videoId: string) {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${this.clientId}`;
    this.ws = new WebSocket(wsUrl);
    this.videoId = videoId;

    this.ws.onopen = () => {
      this.subscribe(videoId);
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onMessageCallbacks.forEach(callback => callback(data));
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket closed');
    };
  }

  subscribe(videoId: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'subscribe', video_id: videoId }));
    }
  }

  unsubscribe(videoId: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'unsubscribe', video_id: videoId }));
    }
  }

  onMessage(callback: (data: any) => void) {
    this.onMessageCallbacks.push(callback);
  }

  disconnect() {
    if (this.videoId) {
      this.unsubscribe(this.videoId);
    }
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default api;