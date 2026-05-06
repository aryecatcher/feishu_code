<template>
  <div class="execute-page">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </button>
      <h1>新建执行</h1>
      <button class="history-btn" @click="goHistory">
        历史记录
      </button>
    </div>

    <div class="execute-container">
      <!-- 需求输入区 -->
      <section class="form-section">
        <h2 class="section-title">
          <span class="section-number">1</span>
          需求描述
        </h2>

        <div class="form-group">
          <label class="form-label">
            需求描述 <span class="required">*</span>
          </label>
          <textarea
            v-model="form.demand"
            class="form-textarea"
            placeholder="请详细描述你的需求，例如：&#10;- 生成一个 FastAPI 用户管理服务&#10;- 包含注册、登录、CRUD 接口&#10;- 使用 SQLite 存储数据&#10;- 需要 JWT 认证"
            rows="8"
          ></textarea>
          <div class="form-hint">
            描述越详细，AI 理解越准确
          </div>
        </div>

        <!-- 代码库关联 -->
        <div class="form-group">
          <label class="form-label collapsible" @click="showAdvanced = !showAdvanced">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: showAdvanced }">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
            可选：关联代码库
          </label>

          <div v-show="showAdvanced" class="advanced-fields">
            <div class="field-row">
              <label class="field-label">项目路径</label>
              <input
                v-model="form.context.repoPath"
                type="text"
                class="form-input"
                placeholder="/path/to/your/project"
              />
              <button class="btn btn-outline btn-sm" @click="browseRepo">
                浏览
              </button>
            </div>

            <div class="field-row">
              <label class="field-label">聚焦文件</label>
              <div class="focus-files">
                <div v-for="(file, index) in form.context.focusFiles" :key="index" class="focus-file-item">
                  <input
                    v-model="form.context.focusFiles[index]"
                    type="text"
                    class="form-input"
                    placeholder="src/main.py:10-50"
                  />
                  <button class="remove-btn" @click="removeFocusFile(index)" title="移除">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </button>
                </div>
                <button class="add-file-btn" @click="addFocusFile">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  添加文件
                </button>
              </div>
              <div class="form-hint">
                支持指定行号范围：src/main.py:10-50
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 执行配置区 -->
      <section class="form-section">
        <h2 class="section-title">
          <span class="section-number">2</span>
          执行配置
        </h2>

        <div class="form-group">
          <label class="form-label">流水线模板</label>
          <select v-model="form.pipelineId" class="form-select">
            <option value="default">默认流水线</option>
            <option v-for="p in pipelines" :key="p.id" :value="p.id">
              {{ p.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">执行选项</label>
          <div class="checkbox-group">
            <label class="checkbox-item">
              <input type="checkbox" v-model="form.enableCheckpoint" />
              <span class="checkmark"></span>
              <span class="checkbox-text">
                启用人工审批
                <span class="checkbox-desc">每个关键阶段完成后需人工确认</span>
              </span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" v-model="form.autoExecute" />
              <span class="checkmark"></span>
              <span class="checkbox-text">
                自动执行模式
                <span class="checkbox-desc">跳过人工审批，直接执行所有阶段</span>
              </span>
            </label>
          </div>
        </div>
      </section>

      <!-- 快捷模板区 -->
      <section class="form-section templates-section">
        <h2 class="section-title">
          <span class="section-number">3</span>
          快速开始
        </h2>
        <div class="template-grid">
          <button
            v-for="template in quickTemplates"
            :key="template.id"
            class="template-card"
            @click="applyTemplate(template)"
          >
            <span class="template-icon">{{ template.icon }}</span>
            <span class="template-name">{{ template.name }}</span>
            <span class="template-desc">{{ template.description }}</span>
          </button>
        </div>
      </section>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <button
          class="btn btn-primary btn-lg"
          @click="startExecution"
          :disabled="!canSubmit || loading"
        >
          <svg v-if="loading" class="spinning" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          {{ loading ? '创建中...' : '开始执行' }}
        </button>
        <p class="submit-hint" v-if="!canSubmit">
          请输入需求描述
        </p>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '../api/devflow'

const router = useRouter()

// ============= State =============

const loading = ref(false)
const showAdvanced = ref(false)
const toast = ref({
  show: false,
  message: '',
  type: 'success' as 'success' | 'error' | 'info'
})

interface Pipeline {
  id: string
  name: string
  description?: string
}

const pipelines = ref<Pipeline[]>([])

const form = ref({
  demand: '',
  pipelineId: 'default',
  enableCheckpoint: true,
  autoExecute: false,
  context: {
    repoPath: '',
    focusFiles: ['']
  }
})

const quickTemplates = [
  {
    id: 'api-service',
    name: 'API 服务',
    icon: '🚀',
    description: 'FastAPI/Flask RESTful 服务',
    demand: '生成一个 FastAPI RESTful API 服务，包含：\n1. 用户管理 CRUD\n2. JWT 认证\n3. 使用 SQLAlchemy + SQLite\n4. 包含完整的 Dockerfile'
  },
  {
    id: 'frontend-app',
    name: '前端应用',
    icon: '⚛️',
    description: 'Vue/React 单页应用',
    demand: '生成一个 Vue3 单页应用，包含：\n1. 用户登录/注册页面\n2. 仪表盘页面\n3. 使用 TailwindCSS 样式\n4. 包含 Docker 配置'
  },
  {
    id: 'script-tool',
    name: '脚本工具',
    icon: '📟',
    description: 'Python/Shell 脚本',
    demand: '生成一个 Python 数据处理脚本，包含：\n1. CSV/Excel 数据读取\n2. 数据清洗和转换\n3. 结果导出\n4. 使用 pandas 库'
  },
  {
    id: 'full-stack',
    name: '全栈项目',
    icon: '🎯',
    description: '前后端完整项目',
    demand: '生成一个前后端分离项目，包含：\n1. FastAPI 后端 RESTful API\n2. Vue3 前端 SPA\n3. Docker Compose 部署配置\n4. 包含用户认证功能'
  }
]

// ============= Computed =============

const canSubmit = computed(() => {
  return form.value.demand.trim().length > 0
})

// ============= Methods =============

function goBack() {
  router.push('/')
}

function goHistory() {
  router.push('/executions')
}

function addFocusFile() {
  form.value.context.focusFiles.push('')
}

function removeFocusFile(index: number) {
  form.value.context.focusFiles.splice(index, 1)
  if (form.value.context.focusFiles.length === 0) {
    form.value.context.focusFiles.push('')
  }
}

function browseRepo() {
  // TODO: 实现文件浏览器
  showToast('文件浏览器功能开发中', 'info')
}

function applyTemplate(template: typeof quickTemplates[0]) {
  form.value.demand = template.demand
}

async function fetchPipelines() {
  try {
    const result = await apiService.getDefaultPipeline()
    if (result.default_pipeline) {
      pipelines.value = [result.default_pipeline]
    }
  } catch (error) {
    console.error('Failed to fetch pipelines:', error)
  }
}

async function startExecution() {
  if (!canSubmit.value) return

  loading.value = true

  try {
    // 构造上下文
    const context: Record<string, any> = {}
    if (form.value.context.repoPath) {
      context.repo_path = form.value.context.repoPath
    }
    if (form.value.context.focusFiles.some(f => f.trim())) {
      context.focus_files = form.value.context.focusFiles
        .filter(f => f.trim())
        .map(f => {
          // 解析文件路径和行号范围
          const match = f.match(/^(.+?)(?::(\d+)(?:-(\d+))?)?$/)
          if (match) {
            return {
              path: match[1],
              start_line: match[2] ? parseInt(match[2]) : undefined,
              end_line: match[3] ? parseInt(match[3]) : undefined
            }
          }
          return { path: f }
        })
    }

    // 调用 API 创建执行
    const result = await apiService.createExecution({
      pipeline_id: form.value.pipelineId || 'default',
      demand: form.value.demand,
      config: {
        auto_execute: form.value.autoExecute,
        enable_checkpoint: form.value.enableCheckpoint
      },
      context: Object.keys(context).length > 0 ? context : undefined
    })

    showToast('执行已创建，正在跳转...', 'success')

    // 跳转到执行详情页
    setTimeout(() => {
      router.push(`/execute/${result.id}`)
    }, 500)

  } catch (error: any) {
    console.error('Failed to start execution:', error)
    showToast(error?.response?.data?.detail || '创建执行失败', 'error')
  } finally {
    loading.value = false
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
  fetchPipelines()
})
</script>

<style scoped>
.execute-page {
  min-height: 100vh;
  background: #f9fafb;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 900px;
  margin: 0 auto 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.back-btn,
.history-btn {
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

.back-btn:hover,
.history-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.execute-container {
  max-width: 900px;
  margin: 0 auto;
}

/* 表单区块 */
.form-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.section-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #2563eb;
  color: #ffffff;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-label.collapsible {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #6b7280;
  user-select: none;
}

.form-label.collapsible svg {
  transition: transform 0.2s;
}

.form-label.collapsible svg.rotated {
  transform: rotate(90deg);
}

.required {
  color: #ef4444;
}

.form-textarea,
.form-input,
.form-select {
  width: 100%;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  background: #ffffff;
  transition: all 0.2s;
}

.form-textarea {
  resize: vertical;
  min-height: 160px;
  line-height: 1.6;
}

.form-textarea:focus,
.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}

/* 高级选项 */
.advanced-fields {
  padding-top: 12px;
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.field-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.field-row:last-child {
  margin-bottom: 0;
}

.field-label {
  min-width: 70px;
  font-size: 13px;
  color: #6b7280;
}

.field-row .form-input {
  flex: 1;
}

.focus-files {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.focus-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.focus-file-item .form-input {
  flex: 1;
}

.remove-btn {
  padding: 6px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.add-file-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px dashed #d1d5db;
  background: transparent;
  color: #6b7280;
  font-size: 13px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.add-file-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
  background: #eff6ff;
}

/* 复选框组 */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  padding: 12px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
}

.checkbox-item:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.checkbox-item input {
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
  flex-shrink: 0;
  transition: all 0.2s;
  margin-top: 2px;
}

.checkbox-item input:checked + .checkmark {
  background: #2563eb;
  border-color: #2563eb;
}

.checkbox-item input:checked + .checkmark::after {
  content: '✓';
  color: #ffffff;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-text {
  font-size: 14px;
  color: #374151;
}

.checkbox-desc {
  display: block;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 快捷模板 */
.templates-section .template-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.template-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.template-card:hover {
  border-color: #2563eb;
  background: #eff6ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15);
}

.template-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.template-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.template-desc {
  font-size: 12px;
  color: #9ca3af;
}

/* 提交按钮 */
.submit-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
}

.btn-lg {
  padding: 14px 48px;
  font-size: 16px;
}

.submit-hint {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
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
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.btn-outline {
  background: transparent;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn-outline:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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

/* 响应式 */
@media (max-width: 640px) {
  .templates-section .template-grid {
    grid-template-columns: 1fr;
  }

  .field-row {
    flex-direction: column;
    align-items: stretch;
  }

  .field-label {
    margin-bottom: 4px;
  }
}
</style>
