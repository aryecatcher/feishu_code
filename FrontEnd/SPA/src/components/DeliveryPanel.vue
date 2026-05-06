<template>
  <div v-if="visible" class="delivery-modal-mask" @click.self="handleClose">
    <div class="delivery-modal">
      <!-- 弹窗头部 -->
      <div class="delivery-modal-header">
        <div>
          <span class="delivery-badge">交付物</span>
          <h2 class="delivery-title">{{ title }}</h2>
        </div>
        <div class="header-actions">
          <button class="btn btn-outline" @click="handleDownloadAll" :disabled="loading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            打包下载
          </button>
          <button class="delivery-close-btn" @click="handleClose" aria-label="关闭">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

      <!-- Tab 切换 -->
      <div class="delivery-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </button>
      </div>

      <!-- 内容区 -->
      <div class="delivery-content">
        <!-- 代码文件 Tab -->
        <div v-if="activeTab === 'code'" class="tab-panel">
          <div v-if="artifacts.length === 0" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <p>暂无生成文件</p>
          </div>
          <div v-else class="file-list">
            <div v-for="(file, index) in artifacts" :key="index" class="file-card">
              <div class="file-header">
                <div class="file-info">
                  <span class="file-icon">{{ getFileIcon(file.path) }}</span>
                  <span class="file-path">{{ file.path }}</span>
                </div>
                <div class="file-actions">
                  <button class="action-btn" @click="previewFile(file)" title="预览">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  </button>
                  <button class="action-btn" @click="copyFile(file)" title="复制">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                  </button>
                  <button class="action-btn" @click="downloadFile(file)" title="下载">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </button>
                </div>
              </div>
              <pre class="file-preview"><code>{{ truncateCode(file.content, 300) }}</code></pre>
            </div>
          </div>
        </div>

        <!-- 部署指南 Tab -->
        <div v-if="activeTab === 'deploy'" class="tab-panel">
          <div v-if="!deliveryData?.deployment_steps?.length" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <p>暂无部署指南</p>
          </div>
          <div v-else class="deploy-guide">
            <!-- 概览信息 -->
            <div class="deploy-overview">
              <div class="overview-item">
                <span class="overview-label">预计耗时</span>
                <span class="overview-value">{{ deliveryData?.estimated_time || '5 分钟' }}</span>
              </div>
              <div class="overview-item">
                <span class="overview-label">访问地址</span>
                <span class="overview-value">{{ deliveryData?.access_url || 'http://localhost:8000' }}</span>
              </div>
              <div class="overview-item">
                <span class="overview-label">步骤数</span>
                <span class="overview-value">{{ deliveryData?.deployment_steps?.length || 0 }} 步</span>
              </div>
            </div>

            <!-- 部署步骤 -->
            <div class="steps-list">
              <div
                v-for="(step, index) in deliveryData?.deployment_steps"
                :key="index"
                class="step-card"
              >
                <div class="step-number">{{ index + 1 }}</div>
                <div class="step-content">
                  <h4 class="step-title">{{ step.action || step.title }}</h4>
                  <p class="step-description">{{ step.description || step.verification || '' }}</p>
                  <div v-if="step.command" class="step-command">
                    <code>{{ step.command }}</code>
                    <button class="copy-btn" @click="copyToClipboard(step.command)" title="复制命令">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 一键脚本 Tab -->
        <div v-if="activeTab === 'script'" class="tab-panel">
          <div v-if="!deliveryData?.deployment_script" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="4 17 10 11 4 5"></polyline>
              <line x1="12" y1="19" x2="20" y2="19"></line>
            </svg>
            <p>暂无部署脚本</p>
          </div>
          <div v-else class="script-panel">
            <div class="script-header">
              <h3>部署脚本</h3>
              <button class="btn btn-primary" @click="copyScript">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                一键复制
              </button>
            </div>
            <pre class="deploy-script"><code>{{ deliveryData.deployment_script }}</code></pre>
            <div class="script-tip">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
              复制后在终端粘贴执行即可
            </div>
          </div>
        </div>

        <!-- 检查清单 Tab -->
        <div v-if="activeTab === 'checklist'" class="tab-panel">
          <div v-if="!checklist.length" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 11l3 3L22 4"></path>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
            </svg>
            <p>暂无检查清单</p>
          </div>
          <div v-else class="checklist-panel">
            <div class="checklist-progress">
              <span>完成进度</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${checklistProgress}%` }"></div>
              </div>
              <span class="progress-text">{{ checkedCount }}/{{ checklist.length }}</span>
            </div>
            <div class="checklist-items">
              <label
                v-for="(item, index) in checklist"
                :key="index"
                class="checklist-item"
              >
                <input type="checkbox" v-model="item.checked" />
                <span class="checkmark"></span>
                <span class="item-text">{{ item.text }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- 文件预览弹窗 -->
      <div v-if="previewFileData" class="preview-modal">
        <div class="preview-header">
          <h3>{{ previewFileData.path }}</h3>
          <button class="preview-close" @click="previewFileData = null">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="preview-body">
          <pre><code>{{ previewFileData.content }}</code></pre>
        </div>
        <div class="preview-footer">
          <button class="btn btn-outline" @click="copyFile(previewFileData)">
            复制内容
          </button>
          <button class="btn btn-primary" @click="downloadFile(previewFileData)">
            下载文件
          </button>
        </div>
      </div>

      <!-- Toast 提示 -->
      <transition name="toast">
        <div v-if="toast.show" class="toast" :class="toast.type">
          {{ toast.message }}
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { apiService } from '../api/devflow'

// ============= Types =============

export interface Artifact {
  path: string
  content: string
  change_type?: string
  language?: string
  description?: string
}

export interface DeploymentStep {
  action?: string
  title?: string
  command?: string
  description?: string
  verification?: string
}

export interface DeliveryData {
  artifacts?: Artifact[]
  deployment_steps?: DeploymentStep[]
  deployment_script?: string
  estimated_time?: string
  access_url?: string
  checklist?: string[]
  summary?: string
}

interface Props {
  visible: boolean
  executionId?: string
  deliveryData?: DeliveryData | null
  title?: string
}

interface Tab {
  id: string
  label: string
  icon: string
}

// ============= Props & Emits =============

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  executionId: '',
  deliveryData: null,
  title: '交付物详情'
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'close': []
}>()

// ============= State =============

const tabs: Tab[] = [
  { id: 'code', label: '代码', icon: '📄' },
  { id: 'deploy', label: '部署', icon: '🚀' },
  { id: 'script', label: '脚本', icon: '⚡' },
  { id: 'checklist', label: '清单', icon: '✅' }
]

const activeTab = ref('code')
const loading = ref(false)
const previewFileData = ref<Artifact | null>(null)
const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error' | 'info'
})

// 本地 checklist 状态（用于交互）
const checklist = ref<Array<{ text: string; checked: boolean }>>([])

// ============= Computed =============

const artifacts = computed(() => {
  return props.deliveryData?.artifacts || []
})

const checklistProgress = computed(() => {
  if (!checklist.value.length) return 0
  const checked = checklist.value.filter(i => i.checked).length
  return Math.round((checked / checklist.value.length) * 100)
})

const checkedCount = computed(() => {
  return checklist.value.filter(i => i.checked).length
})

// ============= Methods =============

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

function getFileIcon(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || ''
  const iconMap: Record<string, string> = {
    py: '🐍',
    js: '📜',
    ts: '🔷',
    vue: '💚',
    jsx: '⚛️',
    tsx: '⚛️',
    html: '🌐',
    css: '🎨',
    scss: '🎨',
    json: '📋',
    yaml: '⚙️',
    yml: '⚙️',
    md: '📝',
    txt: '📃',
    sh: '📟',
    bash: '📟',
    dockerfile: '🐳',
    dockerfile_prod: '🐳',
    env: '🔐',
    gitignore: '🔒',
    lock: '🔒'
  }
  return iconMap[ext] || '📄'
}

function truncateCode(code: string, maxLines: number): string {
  const lines = code.split('\n')
  if (lines.length <= maxLines) return code
  return lines.slice(0, maxLines).join('\n') + '\n\n... (内容过长，查看完整内容请使用预览)'
}

function previewFile(file: Artifact) {
  previewFileData.value = file
}

async function copyFile(file: Artifact) {
  await copyToClipboard(file.content)
  showToast('文件内容已复制', 'success')
}

async function copyScript() {
  if (!props.deliveryData?.deployment_script) return
  await copyToClipboard(props.deliveryData.deployment_script)
  showToast('脚本已复制到剪贴板', 'success')
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}

async function downloadFile(file: Artifact) {
  const blob = new Blob([file.content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = file.path.split('/').pop() || 'file'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  showToast(`已下载: ${file.path}`, 'success')
}

async function handleDownloadAll() {
  if (!artifacts.value.length) {
    showToast('没有可下载的文件', 'error')
    return
  }

  loading.value = true
  try {
    // 如果有服务端 API，先调用 API 打包
    if (props.executionId) {
      // 调用后端打包下载接口
      // const response = await apiService.downloadArtifacts(props.executionId)
      // window.open(response.download_url, '_blank')
    }

    // 客户端打包（备选方案）
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()

    for (const file of artifacts.value) {
      zip.file(file.path, file.content)
    }

    const content = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(content)
    const a = document.createElement('a')
    a.href = url
    a.download = `artifacts-${props.executionId || Date.now()}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    showToast('打包下载成功', 'success')
  } catch (error) {
    console.error('Download error:', error)
    showToast('打包下载失败', 'error')
  } finally {
    loading.value = false
  }
}

function showToast(message: string, type: 'success' | 'error' | 'info' = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 2500)
}

// ============= Watch =============

watch(() => props.visible, (newVal) => {
  if (newVal) {
    // 初始化 checklist
    const defaultChecklist = props.deliveryData?.checklist || [
      '安装项目依赖',
      '配置环境变量',
      '启动服务',
      '验证健康状态',
      '测试核心功能'
    ]
    checklist.value = defaultChecklist.map(text => ({ text, checked: false }))
  }
})

watch(() => props.deliveryData, (newVal) => {
  if (newVal?.checklist) {
    checklist.value = newVal.checklist.map(text => ({ text, checked: false }))
  }
}, { deep: true })
</script>

<style scoped>
/* Modal 基础样式 */
.delivery-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.delivery-modal {
  width: min(960px, 92vw);
  max-height: min(800px, 90vh);
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* 头部 */
.delivery-modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e7ebf3;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.delivery-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}

.delivery-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.delivery-close-btn {
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

.delivery-close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

/* Tabs */
.delivery-tabs {
  display: flex;
  gap: 4px;
  padding: 0 24px;
  background: #f9fafb;
  border-bottom: 1px solid #e7ebf3;
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #374151;
  background: #f3f4f6;
}

.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: #ffffff;
}

.tab-icon {
  font-size: 16px;
}

/* 内容区 */
.delivery-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.tab-panel {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 15px;
}

/* 文件列表 */
.file-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  font-size: 18px;
}

.file-path {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  font-family: 'Consolas', 'Monaco', monospace;
}

.file-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  padding: 6px 8px;
  border: none;
  background: transparent;
  color: #6b7280;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.action-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.file-preview {
  margin: 0;
  padding: 16px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  line-height: 1.6;
  background: #1f2937;
  color: #f3f4f6;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.file-preview code {
  white-space: pre;
}

/* 部署指南 */
.deploy-overview {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f0fdf4;
  border-radius: 8px;
  margin-bottom: 24px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.overview-label {
  font-size: 12px;
  color: #6b7280;
}

.overview-value {
  font-size: 14px;
  font-weight: 600;
  color: #166534;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
}

.step-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.step-description {
  margin: 0 0 8px;
  font-size: 14px;
  color: #6b7280;
}

.step-command {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1f2937;
  border-radius: 6px;
  padding: 8px 12px;
}

.step-command code {
  flex: 1;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #f3f4f6;
  white-space: pre-wrap;
  word-break: break-all;
}

.copy-btn {
  padding: 4px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

/* 脚本面板 */
.script-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.script-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.deploy-script {
  margin: 0;
  padding: 20px;
  background: #1f2937;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Consolas', 'Monaco', monospace;
  color: #f3f4f6;
  line-height: 1.7;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.script-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef3c7;
  border-radius: 8px;
  color: #92400e;
  font-size: 14px;
}

/* 检查清单 */
.checklist-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.checklist-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f0fdf4;
  border-radius: 8px;
}

.checklist-progress span {
  font-size: 14px;
  color: #166534;
  font-weight: 500;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #d1fae5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #22c55e;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  min-width: 40px;
  text-align: right;
}

.checklist-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.checklist-item:hover {
  border-color: #22c55e;
  background: #f0fdf4;
}

.checklist-item input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.checklist-item input:checked + .checkmark {
  background: #22c55e;
  border-color: #22c55e;
}

.checklist-item input:checked + .checkmark::after {
  content: '✓';
  color: #ffffff;
  font-size: 12px;
  font-weight: bold;
}

.item-text {
  font-size: 14px;
  color: #374151;
  transition: all 0.2s;
}

.checklist-item input:checked ~ .item-text {
  color: #6b7280;
  text-decoration: line-through;
}

/* 预览弹窗 */
.preview-modal {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  z-index: 10;
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
  font-family: 'Consolas', 'Monaco', monospace;
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
  font-family: 'Consolas', 'Monaco', monospace;
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
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 20;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast.success {
  background: #22c55e;
  color: #ffffff;
}

.toast.error {
  background: #ef4444;
  color: #ffffff;
}

.toast.info {
  background: #3b82f6;
  color: #ffffff;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #2563eb;
  color: #ffffff;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-outline {
  background: transparent;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-outline:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* 响应式 */
@media (max-width: 768px) {
  .delivery-tabs {
    overflow-x: auto;
    padding: 0 16px;
  }

  .tab-btn {
    padding: 10px 16px;
    white-space: nowrap;
  }

  .deploy-overview {
    flex-wrap: wrap;
  }

  .overview-item {
    flex: 1 1 100px;
  }
}
</style>
