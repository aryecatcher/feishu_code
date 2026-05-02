export interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  startTime?: number;
  endTime?: number;
}

export interface PipelineStatus {
  pipelineId: string;
  name: string;
  status: 'idle' | 'running' | 'success' | 'failed';
  stages: PipelineStage[];
  totalDuration?: number;
  lastUpdated: number;
}

export interface SubmitPromptRequest {
  prompt: string;
  taskId: string;
}

export interface SubmitPromptResponse {
  success: boolean;
  taskId: string;
  message?: string;
}

class PipelineApiService {
  private baseUrl = 'https://api.example.com/pipeline';
  private apiKey?: string;

  setApiConfig(apiKey: string, baseUrl?: string) {
    this.apiKey = apiKey;
    if (baseUrl) {
      this.baseUrl = baseUrl;
    }
  }

  async getPipelineStatus(pipelineId: string): Promise<PipelineStatus> {
    if (!this.apiKey) {
      throw new Error('API key not configured');
    }

    const response = await fetch(`${this.baseUrl}/status/${pipelineId}`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch pipeline status: ${response.statusText}`);
    }

    return response.json();
  }

  async submitPrompt(request: SubmitPromptRequest): Promise<SubmitPromptResponse> {
    if (!this.apiKey) {
      throw new Error('API key not configured');
    }

    const response = await fetch(`${this.baseUrl}/submit-prompt`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to submit prompt: ${response.statusText}`);
    }

    return response.json();
  }
}

export const pipelineApi = new PipelineApiService();
