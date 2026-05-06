<template>
  <section class="workflow-page container">
    <aside class="panel node-lib">
      <h2>节点库</h2>
      <div class="node-group" v-for="group in nodeGroups" :key="group.title">
        <p class="group-title">{{ group.title }}</p>
        <button
          class="node-item"
          v-for="node in group.items"
          :key="node.key"
          @click="addNode(node)"
        >
          <span>{{ node.title }}</span>
          <small>点击添加到画布</small>
        </button>
      </div>
    </aside>

    <div class="panel canvas-panel">
      <div class="canvas-head">
        <div>
          <h2>流水线画布</h2>
          <p class="canvas-status">
            当前状态：{{ statusText }}
            <span v-if="currentExecutionId"> | 执行ID：{{ currentExecutionId }}</span>
            <span v-if="progress > 0"> | 进度：{{ progress }}%</span>
          </p>
        </div>
        <div class="canvas-actions">
          <button class="btn btn-ghost" @click="openLatestCheckpoint" :disabled="!currentExecutionId">
            打开审批
          </button>
          <button class="btn btn-primary" @click="runPipeline" :disabled="running">
            {{ running ? '执行中...' : '运行流水线' }}
          </button>
        </div>
      </div>

      <div class="canvas-toolbar">
        <input
          v-model.trim="demand"
          class="demand-input"
          type="text"
          placeholder="请输入要交给流水线执行的需求"
        />
        <p class="toolbar-tip">
          提示：点击左侧节点添加到画布，拖动节点调整位置，拖拽节点左右两侧的锚点可创建连线。
        </p>
      </div>

      <div class="canvas-body">
        <VueFlow
          v-model:nodes="flowNodes"
          v-model:edges="flowEdges"
          class="workflow-flow"
          :default-zoom="1"
          :min-zoom="0.4"
          :max-zoom="1.8"
          :fit-view-on-init="true"
          :select-nodes-on-drag="false"
          @connect="handleConnect"
          @node-click="handleNodeClick"
          @pane-click="clearSelection"
          @nodes-delete="handleNodesDelete"
        >
          <Background :gap="20" :size="1" pattern-color="#e5ecf7" />
          <Controls position="bottom-right" />

          <template #node-workflow="{ data, selected }">
            <div class="workflow-node" :class="[data.kind, { selected }]">
              <Handle
                v-if="data.kind !== 'start'"
                type="target"
                :position="Position.Left"
                class="workflow-handle"
              />
              <div class="node-badge">{{ data.kindLabel }}</div>
              <strong>{{ data.title }}</strong>
              <small>{{ data.model || '无需模型配置' }}</small>
              <Handle
                v-if="data.kind !== 'end'"
                type="source"
                :position="Position.Right"
                class="workflow-handle"
              />
            </div>
          </template>
        </VueFlow>
      </div>
    </div>

    <aside class="panel config-panel">
      <h2>节点配置</h2>

      <div v-if="selectedNode" class="config-content">
        <p class="config-selected">当前选中：{{ selectedNode.data!.title }}</p>
        <label>
          节点名称
          <input v-model="form.nodeName" type="text" />
        </label>
        <label>
          模型
          <select v-model="form.model">
            <option value="">无</option>
            <option>GPT-4o</option>
            <option>DeepSeek-V3</option>
            <option>Claude Sonnet</option>
          </select>
        </label>
        <label>
          系统提示词
          <textarea v-model="form.prompt" rows="5"></textarea>
        </label>
        <label>
          最大 Token
          <input v-model.number="form.maxTokens" type="number" min="0" step="128" />
        </label>
        <div class="config-actions">
          <button class="btn btn-ghost" @click="removeSelectedNode">删除节点</button>
        </div>
      </div>

      <div v-else class="config-empty">
        <p>当前未选中节点。</p>
        <p>你可以点击画布中的节点，或从左侧节点库新增一个节点开始配置。</p>
      </div>
    </aside>
  </section>

  <AuditModal
    v-model:visible="showAuditModal"
    :audit-data="auditData"
    :run-id="currentRunId"
    title="请确认需求分析方案"
    @success="handleAuditSuccess"
    @error="handleAuditError"
  />
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import {
  VueFlow,
  Handle,
  MarkerType,
  Position,
  addEdge,
  type Connection,
  type Edge,
  type Node as FlowNode,
} from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import AuditModal from '../components/AuditModal.vue'
import { apiClient } from '../main'
import { ExecutionStatus } from '../api/generated'

interface NodeCatalogItem {
  key: string
  title: string
  kind: string
  kindLabel: string
  defaultModel: string
  defaultPrompt: string
  defaultMaxTokens: number
}

interface NodeGroup {
  title: string
  items: NodeCatalogItem[]
}

interface WorkflowNodeData {
  title: string
  kind: string
  kindLabel: string
  model: string
  prompt: string
  maxTokens: number
}

const nodeGroups: NodeGroup[] = [
  {
    title: 'AI 节点',
    items: [
      {
        key: 'llm-chat',
        title: 'LLM 对话',
        kind: 'llm',
        kindLabel: 'AI',
        defaultModel: 'GPT-4o',
        defaultPrompt: '你是通用对话助手，请输出结构化结果。',
        defaultMaxTokens: 2048,
      },
      {
        key: 'multi-agent',
        title: '多 Agent 协作',
        kind: 'agent',
        kindLabel: 'Agent',
        defaultModel: 'Claude Sonnet',
        defaultPrompt: '请协调多个智能体分工执行并最终汇总。',
        defaultMaxTokens: 3072,
      },
      {
        key: 'rag',
        title: 'RAG 检索',
        kind: 'search',
        kindLabel: '检索',
        defaultModel: 'DeepSeek-V3',
        defaultPrompt: '请根据知识库检索结果给出可信答案。',
        defaultMaxTokens: 2048,
      },
    ],
  },
  {
    title: '工具节点',
    items: [
      {
        key: 'http',
        title: 'HTTP 请求',
        kind: 'tool',
        kindLabel: '工具',
        defaultModel: '',
        defaultPrompt: '发起外部 HTTP 请求并整理响应结果。',
        defaultMaxTokens: 0,
      },
      {
        key: 'python',
        title: 'Python 执行',
        kind: 'code',
        kindLabel: '执行',
        defaultModel: '',
        defaultPrompt: '执行 Python 代码并返回运行结果。',
        defaultMaxTokens: 0,
      },
      {
        key: 'db',
        title: '数据库查询',
        kind: 'data',
        kindLabel: '数据',
        defaultModel: '',
        defaultPrompt: '执行数据库查询并返回结构化数据。',
        defaultMaxTokens: 0,
      },
    ],
  },
  {
    title: '控制流',
    items: [
      {
        key: 'branch',
        title: '条件分支',
        kind: 'control',
        kindLabel: '控制',
        defaultModel: '',
        defaultPrompt: '根据条件选择后续执行分支。',
        defaultMaxTokens: 0,
      },
      {
        key: 'parallel',
        title: '并行执行',
        kind: 'control',
        kindLabel: '控制',
        defaultModel: '',
        defaultPrompt: '并行调度多个任务并汇总结果。',
        defaultMaxTokens: 0,
      },
      {
        key: 'retry',
        title: '重试策略',
        kind: 'control',
        kindLabel: '控制',
        defaultModel: '',
        defaultPrompt: '设置失败重试次数和退避策略。',
        defaultMaxTokens: 0,
      },
    ],
  },
]

const flowNodes = ref<FlowNode<WorkflowNodeData>[]>([
  {
    id: 'node-1',
    type: 'workflow',
    position: { x: 40, y: 50 },
    data: {
      title: '触发器',
      kind: 'start',
      kindLabel: '开始',
      model: '',
      prompt: '监听用户发起的需求输入。',
      maxTokens: 0,
    },
  },
  {
    id: 'node-2',
    type: 'workflow',
    position: { x: 280, y: 50 },
    data: {
      title: '需求分析 Agent',
      kind: 'agent',
      kindLabel: 'Agent',
      model: 'GPT-4o',
      prompt: '你是流程分析助手，输出结构化任务清单。',
      maxTokens: 2048,
    },
  },
  {
    id: 'node-3',
    type: 'workflow',
    position: { x: 280, y: 200 },
    data: {
      title: '知识检索',
      kind: 'search',
      kindLabel: '检索',
      model: 'DeepSeek-V3',
      prompt: '检索相关文档和知识库，为代码生成提供上下文。',
      maxTokens: 2048,
    },
  },
  {
    id: 'node-4',
    type: 'workflow',
    position: { x: 540, y: 200 },
    data: {
      title: '代码执行',
      kind: 'code',
      kindLabel: '执行',
      model: '',
      prompt: '执行生成的代码并反馈运行结果。',
      maxTokens: 0,
    },
  },
  {
    id: 'node-5',
    type: 'workflow',
    position: { x: 540, y: 50 },
    data: {
      title: '汇总输出',
      kind: 'end',
      kindLabel: '结束',
      model: '',
      prompt: '汇总最终执行结果并输出给用户。',
      maxTokens: 0,
    },
  },
])

const flowEdges = ref<Edge[]>([
  {
    id: 'edge-1',
    source: 'node-1',
    target: 'node-2',
    markerEnd: MarkerType.ArrowClosed,
  },
  {
    id: 'edge-2',
    source: 'node-2',
    target: 'node-3',
    markerEnd: MarkerType.ArrowClosed,
  },
  {
    id: 'edge-3',
    source: 'node-3',
    target: 'node-4',
    markerEnd: MarkerType.ArrowClosed,
  },
  {
    id: 'edge-4',
    source: 'node-2',
    target: 'node-5',
    markerEnd: MarkerType.ArrowClosed,
  },
])

const form = reactive({
  nodeName: '',
  model: '',
  prompt: '',
  maxTokens: 0,
})

const demand = ref('创建一个简单的用户登录功能')
const selectedNodeId = ref('node-2')
const showAuditModal = ref(false)
const currentRunId = ref('')
const currentExecutionId = ref('')
const executionStatus = ref<ExecutionStatus | ''>('')
const progress = ref(0)
const running = ref(false)
const pollTimer = ref<number | null>(null)
const auditData = ref<Record<string, any> | null>(null)

let nodeCounter = flowNodes.value.length + 1
let syncingForm = false

// @ts-ignore
const selectedNode = computed<FlowNode<WorkflowNodeData> | null>(() => {
  return flowNodes.value.find((node) => node.id === selectedNodeId.value) ?? null
})

const statusText = computed(() => {
  switch (executionStatus.value) {
    case ExecutionStatus.PENDING:
      return '等待启动'
    case ExecutionStatus.RUNNING:
      return '执行中'
    case ExecutionStatus.WAITING_APPROVAL:
      return '等待审批'
    case ExecutionStatus.APPROVED:
      return '审批通过'
    case ExecutionStatus.REJECTED:
      return '审批驳回'
    case ExecutionStatus.COMPLETED:
      return '执行完成'
    case ExecutionStatus.FAILED:
      return '执行失败'
    case ExecutionStatus.CANCELLED:
      return '已取消'
    default:
      return '未开始'
  }
})

watch(
  selectedNode,
  (node) => {
    syncingForm = true
    if (node) {
      form.nodeName = node.data!.title
      form.model = node.data!.model
      form.prompt = node.data!.prompt
      form.maxTokens = node.data!.maxTokens
    } else {
      form.nodeName = ''
      form.model = ''
      form.prompt = ''
      form.maxTokens = 0
    }
    syncingForm = false
  },
  { immediate: true }
)

watch(
  form,
  () => {
    if (syncingForm || !selectedNode.value) return
    selectedNode.value.data = {
      ...selectedNode.value.data!,
      title: form.nodeName,
      model: form.model,
      prompt: form.prompt,
      maxTokens: form.maxTokens,
    }
  },
  { deep: true }
)

function addNode(item: NodeCatalogItem) {
  const index = flowNodes.value.length
  const column = index % 3
  const row = Math.floor(index / 3)
  const id = `node-${nodeCounter++}`

  flowNodes.value = [
    ...flowNodes.value,
    {
      id,
      type: 'workflow',
      position: { x: 60 + column * 220, y: 80 + row * 130 },
      data: {
        title: item.title,
        kind: item.kind,
        kindLabel: item.kindLabel,
        model: item.defaultModel,
        prompt: item.defaultPrompt,
        maxTokens: item.defaultMaxTokens,
      },
    },
  ]

  selectedNodeId.value = id
}

function handleConnect(connection: Connection) {
  flowEdges.value = addEdge(
    {
      ...connection,
      id: `edge-${Date.now()}-${flowEdges.value.length}`,
      markerEnd: MarkerType.ArrowClosed,
    },
    flowEdges.value
  ) as Edge[]
}

function handleNodeClick(event: { node: FlowNode<WorkflowNodeData> }) {
  selectedNodeId.value = event.node.id
}

function clearSelection() {
  selectedNodeId.value = ''
}

function handleNodesDelete(deletedNodes: FlowNode<WorkflowNodeData>[]) {
  if (deletedNodes.some((node) => node.id === selectedNodeId.value)) {
    selectedNodeId.value = flowNodes.value[0]?.id ?? ''
  }
}

function removeSelectedNode() {
  if (!selectedNode.value) return
  const nodeId = selectedNode.value.id
  flowNodes.value = flowNodes.value.filter((node) => node.id !== nodeId)
  flowEdges.value = flowEdges.value.filter((edge) => edge.source !== nodeId && edge.target !== nodeId)
  selectedNodeId.value = flowNodes.value[0]?.id ?? ''
}

async function runPipeline() {
  if (running.value) return
  if (!demand.value) {
    alert('请先输入要执行的需求')
    return
  }

  try {
    running.value = true
    executionStatus.value = ExecutionStatus.PENDING
    progress.value = 0
    auditData.value = null

    const result = await apiClient.execution.createExecutionApiExecutionsPost({
      pipeline_id: 'default',
      demand: demand.value,
      config: {
        nodes: flowNodes.value.map((node) => ({
          id: node.id,
          title: node.data!.title,
          kind: node.data!.kind,
          position: node.position,
          model: node.data!.model,
          prompt: node.data!.prompt,
          max_tokens: node.data!.maxTokens,
        })),
        edges: flowEdges.value.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
        })),
      },
    })

    currentExecutionId.value = result.id
    currentRunId.value = result.id
    executionStatus.value = result.status

    await pollExecutionStatus()
    startPolling()
  } catch (error) {
    console.error('启动流水线失败：', error)
    executionStatus.value = ExecutionStatus.FAILED
    running.value = false
    alert('启动失败，请检查后端服务或接口参数')
  }
}

function startPolling() {
  stopPolling()
  pollTimer.value = window.setInterval(() => {
    void pollExecutionStatus()
  }, 2000)
}

function stopPolling() {
  if (pollTimer.value) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

async function pollExecutionStatus() {
  if (!currentExecutionId.value) return

  try {
    const status = await apiClient.execution.getExecutionApiExecutionsExecutionIdGet(currentExecutionId.value)
    executionStatus.value = status.status
    progress.value = status.progress ?? 0

    if (status.status === ExecutionStatus.WAITING_APPROVAL) {
      stopPolling()
      await fetchLatestCheckpoint()
      running.value = false
      return
    }

    if (
      status.status === ExecutionStatus.COMPLETED ||
      status.status === ExecutionStatus.FAILED ||
      status.status === ExecutionStatus.CANCELLED
    ) {
      stopPolling()
      running.value = false
      if (status.status === ExecutionStatus.COMPLETED) {
        alert('流水线执行完成')
      } else if (status.status === ExecutionStatus.FAILED) {
        alert(`流水线执行失败：${status.error || '未知错误'}`)
      }
    }
  } catch (error) {
    console.error('轮询执行状态失败：', error)
    stopPolling()
    running.value = false
  }
}

async function fetchLatestCheckpoint() {
  if (!currentExecutionId.value) return

  try {
    const checkpointList = await apiClient.checkpoint.listPendingCheckpointsApiCheckpointsGet(currentExecutionId.value)
    if (checkpointList.items.length > 0) {
      auditData.value = checkpointList.items[0]
      showAuditModal.value = true
    } else {
      alert('当前没有待审批的检查点')
    }
  } catch (error) {
    console.error('获取待审批检查点失败：', error)
    alert('获取审批信息失败，请稍后重试')
  }
}

async function openLatestCheckpoint() {
  if (!currentExecutionId.value) {
    alert('当前还没有运行中的执行实例')
    return
  }
  await fetchLatestCheckpoint()
}

function handleAuditSuccess(action: 'approve' | 'reject', result: any) {
  console.log(`审批${action === 'approve' ? '通过' : '驳回'}成功：`, result)
  executionStatus.value = action === 'approve' ? ExecutionStatus.APPROVED : ExecutionStatus.REJECTED
  running.value = true
  alert(`审批${action === 'approve' ? '通过' : '驳回'}成功！`)
  void pollExecutionStatus()
  startPolling()
}

function handleAuditError(action: 'approve' | 'reject', error: any) {
  console.error(`审批${action === 'approve' ? '通过' : '驳回'}失败：`, error)
  alert('审批失败，请检查接口状态。')
}
</script>

<style scoped>
.canvas-status {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.canvas-toolbar {
  padding: 8px;
}

.toolbar-tip {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 12px;
}

.workflow-flow {
  width: 100%;
  height: 100%;
  background: #fff;
}

.workflow-node {
  min-width: 172px;
  border: 1px solid #d6dff5;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(30, 41, 59, 0.1);
  padding: 12px 14px;
  text-align: left;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.workflow-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.12);
}

.workflow-node.selected {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
}

.workflow-node strong {
  display: block;
  color: #0f172a;
  font-size: 14px;
}

.workflow-node small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.workflow-handle {
  width: 10px;
  height: 10px;
  background: #2563eb;
  border: 2px solid #fff;
}

.node-badge {
  display: inline-flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: #eff6ff;
  color: #1d4ed8;
}

.workflow-node.start .node-badge {
  background: #ecfdf5;
  color: #047857;
}

.workflow-node.end .node-badge {
  background: #eff6ff;
  color: #1d4ed8;
}

.workflow-node.code .node-badge {
  background: #fff1f2;
  color: #be123c;
}

.workflow-node.search .node-badge {
  background: #f0fdf4;
  color: #15803d;
}

.workflow-node.agent .node-badge,
.workflow-node.llm .node-badge {
  background: #eef2ff;
  color: #4f46e5;
}

.workflow-node.control .node-badge {
  background: #f8fafc;
  color: #475569;
}

.node-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.node-item small {
  color: #64748b;
  font-size: 12px;
}

.config-content,
.config-empty {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-selected {
  margin: 0;
  color: #1d4ed8;
  font-weight: 600;
}

.config-panel label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #334155;
  font-size: 14px;
}

.config-panel input,
.config-panel select,
.config-panel textarea,
.demand-input {
  width: 100%;
  border: 1px solid #d6dff5;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.config-panel input:focus,
.config-panel select:focus,
.config-panel textarea:focus,
.demand-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.12);
}

.config-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
