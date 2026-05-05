/* 数据模型 */
// PipelineStage - Pipeline阶段信息
export interface PipelineStage {
  stageId: string;
  name?: string;
  description?: string;
}
// ExecutionStatus - 执行状态信息
export interface ExecutionStatus {
  pipelineId: string;
  executionId: string;
  status: 'idle' | 'running' | 'success' | 'failed';
  currentStageId?: string;
  totalDuration?: number;
  lastUpdated: number;
}
// PipelineStatus - Pipeline模板信息
export interface PipelineStatus {
  pipelineId: string;
  name?: string;
  description?: string;
  stages: PipelineStage[];
}
// Checkpoint - 检查点信息
export interface CheckpointStatus {
  executionId: string;
  checkpointId: string;
  reviews: string;
  action?: 'accept' | 'reject';
  prompt?: string;
}
// StartTaskRequest - 启动任务信息
export interface StartTaskRequest {
  pipelineId: string;
  sourceData?: string;
  prompt?: string;
}
class PipelineApiService {
  private baseUrl = 'http://60.204.174.188:8000';

  setApiConfig(baseUrl?: string) {
    if (baseUrl) {
      this.baseUrl = baseUrl;
    }
  }

  // GetPipelines - 获取Pipeline列表
  async getPipelines(): Promise<PipelineStatus[]> {
    const response = await fetch(`${this.baseUrl}/api/pipelines`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch pipeline list: ${response.statusText}`);
    }

    const data = await response.json();
    return data.items || [];
  }

  // GetPipelineConfig - 获取指定Pipeline的配置
  async getPipelineConfig(pipelineId: string): Promise<PipelineStatus> {
    const response = await fetch(`${this.baseUrl}/api/pipelines/${pipelineId}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch pipeline config: ${response.statusText}`);
    }

    return response.json();
  }

  // StartTask - 启动新任务
  async startTask(request: StartTaskRequest): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/executions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to start task: ${response.statusText}`);
    }

    return response.json();
  }

  // GetCheckpoint - 获取待审批检查点信息
  async getCheckpoint(executionId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/checkpoints/${executionId}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch checkpoint list: ${response.statusText}`);
    }

    return response.json();
  }

  // CheckpointPrompt - 提交检查点反馈
  async checkpointPrompt(request: CheckpointStatus): Promise<any> {
    if (request.action==='accept') {
      const response = await fetch(`${this.baseUrl}/api/checkpoints/${request.executionId}/${request.checkpointId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: request.action,
          reviews: request.reviews,
          prompt: request.prompt
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to process checkpoint: ${response.statusText}`);
      }
      return response.json();
    }
    else if (request.action==='reject') {
      const response = await fetch(`${this.baseUrl}/api/checkpoints/${request.executionId}/${request.checkpointId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: request.action,
          reviews: request.reviews,
          prompt: request.prompt
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to process checkpoint: ${response.statusText}`);
      }
      return response.json();
    }
    else {
      throw new Error(`Invalid action: ${request.action}`);
    }
  }

  // GetTaskState - 获取当前任务状态
  async getTaskState(executionId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/executions/${executionId}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch task state: ${response.statusText}`);
    }

    return response.json();
  }
}

export const pipelineApi = new PipelineApiService();
