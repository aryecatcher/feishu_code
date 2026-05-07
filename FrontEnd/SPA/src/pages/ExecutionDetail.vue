<template>
  <div class="execution-detail">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </button>
      <h1>执行详情</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshStatus" :disabled="loading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          刷新
        </button>
        <button v-if="execution?.status === 'completed'" class="btn btn-primary" @click="openDeliveryPanel">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          下载产物
        </button>
      </div>
    </div>

    <!-- 执行状态卡片 -->
    <div class="status-card">
      <div class="status-header">
        <div class="status-info">
          <span class="status-badge" :class="statusClass">
            <span v-if="isRunning" class="spinner"></span>
            {{ statusText }}
          </span>
          <span class="execution-id">ID: {{ executionId }}</span>
        </div>
        <div class="execution-time">
          <span v-if="execution?.created_at">开始于 {{ formatTime(execution.created_at) }}</span>
          <span v-if="execution?.completed_at"> · 完成于 {{ formatTime(execution.completed_at) }}</span>
        </div>
      </div>

      <!-- 流水线进度 -->
      <PipelineProgress
        :stages="pipelineStages"
        :current-stage-id="execution?.current_stage_id || []"
        :completed-stage-ids="completedStageIds"
        :status="(execution?.status || 'pending') as 'pending' | 'running' | 'waiting_approval' | 'completed' | 'failed'"
        :checkpoints="checkpointDisplayList"
      />
    </div>

    <!-- 检查点状态概览 - 基于流水线定义 -->
    <div v-if="checkpointStages.length > 0" class="checkpoint-overview">
      <div class="checkpoint-summary">
        <div class="summary-header">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 11l3 3L22 4"/>
            <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
          </svg>
          <span>检查点状态</span>
          <span class="checkpoint-counts">
            <span class="count-item pending">{{ checkpointSummary.pending }} 待审批</span>
            <span class="count-item approved">{{ checkpointSummary.approved }} 已通过</span>
            <span class="count-item rejected">{{ checkpointSummary.rejected }} 已驳回</span>
          </span>
        </div>
        
        <!-- 检查点时间线 -->
        <div class="checkpoint-timeline">
          <div 
            v-for="checkpoint in allCheckpoints" 
            :key="checkpoint.id"
            class="timeline-item"
            :class="getCheckpointStatusClass(checkpoint.status)"
          >
            <div class="timeline-marker">
              <span v-if="checkpoint.status === 'pending'" class="pending-icon">⏳</span>
              <span v-else-if="checkpoint.status === 'approved'" class="approved-icon">✓</span>
              <span v-else-if="checkpoint.status === 'rejected'" class="rejected-icon">✕</span>
              <span v-else class="pending-icon">○</span>
            </div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="stage-name">{{ checkpoint.stage_id }}</span>
                <span class="checkpoint-time">{{ formatTime(checkpoint.created_at) }}</span>
              </div>
              <div v-if="checkpoint.decided_at" class="decision-info">
                <span v-if="checkpoint.approval_action === 'approved'" class="action approved">
                  通过 · {{ checkpoint.decided_by || '用户' }} · {{ formatTime(checkpoint.decided_at) }}
                </span>
                <span v-else-if="checkpoint.approval_action === 'rejected'" class="action rejected">
                  驳回 · {{ checkpoint.decided_by || '用户' }} · {{ formatTime(checkpoint.decided_at) }}
                </span>
              </div>
              <div v-if="checkpoint.comment" class="decision-comment">
                {{ checkpoint.comment }}
              </div>
            </div>
          </div>
          
          <!-- 如果没有检查点记录，显示占位符 -->
          <div v-if="allCheckpoints.length === 0" class="no-checkpoints">
            <span class="no-checkpoints-text">暂无检查点记录</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 需要审批时显示 -->
    <div v-if="pendingCheckpoint" class="checkpoint-panel">
      <div class="checkpoint-header">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>需要人工审批</span>
        <span class="checkpoint-badge">检查点 #{{ currentCheckpointIndex + 1 }}</span>
      </div>

      <div class="checkpoint-body">
        <h3>{{ pendingCheckpoint.stage_id }}</h3>
        <p class="checkpoint-desc">请确认以下方案，执行将继续进行</p>

        <!-- 阶段输出 -->
        <div v-if="pendingCheckpoint.stage_result" class="stage-output">
          <div class="output-header">
            <span>阶段输出</span>
            <button class="expand-btn" @click="toggleCheckpointOutput">
              {{ checkpointOutputExpanded ? '收起' : '展开' }}
            </button>
          </div>
          <pre v-show="checkpointOutputExpanded">{{ formatOutput(pendingCheckpoint.stage_result) }}</pre>
        </div>

        <!-- 生成的产物 -->
        <div v-if="pendingCheckpoint.stage_result?.artifacts?.length > 0" class="checkpoint-artifacts">
          <div class="output-header">
            <span>生成的产物 ({{ pendingCheckpoint.stage_result.artifacts.length }})</span>
          </div>
          <div class="artifact-list">
            <div v-for="artifact in pendingCheckpoint.stage_result.artifacts" :key="artifact.file_path" class="artifact-item">
              <span class="artifact-icon">{{ getFileIcon(artifact.file_path) }}</span>
              <span class="artifact-path">{{ artifact.file_path }}</span>
              <span class="artifact-type">{{ artifact.change_type || '修改' }}</span>
              <button class="artifact-action" @click="previewArtifact(artifact)">预览</button>
            </div>
          </div>
        </div>
      </div>

      <div class="checkpoint-actions">
        <div class="reject-section">
          <button class="btn btn-danger-outline" @click="showRejectDialog = true" :disabled="actionLoading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            驳回
          </button>
        </div>
        <button class="btn btn-primary" @click="handleApprove" :disabled="actionLoading">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          {{ actionLoading ? '处理中...' : '通过并继续' }}
        </button>
      </div>
    </div>

    <!-- 驳回原因弹窗 -->
    <div v-if="showRejectDialog" class="modal-overlay" @click.self="showRejectDialog = false">
      <div class="reject-dialog">
        <div class="dialog-header">
          <h3>驳回检查点</h3>
          <button class="close-btn" @click="showRejectDialog = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <p class="dialog-desc">
            请输入驳回原因，这将终止当前执行流程。
          </p>
          <textarea 
            v-model="rejectReason"
            class="reject-textarea"
            placeholder="请输入驳回原因..."
            rows="4"
          ></textarea>
          <p v-if="rejectReason && rejectReason.length < 2" class="reject-hint">
            驳回原因至少需要 2 个字符
          </p>
        </div>
        <div class="dialog-footer">
          <button class="btn btn-outline" @click="showRejectDialog = false" :disabled="actionLoading">
            取消
          </button>
          <button 
            class="btn btn-danger" 
            @click="confirmReject" 
            :disabled="actionLoading || rejectReason.length < 2"
          >
            {{ actionLoading ? '提交中...' : '确认驳回' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 阶段详情 -->
    <div class="stages-section">
      <h2 class="section-title">阶段输出</h2>

      <div v-if="stageResults.length === 0" class="empty-stages">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <line x1="3" y1="9" x2="21" y2="9"/>
          <line x1="9" y1="21" x2="9" y2="9"/>
        </svg>
        <p>暂无阶段输出</p>
      </div>

      <div v-else class="stage-cards">
        <div v-for="(stage, index) in stageResults" :key="stage.stage_id" class="stage-card">
          <div class="stage-card-header" @click="toggleStage(index)">
            <div class="stage-info">
              <span class="stage-icon" :class="stageIconClass(stage.status)">
                {{ stageIcon(stage.status) }}
              </span>
              <span class="stage-name">{{ stage.stage_id }}</span>
              <span v-if="stage.duration_seconds" class="stage-duration">
                {{ stage.duration_seconds.toFixed(1) }}s
              </span>
            </div>
            <svg class="expand-icon" :class="{ expanded: expandedStages.has(index) }" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>

          <div v-show="expandedStages.has(index)" class="stage-card-body">
            <!-- 状态和错误 -->
            <div v-if="stage.error" class="stage-error">
              <strong>错误:</strong> {{ stage.error }}
            </div>

            <!-- 输出内容 -->
            <div v-if="stage.output && Object.keys(stage.output).length > 0" class="stage-output">
              <h4>输出</h4>
              <pre>{{ JSON.stringify(stage.output, null, 2) }}</pre>
            </div>

            <!-- 产物 -->
            <div v-if="stage.artifacts?.length > 0" class="stage-artifacts">
              <h4>生成的文件 ({{ stage.artifacts.length }})</h4>
              <div class="artifact-list">
                <div v-for="artifact in stage.artifacts" :key="artifact.file_path" class="artifact-item">
                  <span class="artifact-icon">{{ getFileIcon(artifact.file_path) }}</span>
                  <span class="artifact-path">{{ artifact.file_path }}</span>
                  <button class="artifact-action" @click="previewArtifact(artifact)">
                    预览
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 交付物面板 -->
    <DeliveryPanel
      v-model:visible="showDeliveryPanel"
      :execution-id="executionId"
      :delivery-data="deliveryData"
      @close="handleDeliveryClose"
    />

    <!-- 文件预览弹窗 -->
    <div v-if="previewArtifactData" class="preview-modal">
      <div class="preview-header">
        <h3>{{ previewArtifactData.file_path }}</h3>
        <button class="preview-close" @click="previewArtifactData = null">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="preview-body">
        <pre><code>{{ previewArtifactData.content }}</code></pre>
      </div>
      <div class="preview-footer">
        <button class="btn btn-outline" @click="copyArtifactContent">
          复制内容
        </button>
        <button class="btn btn-primary" @click="downloadArtifact">
          下载文件
        </button>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast.show" class="toast" :class="toast.type">
        {{ toast.message }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiService } from '../api/devflow'
import type { ExecutionStatus, StageResult, CheckpointInfo } from '../api/devflow'
import PipelineProgress from '../components/PipelineProgress.vue'
import DeliveryPanel from '../components/DeliveryPanel.vue'

const route = useRoute()
const router = useRouter()

// ============= State =============

const executionId = computed(() => route.params.id as string)

const execution = ref<ExecutionStatus | null>(null)
const loading = ref(false)
const actionLoading = ref(false)
const showDeliveryPanel = ref(false)
const expandedStages = ref(new Set<number>())
const previewArtifactData = ref<{ file_path: string; content: string } | null>(null)
const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error' | 'info'
})

// 检查点相关状态
const checkpointOutputExpanded = ref(true)
const showRejectDialog = ref(false)
const rejectReason = ref('')
const checkpointsPollingInterval = ref<ReturnType<typeof setInterval> | null>(null)

let pollingInterval: ReturnType<typeof setInterval> | null = null

// ============= Computed =============

const isRunning = computed(() => {
  return execution.value?.status === 'running' || execution.value?.status === 'waiting_approval'
})

const statusText = computed(() => {
  const status = execution.value?.status
  const statusMap: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    waiting_approval: '等待审批',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
    paused: '已暂停'
  }
  return statusMap[status || ''] || '未知'
})

const statusClass = computed(() => {
  const status = execution.value?.status
  return {
    'status-pending': status === 'pending',
    'status-running': status === 'running',
    'status-waiting': status === 'waiting_approval',
    'status-completed': status === 'completed',
    'status-failed': status === 'failed' || status === 'cancelled'
  }
})

const pipelineStages = computed(() => {
  const stages = [
    { id: 'demand-analysis', name: '需求分析', isCheckpoint: false },
    { id: 'scheme-design', name: '方案设计', isCheckpoint: true },
    { id: 'code-generation', name: '代码生成', isCheckpoint: false },
    { id: 'code-review', name: '代码评审', isCheckpoint: true },
    { id: 'delivery', name: '交付集成', isCheckpoint: false }
  ]
  return stages
})

const completedStageIds = computed(() => {
  if (!execution.value?.results) return []
  return Object.keys(execution.value.results)
})

const stageResults = computed(() => {
  if (!execution.value?.results) return []
  return Object.values(execution.value.results).map(result => {
    // 转换数据结构
    if (result.output?.stage_result) {
      return {
        stage_id: result.stage_id || result.output.stage_result.stage_id,
        status: result.status,
        output: result.output,
        artifacts: result.artifacts || result.output.artifacts || [],
        error: result.error,
        duration_seconds: result.duration_seconds
      }
    }
    return {
      stage_id: result.stage_id || 'unknown',
      status: result.status,
      output: result.output,
      artifacts: result.artifacts || [],
      error: result.error,
      duration_seconds: result.duration_seconds
    }
  })
})

const pendingCheckpoint = computed(() => {
  if (!execution.value?.checkpoints) return null
  const checkpoints = Object.values(execution.value.checkpoints)
  return checkpoints.find(cp => cp.status === 'pending' || cp.status === 'waiting_approval') as CheckpointInfo | null
})

const currentCheckpointIndex = computed(() => {
  if (!pendingCheckpoint.value || !execution.value?.checkpoints) return 0
  const checkpoints = Object.keys(execution.value.checkpoints)
  return checkpoints.indexOf(pendingCheckpoint.value.stage_id)
})

// 检查点概览计算属性
const checkpointSummary = computed(() => {
  if (!execution.value?.checkpoints) {
    return { total: 0, pending: 0, approved: 0, rejected: 0 }
  }
  
  const checkpoints = Object.values(execution.value.checkpoints)
  return {
    total: checkpoints.length,
    pending: checkpoints.filter(cp => cp.status === 'pending' || cp.status === 'waiting_approval').length,
    approved: checkpoints.filter(cp => cp.status === 'approved').length,
    rejected: checkpoints.filter(cp => cp.status === 'rejected').length
  }
})

// 所有检查点列表
const allCheckpoints = computed(() => {
  if (!execution.value?.checkpoints) return []
  return Object.values(execution.value.checkpoints)
})

// 流水线中的审批点列表
const checkpointStages = computed(() => {
  const stages = pipelineStages.value.filter(stage => stage.isCheckpoint)
  console.log('Pipeline checkpoint stages:', stages)
  return stages
})

// 传递给 PipelineProgress 的检查点列表
const checkpointDisplayList = computed(() => {
  if (!execution.value?.checkpoints) return []
  return Object.entries(execution.value.checkpoints).map(([stageId, cp]) => ({
    stageId,
    status: cp.status as 'pending' | 'approved' | 'rejected' | 'waiting_approval'
  }))
})

const deliveryData = computed(() => {
  // 从阶段结果中提取交付物
  const artifacts: Array<{ path: string; content: string; language?: string }> = []
  const deploymentSteps: Array<{ action: string; command?: string; description?: string }> = []

  stageResults.value.forEach(stage => {
    if (stage.artifacts) {
      stage.artifacts.forEach(artifact => {
        if (artifact.file_path && artifact.content) {
          artifacts.push({
            path: artifact.file_path,
            content: artifact.content,
            language: artifact.language
          })
        }
      })
    }
  })

  return {
    artifacts,
    deployment_steps: deploymentSteps
  }
})

// ============= Methods =============

function goBack() {
  router.push('/execute')
}

async function refreshStatus() {
  await Promise.all([fetchExecution(), fetchCheckpointDetails()])
}

async function fetchExecution() {
  if (!executionId.value) return

  loading.value = true
  try {
    const data = await apiService.getExecution(executionId.value)
    console.log('Execution data:', data)
    console.log('Checkpoints:', data.checkpoints)
    
    // 保留之前的检查点数据，避免被覆盖
    const existingCheckpoints = execution.value?.checkpoints || {}
    execution.value = data
    
    // 合并后端返回的检查点和本地的检查点数据
    if (data.checkpoints) {
      Object.assign(execution.value.checkpoints, existingCheckpoints)
    } else {
      execution.value.checkpoints = existingCheckpoints
    }
  } catch (error) {
    console.error('Failed to fetch execution:', error)
    // showToast('获取执行状态失败', 'error')
  } finally {
    loading.value = false
  }
}

// 获取检查点详情 - 使用 /api/checkpoints?execution_id=xxx 接口
async function fetchCheckpointDetails() {
  if (!executionId.value) return
  
  try {
    // 轮询待审批检查点接口
    const result = await apiService.getPendingCheckpoints(executionId.value)
    console.log('Pending checkpoints:', result)
    
    if (execution.value) {
      // 合并检查点数据（保留已审批/已驳回的检查点）
      result.items.forEach(cp => {
        const existing = execution.value!.checkpoints[cp.stage_id]
        // 如果已有记录且已审批/驳回，不覆盖
        if (existing && (existing.status === 'approved' || existing.status === 'rejected')) {
          return
        }
        // 更新或新增检查点
        execution.value!.checkpoints[cp.stage_id] = cp
      })
    }
  } catch (error) {
    console.error('Failed to fetch checkpoint details:', error)
  }
}

function startPolling() {
  // 主轮询：每 2 秒获取执行状态
  pollingInterval = setInterval(async () => {
    await fetchExecution()
  }, 2000)
  
  // 检查点轮询：每 3 秒获取检查点详情（始终轮询）
  checkpointsPollingInterval.value = setInterval(async () => {
    await fetchCheckpointDetails()
  }, 3000)
}

function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval)
    pollingInterval = null
  }
  if (checkpointsPollingInterval.value) {
    clearInterval(checkpointsPollingInterval.value)
    checkpointsPollingInterval.value = null
  }
}

function toggleStage(index: number) {
  if (expandedStages.value.has(index)) {
    expandedStages.value.delete(index)
  } else {
    expandedStages.value.add(index)
  }
  expandedStages.value = new Set(expandedStages.value)
}

function toggleCheckpointOutput() {
  checkpointOutputExpanded.value = !checkpointOutputExpanded.value
}

function stageIcon(status: string) {
  const iconMap: Record<string, string> = {
    completed: '✓',
    running: '⟳',
    failed: '✕',
    pending: '○'
  }
  return iconMap[status] || '○'
}

function stageIconClass(status: string) {
  return {
    'icon-completed': status === 'completed',
    'icon-running': status === 'running',
    'icon-failed': status === 'failed',
    'icon-pending': !status || status === 'pending'
  }
}

function getCheckpointStatusClass(status: string) {
  return {
    'status-pending': status === 'pending' || status === 'waiting_approval',
    'status-approved': status === 'approved',
    'status-rejected': status === 'rejected'
  }
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatOutput(stageResult: any): string {
  if (typeof stageResult === 'string') return stageResult
  if (stageResult.reviews) return stageResult.reviews
  if (stageResult.content) return stageResult.content
  return JSON.stringify(stageResult, null, 2)
}

function getFileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || ''
  const iconMap: Record<string, string> = {
    py: '🐍', js: '📜', ts: '🔷', vue: '💚', jsx: '⚛️',
    tsx: '⚛️', html: '🌐', css: '🎨', json: '📋', yaml: '⚙️',
    yml: '⚙️', md: '📝', txt: '📃', sh: '📟', dockerfile: '🐳'
  }
  return iconMap[ext] || '📄'
}

function previewArtifact(artifact: { file_path: string; content: string }) {
  previewArtifactData.value = artifact
}

async function copyArtifactContent() {
  if (!previewArtifactData.value) return
  try {
    await navigator.clipboard.writeText(previewArtifactData.value.content)
    showToast('已复制到剪贴板', 'success')
  } catch {
    showToast('复制失败', 'error')
  }
}

function downloadArtifact() {
  if (!previewArtifactData.value) return
  const blob = new Blob([previewArtifactData.value.content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = previewArtifactData.value.file_path.split('/').pop() || 'file'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  showToast('文件已开始下载', 'success')
}

function openDeliveryPanel() {
  showDeliveryPanel.value = true
}

function handleDeliveryClose() {
  console.log('Delivery panel closed')
}

async function handleApprove() {
  if (!pendingCheckpoint.value) return

  actionLoading.value = true
  try {
    const stageId = pendingCheckpoint.value.stage_id
    await apiService.approveCheckpoint(
      executionId.value,
      stageId
    )
    showToast('已通过，执行继续中...', 'success')
    // 从 execution 中移除该检查点（关闭面板）
    if (execution.value?.checkpoints[stageId]) {
      delete execution.value.checkpoints[stageId]
    }
    await fetchExecution()
  } catch (error: any) {
    // showToast(error?.response?.data?.detail || '审批失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

async function confirmReject() {
  if (!pendingCheckpoint.value || rejectReason.value.length < 2) return

  actionLoading.value = true
  try {
    const stageId = pendingCheckpoint.value.stage_id
    await apiService.rejectCheckpoint(
      executionId.value,
      stageId,
      rejectReason.value
    )
    showToast('已驳回，执行已终止', 'info')
    // 关闭弹窗
    showRejectDialog.value = false
    rejectReason.value = ''
    // 从 execution 中移除该检查点（关闭面板）
    if (execution.value?.checkpoints[stageId]) {
      delete execution.value.checkpoints[stageId]
    }
    await fetchExecution()
  } catch (error: any) {
    // showToast(error?.response?.data?.detail || '驳回失败', 'error')
  } finally {
    actionLoading.value = false
  }
}

function showToast(message: string, type: 'success' | 'error' | 'info' = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// ============= Lifecycle =============

onMounted(() => {
  fetchExecution()
  fetchCheckpointDetails()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

// 当有待审批检查点时，增加轮询频率
watch(pendingCheckpoint, (newVal) => {
  if (newVal) {
    showToast('发现待审批检查点，请及时处理', 'info')
  }
})
</script>

<style scoped>
.execution-detail {
  min-height: 100vh;
  background: #f9fafb;
  padding: 24px;
}

/* 头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1000px;
  margin: 0 auto 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 状态卡片 */
.status-card {
  max-width: 1000px;
  margin: 0 auto 24px;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-pending {
  background: #f3f4f6;
  color: #6b7280;
}

.status-running {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-waiting {
  background: #fef3c7;
  color: #d97706;
}

.status-completed {
  background: #dcfce7;
  color: #166534;
}

.status-failed {
  background: #fee2e2;
  color: #dc2626;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.execution-id {
  font-size: 13px;
  color: #9ca3af;
  font-family: monospace;
}

.execution-time {
  font-size: 13px;
  color: #9ca3af;
}

/* 检查点概览 */
.checkpoint-overview {
  max-width: 1000px;
  margin: 0 auto 24px;
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.checkpoint-summary .summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: #374151;
  font-weight: 600;
}

.checkpoint-counts {
  margin-left: auto;
  display: flex;
  gap: 16px;
  font-weight: normal;
  font-size: 13px;
}

.count-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.count-item.pending {
  color: #d97706;
}

.count-item.approved {
  color: #16a34a;
}

.count-item.rejected {
  color: #dc2626;
}

/* 检查点时间线 */
.checkpoint-timeline {
  position: relative;
  padding-left: 24px;
}

.checkpoint-timeline::before {
  content: '';
  position: absolute;
  left: 7px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  padding-bottom: 20px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-marker {
  position: absolute;
  left: -24px;
  top: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  z-index: 1;
}

.timeline-item.status-pending .timeline-marker {
  border-color: #d97706;
  background: #fef3c7;
}

.timeline-item.status-approved .timeline-marker {
  border-color: #16a34a;
  background: #dcfce7;
}

.timeline-item.status-rejected .timeline-marker {
  border-color: #dc2626;
  background: #fee2e2;
}

.timeline-content {
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px 16px;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.timeline-header .stage-name {
  font-weight: 500;
  color: #1f2937;
}

.timeline-header .checkpoint-time {
  font-size: 12px;
  color: #9ca3af;
}

.decision-info {
  font-size: 13px;
  margin-top: 4px;
}

.decision-info .action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.decision-info .action.approved {
  color: #16a34a;
}

.decision-info .action.rejected {
  color: #dc2626;
}

.decision-comment {
  margin-top: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 6px;
  font-size: 13px;
  color: #6b7280;
  border-left: 3px solid #e5e7eb;
}

.decision-comment.rejected {
  border-left-color: #dc2626;
}

.no-checkpoints {
  padding: 16px;
  text-align: center;
}

.no-checkpoints-text {
  color: #9ca3af;
  font-size: 13px;
}

/* 审批面板 */
.checkpoint-panel {
  max-width: 1000px;
  margin: 0 auto 24px;
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 12px;
  overflow: hidden;
}

.checkpoint-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: #fef3c7;
  color: #92400e;
  font-weight: 600;
}

.checkpoint-badge {
  margin-left: auto;
  padding: 2px 8px;
  background: #ffffff;
  border-radius: 12px;
  font-size: 12px;
  font-weight: normal;
  color: #92400e;
}

.checkpoint-body {
  padding: 20px;
}

.checkpoint-body h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #1f2937;
}

.checkpoint-desc {
  margin: 0 0 16px;
  color: #6b7280;
  font-size: 14px;
}

.stage-output {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.output-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
}

.expand-btn {
  padding: 4px 8px;
  border: none;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.expand-btn:hover {
  background: #dbeafe;
}

.stage-output pre {
  margin: 0;
  font-size: 13px;
  font-family: 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.checkpoint-artifacts {
  margin-top: 16px;
}

.checkpoint-artifacts .artifact-list {
  margin-top: 8px;
}

/* 检查点操作按钮 */
.checkpoint-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: #fef3c7;
  border-top: 1px solid #fcd34d;
}

/* 驳回按钮样式 */
.reject-section {
  margin-right: auto;
}

.btn-danger-outline {
  background: transparent;
  border: 1px solid #dc2626;
  color: #dc2626;
}

.btn-danger-outline:hover:not(:disabled) {
  background: #fef2f2;
}

.btn-danger {
  background: #dc2626;
  color: #ffffff;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

/* 驳回弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reject-dialog {
  background: #ffffff;
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2937;
}

.close-btn {
  padding: 4px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.dialog-body {
  padding: 24px;
}

.dialog-desc {
  margin: 0 0 16px;
  color: #6b7280;
  font-size: 14px;
}

.reject-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.reject-textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.reject-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #dc2626;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  border-radius: 0 0 12px 12px;
}

/* 阶段列表 */
.stages-section {
  max-width: 1000px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.empty-stages {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 20px;
  color: #9ca3af;
}

.empty-stages svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-stages p {
  margin: 0;
  font-size: 14px;
}

.stage-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.stage-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: #f9fafb;
  cursor: pointer;
  transition: background 0.2s;
}

.stage-card-header:hover {
  background: #f3f4f6;
}

.stage-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stage-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.icon-completed {
  background: #dcfce7;
  color: #166534;
}

.icon-running {
  background: #dbeafe;
  color: #1d4ed8;
}

.icon-failed {
  background: #fee2e2;
  color: #dc2626;
}

.icon-pending {
  background: #f3f4f6;
  color: #9ca3af;
}

.stage-icon.icon-running {
  animation: spin 1s linear infinite;
}

.stage-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.stage-duration {
  font-size: 12px;
  color: #9ca3af;
}

.expand-icon {
  color: #9ca3af;
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.stage-card-body {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.stage-error {
  padding: 12px;
  background: #fee2e2;
  border-radius: 6px;
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 12px;
}

.stage-output h4,
.stage-artifacts h4 {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.stage-output pre {
  margin: 0;
  padding: 12px;
  background: #1f2937;
  border-radius: 6px;
  font-size: 12px;
  font-family: 'Consolas', monospace;
  color: #f3f4f6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 300px;
  overflow-y: auto;
}

.stage-artifacts {
  margin-top: 16px;
}

.artifact-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artifact-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.artifact-icon {
  font-size: 16px;
}

.artifact-path {
  flex: 1;
  font-size: 13px;
  font-family: monospace;
  color: #374151;
}

.artifact-action {
  padding: 4px 10px;
  border: none;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.artifact-action:hover {
  background: #dbeafe;
}

/* 预览弹窗 */
.preview-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #1f2937;
}

.preview-header h3 {
  margin: 0;
  font-size: 14px;
  color: #f3f4f6;
  font-family: 'Consolas', monospace;
}

.preview-close {
  padding: 4px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
}

.preview-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.preview-body {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.preview-body pre {
  margin: 0;
  font-size: 14px;
  font-family: 'Consolas', monospace;
  color: #f3f4f6;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.preview-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #1f2937;
  border-top: 1px solid #374151;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast.success { background: #22c55e; color: #ffffff; }
.toast.error { background: #ef4444; color: #ffffff; }
.toast.info { background: #3b82f6; color: #ffffff; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(-50%) translateY(20px); }

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled { opacity: 0.6; cursor: not-allowed; }

.btn-primary {
  background: #2563eb;
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) { background: #1d4ed8; }

.btn-outline {
  background: transparent;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-outline:hover:not(:disabled) { background: #f3f4f6; }
</style>
