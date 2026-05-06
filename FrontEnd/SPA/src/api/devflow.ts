/**
 * API Service - 与后端 DevFlow API 交互
 * 匹配后端 /api/executions, /api/pipelines, /api/checkpoints 端点
 */

import axios, { AxiosInstance, AxiosError } from 'axios'

// ============= Types =============

export interface ExecutionStatus {
  id: string
  pipeline_id: string
  status: string
  current_stage_id: string[]
  current_stage_name: string | null
  progress: number
  results: Record<string, StageResult>
  checkpoints: Record<string, CheckpointInfo>
  error: string | null
  created_at: string
  updated_at: string | null
  completed_at?: string | null
}

export interface StageResult {
  stage_id: string
  status: string
  output: Record<string, any>
  artifacts: Array<{
    file_path: string
    content: string
    change_type: string
    language?: string
    description?: string
  }>
  error?: string
  duration_seconds?: number
  started_at?: string
  completed_at?: string
}

export interface CheckpointInfo {
  id: string
  execution_id: string
  stage_id: string
  stage_result: Record<string, any>  // 匹配后端 dict[str, Any]
  status: string
  created_at: string
  decided_at: string | null
  decided_by: string | null
  comment: string | null
  approval_action: string | null
}

export interface ExecutionCreateResponse {
  id: string
  pipeline_id: string
  status: string[]
  current_stage_id: string[]
  results: Record<string, any>
  checkpoints: Record<string, any>
  created_at: string
  updated_at: string | null
  completed_at: string | null
}

export interface ExecutionCreateParams {
  pipeline_id: string
  demand: string
  config?: Record<string, any>
  context?: {
    repo_path?: string
    focus_files?: Array<{
      path: string
      start_line?: number
      end_line?: number
    }>
  }
}

export interface CheckpointListResponse {
  items: CheckpointInfo[]
  total: number
  pending: number
}

export interface CheckpointSummary {
  execution_id: string
  total: number
  pending: number
  approved: number
  rejected: number
  checkpoints: Array<{
    id: string
    stage_id: string
    status: string
    created_at: string
    decided_at: string | null
    decided_by: string | null
  }>
}

export interface HealthResponse {
  status: string
  version: string
  timestamp: string
  services: Record<string, boolean>
}

export interface PipelineInfo {
  id: string
  name: string
  description: string
  stages: Array<{
    id: string
    name: string
    stage_type: string
    description: string
    is_checkpoint: boolean
  }>
  status: string
  created_at: string
  updated_at: string
}

// ============= API Client =============

class ApiService {
  private client: AxiosInstance

  constructor(baseURL: string = '') {
    this.client = axios.create({
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 60000, // 60秒超时，LLM调用可能较慢
    })

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  setBaseURL(url: string) {
    this.client.defaults.baseURL = url
  }

  // ============= Health =============

  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/api/health')
    return response.data
  }

  // ============= Executions =============

  /**
   * 创建并启动执行
   */
  async createExecution(params: ExecutionCreateParams): Promise<ExecutionCreateResponse> {
    const response = await this.client.post<ExecutionCreateResponse>('/api/executions', {
      pipeline_id: params.pipeline_id,
      demand: params.demand,
      config: params.config || {},
      context: params.context,
    })
    return response.data
  }

  /**
   * 获取执行详情
   */
  async getExecution(executionId: string): Promise<ExecutionStatus> {
    const response = await this.client.get<ExecutionStatus>(`/api/executions/${executionId}`)
    return response.data
  }

  /**
   * 获取执行列表
   */
  async listExecutions(
    pipelineId?: string,
    page: number = 1,
    pageSize: number = 20
  ): Promise<{ items: ExecutionStatus[]; total: number; page: number; page_size: number }> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (pipelineId) params.pipeline_id = pipelineId

    const response = await this.client.get('/api/executions', { params })
    return response.data
  }

  /**
   * 取消执行
   */
  async cancelExecution(executionId: string): Promise<{ status: string; execution_id: string }> {
    const response = await this.client.post(`/api/executions/${executionId}/cancel`)
    return response.data
  }

  /**
   * 暂停执行
   */
  async pauseExecution(executionId: string): Promise<{ status: string; execution_id: string }> {
    const response = await this.client.post(`/api/executions/${executionId}/pause`)
    return response.data
  }

  /**
   * 恢复执行
   */
  async resumeExecution(executionId: string): Promise<any> {
    const response = await this.client.post(`/api/executions/${executionId}/resume`)
    return response.data
  }

  /**
   * 测试运行流水线（同步）
   */
  async testRun(
    pipelineId: string,
    demand: string,
    outputDir: string = 'output'
  ): Promise<{
    status: string
    result: {
      status: string
      current_stage_id: string[]
      results: Record<string, any>
      output: {
        files_written: string[]
        count: number
        message?: string
      }
    }
  }> {
    const response = await this.client.post('/api/executions/test-run', {
      pipeline_id: pipelineId,
      demand,
      output_dir: outputDir,
    })
    return response.data
  }

  // ============= Checkpoints =============

  /**
   * 获取待审批检查点列表
   */
  async getPendingCheckpoints(executionId?: string): Promise<CheckpointListResponse> {
    const params: Record<string, any> = {}
    if (executionId) params.execution_id = executionId

    const response = await this.client.get('/api/checkpoints', { params })
    return response.data
  }

  /**
   * 获取所有检查点
   */
  async getAllCheckpoints(
    executionId?: string,
    status?: string
  ): Promise<{
    items: CheckpointInfo[]
    total: number
    pending: number
    approved: number
    rejected: number
    by_status: Record<string, number>
    by_execution: Record<string, number>
  }> {
    const params: Record<string, any> = {}
    if (executionId) params.execution_id = executionId
    if (status) params.status = status

    const response = await this.client.get('/api/checkpoints/all', { params })
    return response.data
  }

  /**
   * 获取检查点详情
   */
  async getCheckpoint(executionId: string, stageId: string): Promise<CheckpointInfo> {
    const response = await this.client.get<CheckpointInfo>(
      `/api/checkpoints/${executionId}/${stageId}`
    )
    return response.data
  }

  /**
   * 批准检查点
   */
  async approveCheckpoint(
    executionId: string,
    stageId: string,
    comment?: string,
    approver: string = 'human'
  ): Promise<CheckpointInfo> {
    const response = await this.client.post<CheckpointInfo>(
      `/api/checkpoints/${executionId}/${stageId}/approve`,
      {
        comment,
        approver,
      }
    )
    return response.data
  }

  /**
   * 拒绝检查点
   */
  async rejectCheckpoint(
    executionId: string,
    stageId: string,
    comment: string,
    rejector: string = 'human'
  ): Promise<CheckpointInfo> {
    const response = await this.client.post<CheckpointInfo>(
      `/api/checkpoints/${executionId}/${stageId}/reject`,
      {
        comment,
        rejector,
      }
    )
    return response.data
  }

  /**
   * 获取检查点汇总
   */
  async getCheckpointSummary(executionId: string): Promise<CheckpointSummary> {
    const response = await this.client.get<CheckpointSummary>(
      `/api/checkpoints/${executionId}/summary`
    )
    return response.data
  }

  // ============= Pipelines =============

  /**
   * 获取默认流水线
   */
  async getDefaultPipeline(): Promise<{
    default_pipeline_id: string | null
    default_pipeline: PipelineInfo | null
  }> {
    const response = await this.client.get('/api/pipelines/default')
    return response.data
  }

  /**
   * 获取流水线详情
   */
  async getPipeline(pipelineId: string): Promise<PipelineInfo> {
    const response = await this.client.get<PipelineInfo>(`/api/pipelines/${pipelineId}`)
    return response.data
  }

  // ============= Delivery / Artifacts =============

  /**
   * 获取交付物详情
   */
  async getDelivery(executionId: string): Promise<{
    artifacts: Array<{
      file_path: string
      content: string
      change_type: string
      language?: string
      description?: string
    }>
    deployment_steps: Array<{
      action: string
      command?: string
      description?: string
      verification?: string
    }>
    deployment_script?: string
    estimated_time?: string
    access_url?: string
    checklist?: string[]
    summary?: string
  }> {
    const response = await this.client.get(`/api/executions/${executionId}/delivery`)
    return response.data
  }

  /**
   * 下载单个文件
   */
  async downloadArtifact(
    executionId: string,
    filePath: string
  ): Promise<Blob> {
    const response = await this.client.get(
      `/api/executions/${executionId}/artifacts/${filePath}`,
      { responseType: 'blob' }
    )
    return response.data
  }

  /**
   * 打包下载所有产物
   */
  async downloadAllArtifacts(executionId: string): Promise<Blob> {
    const response = await this.client.get(
      `/api/executions/${executionId}/artifacts/download`,
      { responseType: 'blob' }
    )
    return response.data
  }
}

// 导出单例
export const apiService = new ApiService()

// 也导出类以便测试
export { ApiService }
