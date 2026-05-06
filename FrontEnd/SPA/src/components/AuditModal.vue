<template>
  <div v-if="visible" class="audit-modal-mask" @click.self="handleClose">
    <div class="audit-modal">
      <!-- 弹窗头部 -->
      <div class="audit-modal-header">
        <div>
          <span class="audit-badge">人工审批</span>
          <h2 class="audit-title">{{ title }}</h2>
        </div>
        <button class="audit-close-btn" @click="handleClose" :disabled="loading" aria-label="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- 方案内容 -->
      <div class="audit-content">
        <div class="audit-section">
          <h3 class="audit-section-title">📋 后端返回方案</h3>
          <div class="audit-plan-content">
            {{ displayContent }}
          </div>
        </div>

        <!-- 检查点信息 -->
        <div class="audit-grid">
          <div class="audit-section">
            <h3 class="audit-section-title">ℹ️ 基础信息</h3>
            <ul class="audit-info-list">
              <li>
                <span class="info-label">运行ID：</span>
                <span class="info-value">{{ runId || '未获取' }}</span>
              </li>
              <li>
                <span class="info-label">检查点ID：</span>
                <span class="info-value">{{ checkpointIdentifier }}</span>
              </li>
              <li>
                <span class="info-label">建议动作：</span>
                <span class="info-value" :class="actionClass">
                  {{ actionLabel }}
                </span>
              </li>
              <li>
                <span class="info-label">阶段ID：</span>
                <span class="info-value">{{ auditData?.stage_id || auditData?.resolution?.context_id || '未获取' }}</span>
              </li>
            </ul>
          </div>

          <div class="audit-section">
            <h3 class="audit-section-title">🔍 原始返回</h3>
            <pre class="audit-raw-json">{{ formattedAuditData }}</pre>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="audit-footer">
        <button 
          class="audit-btn audit-btn-reject" 
          @click="handleAction('reject')" 
          :disabled="loading"
        >
          {{ loading ? '处理中...' : '驳回' }}
        </button>
        <button 
          class="audit-btn audit-btn-approve" 
          @click="handleAction('approve')" 
          :disabled="loading"
        >
          {{ loading ? '处理中...' : '通过' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { apiClient } from '../main'

// 组件入参
interface Props {
  /** 弹窗显隐状态，支持v-model */
  visible: boolean
  /** 后端返回的审批数据 */
  auditData?: Record<string, any> | null
  /** 当前运行实例ID */
  runId?: string | number
  /** 弹窗标题 */
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  auditData: null,
  runId: '',
  title: '请确认方案内容'
})

// 事件抛出
const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': [action: 'approve' | 'reject', result: any]
  'error': [action: 'approve' | 'reject', error: any]
  'close': []
}>()

const loading = ref(false)

// 格式化原始返回数据
const formattedAuditData = computed(() => {
  return props.auditData ? JSON.stringify(props.auditData, null, 2) : '{}'
})

const displayContent = computed(() => {
  return (
    props.auditData?.content ||
    props.auditData?.reviews ||
    props.auditData?.stage_result?.output ||
    props.auditData?.stage_result?.content ||
    '后端暂未返回方案内容'
  )
})

const checkpointIdentifier = computed(() => {
  return props.auditData?.checkpoint_id || props.auditData?.id || '未获取'
})

const actionLabel = computed(() => {
  const resolutionAction = props.auditData?.resolution?.action
  const approvalAction = props.auditData?.approval_action
  if (resolutionAction === 'accept' || approvalAction === 'approve') return '通过'
  if (resolutionAction === 'reject' || approvalAction === 'reject') return '驳回'
  return '待确认'
})

// 建议动作样式类
const actionClass = computed(() => {
  const action = props.auditData?.resolution?.action || props.auditData?.approval_action
  return {
    'text-green-600': action === 'accept' || action === 'approve',
    'text-red-600': action === 'reject',
    'text-orange-600': !action
  }
})

// 关闭弹窗
function handleClose() {
  if (loading.value) return
  emit('update:visible', false)
  emit('close')
}

// 处理审批操作
async function handleAction(action: 'approve' | 'reject') {
  if (!props.auditData || !props.runId) {
    console.error('缺少必要参数：runId 或 auditData')
    return
  }

  try {
    loading.value = true
    const runId = String(props.runId)
    const stageId = String(props.auditData.stage_id || props.auditData.checkpoint_id)
    
    let result
    if (action === 'approve') {
      // 调用通过接口
      result = await apiClient.checkpoint.approveCheckpointApiCheckpointsExecutionIdStageIdApprovePost(
        runId,
        stageId,
        {
          comment: '审批通过',
          approver: 'frontend-user',
        }
      )
    } else {
      // 调用驳回接口
      result = await apiClient.checkpoint.rejectCheckpointApiCheckpointsExecutionIdStageIdRejectPost(
        runId,
        stageId,
        {
          comment: '审批驳回',
          rejector: 'frontend-user',
        }
      )
    }

    emit('success', action, result)
    handleClose()
  } catch (err) {
    console.error(`审批${action === 'approve' ? '通过' : '驳回'}失败：`, err)
    emit('error', action, err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.audit-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.audit-modal {
  width: min(840px, 92vw);
  max-height: min(760px, 90vh);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部 */
.audit-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e7ebf3;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.audit-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  background: #fef3c7;
  color: #d97706;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}

.audit-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.audit-close-btn {
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 8px;
  padding: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.audit-close-btn:hover:not(:disabled) {
  background: #e5e7eb;
  color: #374151;
}

.audit-close-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 内容区 */
.audit-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

.audit-section {
  margin-bottom: 24px;
}

.audit-section-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.audit-plan-content {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  min-height: 80px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-all;
  color: #1f2937;
  font-size: 14px;
}

.audit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.audit-info-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.audit-info-list li {
  padding: 6px 0;
  font-size: 14px;
  display: flex;
}

.info-label {
  color: #6b7280;
  min-width: 80px;
}

.info-value {
  color: #1f2937;
  flex: 1;
}

.text-green-600 {
  color: #059669;
}

.text-red-600 {
  color: #dc2626;
}

.text-orange-600 {
  color: #d97706;
}

.audit-raw-json {
  background: #1f2937;
  color: #f3f4f6;
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  overflow: auto;
  max-height: 200px;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
}

/* 底部操作区 */
.audit-footer {
  padding: 20px 24px;
  border-top: 1px solid #e7ebf3;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.audit-btn {
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.audit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.audit-btn-reject {
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.audit-btn-reject:hover:not(:disabled) {
  background: #fecaca;
}

.audit-btn-approve {
  background: #2563eb;
  color: white;
}

.audit-btn-approve:hover:not(:disabled) {
  background: #1d4ed8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* 响应式 */
@media (max-width: 768px) {
  .audit-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .audit-modal {
    width: calc(100% - 24px);
    max-height: calc(100vh - 40px);
  }
}
</style>
