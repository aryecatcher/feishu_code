<template>
  <div class="pipeline-progress">
    <div class="progress-steps">
      <template v-for="(item, index) in displayItems" :key="item.key">
        <!-- 分支线条（reject 回归线） -->
        <div v-if="item.type === 'branch-line'" class="branch-line-container">
          <div class="branch-line" :class="{ 'rejected': item.branchStatus === 'rejected' }">
            <div class="branch-path"></div>
            <span class="branch-label">
              <span v-if="item.branchStatus === 'rejected'" class="reject-icon">✕</span>
              {{ item.branchLabel }}
            </span>
          </div>
        </div>

        <!-- 审批点 -->
        <div v-else-if="item.type === 'checkpoint'" class="progress-step checkpoint-step" :class="getCheckpointClass(item.status)">
          <div v-if="index > 0" class="step-line" :class="{ 'line-completed': item.status === 'approved' }"></div>

          <div class="step-node">
            <div class="node-circle checkpoint-circle">
              <span v-if="item.status === 'approved'" class="node-icon">✓</span>
              <span v-else-if="item.status === 'rejected'" class="node-icon">✕</span>
              <span v-else class="node-icon">?</span>
            </div>
            <span class="node-label checkpoint-label">{{ item.name }}</span>
          </div>

          <div class="step-status">
            <span v-if="item.status === 'approved'" class="status-badge status-approved">已通过</span>
            <span v-else-if="item.status === 'rejected'" class="status-badge status-rejected">已驳回</span>
            <span v-else class="status-badge status-waiting">待审批</span>
          </div>
        </div>

        <!-- 普通阶段 -->
        <div v-else class="progress-step" :class="{
          'is-completed': item.completed,
          'is-current': item.current,
          'is-pending': !item.completed && !item.current,
          'has-error': hasError && !item.completed
        }">
          <div v-if="index > 0" class="step-line" :class="{ 'line-completed': item.completed }"></div>

          <div class="step-node">
            <div class="node-circle">
              <span v-if="item.completed" class="node-icon">✓</span>
              <span v-else-if="item.current" class="node-icon spinning">⟳</span>
              <span v-else-if="hasError" class="node-icon">✕</span>
              <span v-else class="node-number">{{ index + 1 }}</span>
            </div>
            <span class="node-label">{{ item.name }}</span>
            <span v-if="item.duration" class="node-duration">{{ item.duration }}</span>
          </div>

          <div class="step-status">
            <span v-if="item.completed" class="status-badge status-completed">完成</span>
            <span v-else-if="item.current" class="status-badge status-running">进行中</span>
            <span v-else-if="hasError" class="status-badge status-error">失败</span>
            <span v-else class="status-badge status-pending">待执行</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Stage {
  id: string
  name: string
  duration?: string
  isCheckpoint?: boolean
}

interface CheckpointStatus {
  stageId: string
  status: 'pending' | 'approved' | 'rejected' | 'waiting_approval'
}

interface Props {
  stages: Stage[]
  currentStageId: string | string[]
  completedStageIds: string[]
  status: 'pending' | 'running' | 'waiting_approval' | 'completed' | 'failed'
  checkpoints?: CheckpointStatus[]
}

const props = withDefaults(defineProps<Props>(), {
  stages: () => [],
  currentStageId: () => [],
  completedStageIds: () => [],
  checkpoints: () => []
})

// 当前阶段可能是数组或单个值
const currentStageIds = computed(() => {
  return Array.isArray(props.currentStageId) ? props.currentStageId : [props.currentStageId]
})

const hasError = computed(() => props.status === 'failed')

// 审批点ID列表
const checkpointStageIds = computed(() => {
  return new Set(
    props.stages
      .filter(s => s.isCheckpoint || s.id === 'scheme-design' || s.id === 'code-review')
      .map(s => s.id)
  )
})

// 获取审批点状态
function getCheckpointStatus(stageId: string): string {
  const cp = props.checkpoints.find(c => c.stageId === stageId)
  return cp?.status || 'pending'
}

// 是否有审批点需要等待
const hasPendingCheckpoint = computed(() => {
  return props.status === 'waiting_approval' || props.checkpoints.some(c => 
    c.status === 'pending' || c.status === 'waiting_approval'
  )
})

// 展示项（阶段和审批点混合）
const displayItems = computed(() => {
  type DisplayItem = {
    key: string
    type: 'stage' | 'checkpoint' | 'branch-line'
    id?: string
    name: string
    completed?: boolean
    current?: boolean
    status?: string
    branchStatus?: string
    branchLabel?: string
    duration?: string
  }

  const items: DisplayItem[] = []

  let lastCheckpointStageId = ''

  for (let i = 0; i < props.stages.length; i++) {
    const stage = props.stages[i]
    const isCheckpoint = stage.isCheckpoint || stage.id === 'scheme-design' || stage.id === 'code-review'
    const isCurrent = currentStageIds.value.includes(stage.id)
    const isCompleted = props.completedStageIds.includes(stage.id)

    // 添加分支线条（如果在审批点之后，且当前不在该审批点之后）
    if (lastCheckpointStageId && !isCurrent && !isCompleted) {
      const lastCheckpointStatus = getCheckpointStatus(lastCheckpointStageId)
      if (lastCheckpointStatus === 'rejected') {
        items.push({
          key: `branch-${lastCheckpointStageId}`,
          type: 'branch-line',
          name: '',
          branchStatus: 'rejected',
          branchLabel: '驳回回归'
        })
      }
    }

    if (isCheckpoint) {
      // 审批点
      items.push({
        key: `checkpoint-${stage.id}`,
        type: 'checkpoint',
        id: stage.id,
        name: stage.name,
        status: getCheckpointStatus(stage.id)
      })
      lastCheckpointStageId = stage.id
    } else {
      // 普通阶段
      items.push({
        key: `stage-${stage.id}`,
        type: 'stage',
        id: stage.id,
        name: stage.name,
        completed: isCompleted,
        current: isCurrent && (props.status === 'running'),
        duration: stage.duration
      })
    }
  }

  return items
})

function getCheckpointClass(status: string | undefined) {
  return {
    'checkpoint-approved': status === 'approved',
    'checkpoint-rejected': status === 'rejected',
    'checkpoint-waiting': status === 'pending' || status === 'waiting_approval',
    'is-current': status === 'pending' || status === 'waiting_approval'
  }
}
</script>

<style scoped>
.pipeline-progress {
  padding: 20px 0;
}

.progress-steps {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
  padding: 0 10px;
}

.progress-step:first-child {
  padding-left: 0;
}

.progress-step:last-child {
  padding-right: 0;
}

/* 连接线 */
.step-line {
  position: absolute;
  top: 16px;
  left: -50%;
  width: 100%;
  height: 2px;
  background: #e5e7eb;
  z-index: 0;
}

.step-line.line-completed {
  background: #22c55e;
}

/* 步骤节点 */
.step-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
  background: #fff;
  padding: 0 12px;
}

.node-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  background: #ffffff;
  border: 2px solid #e5e7eb;
  color: #9ca3af;
}

.progress-step.is-completed .node-circle {
  background: #22c55e;
  border-color: #22c55e;
  color: #ffffff;
}

.progress-step.is-current .node-circle {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
}

.progress-step.has-error .node-circle {
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}

.node-icon {
  font-size: 16px;
}

.node-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.node-label {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  text-align: center;
  max-width: 80px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.progress-step.is-completed .node-label,
.progress-step.is-current .node-label {
  color: #1f2937;
}

.node-duration {
  margin-top: 2px;
  font-size: 11px;
  color: #9ca3af;
}

/* 状态标签 */
.step-status {
  margin-top: 8px;
  min-height: 22px;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.status-completed {
  background: #dcfce7;
  color: #166534;
}

.status-badge.status-running {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-badge.status-pending {
  background: #f3f4f6;
  color: #6b7280;
}

.status-badge.status-error {
  background: #fee2e2;
  color: #dc2626;
}

/* 审批点样式 */
.checkpoint-step {
  min-width: 80px;
}

.checkpoint-circle {
  width: 32px;
  height: 32px;
  font-size: 14px;
}

.checkpoint-label {
  color: #d97706;
  font-weight: 500;
}

.checkpoint-step.checkpoint-approved .checkpoint-circle {
  background: #22c55e;
  border-color: #22c55e;
}

.checkpoint-step.checkpoint-rejected .checkpoint-circle {
  background: #ef4444;
  border-color: #ef4444;
}

.checkpoint-step.checkpoint-waiting .checkpoint-circle {
  background: #fef3c7;
  border-color: #d97706;
  color: #d97706;
}

.checkpoint-step.checkpoint-waiting.is-current .checkpoint-circle {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(217, 119, 6, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(217, 119, 6, 0); }
}

.status-badge.status-approved {
  background: #dcfce7;
  color: #166534;
}

.status-badge.status-rejected {
  background: #fee2e2;
  color: #dc2626;
}

.status-badge.status-waiting {
  background: #fef3c7;
  color: #d97706;
}

/* 分支线条 */
.branch-line-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
}

.branch-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.branch-path {
  width: 2px;
  height: 30px;
  background: linear-gradient(to bottom, #e5e7eb, #9ca3af);
  border-radius: 1px;
}

.branch-line.rejected .branch-path {
  background: linear-gradient(to bottom, #ef4444, #fca5a5);
}

.branch-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #9ca3af;
  white-space: nowrap;
}

.branch-line.rejected .branch-label {
  color: #ef4444;
}

.reject-icon {
  font-size: 12px;
}

/* 响应式 */
@media (max-width: 640px) {
  .node-label {
    font-size: 11px;
    max-width: 60px;
  }

  .step-status {
    display: none;
  }
}
</style>
