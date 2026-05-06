<template>
  <section class="workflow-page container">
    <aside class="panel node-lib">
      <h2>节点库</h2>
      <div class="node-group" v-for="group in nodeGroups" :key="group.title">
        <p class="group-title">{{ group.title }}</p>
        <button class="node-item" v-for="node in group.items" :key="node">{{ node }}</button>
      </div>
    </aside>

    <div class="panel canvas-panel">
      <div class="canvas-head">
        <h2>流水线画布</h2>
        <div class="canvas-actions">
          <button class="btn btn-ghost" @click="showAuditModal = true">打开审批</button>
          <button class="btn btn-secondary" @click="showDeliveryPanel = true">查看交付物</button>
          <button class="btn btn-primary">发布流水线</button>
        </div>
      </div>
      <div class="canvas-body">
        <div class="flow-node start" style="top: 48px; left: 56px">触发器</div>
        <div class="flow-node" style="top: 48px; left: 280px">需求分析 Agent</div>
        <div class="flow-node" style="top: 170px; left: 280px">知识检索</div>
        <div class="flow-node" style="top: 170px; left: 520px">代码执行</div>
        <div class="flow-node end" style="top: 48px; left: 520px">汇总输出</div>
      </div>
    </div>

    <aside class="panel config-panel">
      <h2>节点配置</h2>
      <label>
        节点名称
        <input v-model="form.nodeName" type="text" />
      </label>
      <label>
        模型
        <select v-model="form.model">
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
        <input v-model.number="form.maxTokens" type="number" min="256" step="128" />
      </label>
    </aside>
  </section>

  <!-- 审批弹窗 -->
  <AuditModal
    v-model:visible="showAuditModal"
    :audit-data="auditData"
    :run-id="currentRunId"
    title="请确认需求分析方案"
    @success="handleAuditSuccess"
    @error="handleAuditError"
  />

  <!-- 交付物面板 -->
  <DeliveryPanel
    v-model:visible="showDeliveryPanel"
    :execution-id="currentRunId"
    :delivery-data="deliveryData"
    title="交付物详情"
    @close="handleDeliveryClose"
  />
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import AuditModal from '../components/AuditModal.vue'
import DeliveryPanel from '../components/DeliveryPanel.vue'

interface NodeGroup {
  title: string
  items: string[]
}

const nodeGroups: NodeGroup[] = [
  { title: 'AI 节点', items: ['LLM 对话', '多 Agent 协作', 'RAG 检索'] },
  { title: '工具节点', items: ['HTTP 请求', 'Python 执行', '数据库查询'] },
  { title: '控制流', items: ['条件分支', '并行执行', '重试策略'] },
]

const form = reactive({
  nodeName: '需求分析 Agent',
  model: 'GPT-4o',
  prompt: '你是流程分析助手，输出结构化任务清单。',
  maxTokens: 2048,
})

// 审批弹窗状态
const showAuditModal = ref(false)
const currentRunId = ref('run_20260426_001') // 测试用运行ID，实际从后端获取
const auditData = ref({
  // 测试用审批数据，实际从后端获取
  checkpoint_id: 10086,
  reviews: `### 需求分析方案
1. 梳理用户需求：实现AI工作流审批功能
2. 技术选型：Vue3 + TypeScript
3. 接口对接：对接后端审批接口，支持通过/驳回操作
4. 交互设计：弹窗展示方案，支持原始数据查看`,
  resolution: {
    action: 'accept',
    context_id: 202304
  }
})

// 交付物面板状态
const showDeliveryPanel = ref(false)
const deliveryData = ref({
  // 测试用交付物数据，实际从后端获取
  artifacts: [
    {
      path: 'app.py',
      content: `from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
`,
      language: 'python',
      description: 'FastAPI 应用主文件'
    },
    {
      path: 'requirements.txt',
      content: `fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3`,
      language: 'text',
      description: 'Python 依赖'
    },
    {
      path: 'Dockerfile',
      content: `FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]`,
      language: 'dockerfile',
      description: 'Docker 镜像配置'
    }
  ],
  deployment_steps: [
    {
      action: '安装依赖',
      command: 'pip install -r requirements.txt',
      description: '安装项目所需的 Python 包',
      verification: '运行 pip list 确认包已安装'
    },
    {
      action: '启动服务',
      command: 'uvicorn app:app --host 0.0.0.0 --port 8000',
      description: '启动 FastAPI 应用',
      verification: '访问 http://localhost:8000/docs 查看 API 文档'
    },
    {
      action: '健康检查',
      command: 'curl http://localhost:8000/health',
      description: '验证服务是否正常运行',
      verification: '返回 {"status":"healthy"}'
    }
  ],
  deployment_script: `#!/bin/bash
# 部署脚本

# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
uvicorn app:app --host 0.0.0.0 --port 8000`,
  estimated_time: '3 分钟',
  access_url: 'http://localhost:8000',
  checklist: [
    '安装项目依赖',
    '配置环境变量',
    '启动服务',
    '验证健康状态',
    '测试核心功能'
  ],
  summary: '生成了 3 个文件，包含 FastAPI 应用、Dockerfile 和部署脚本'
})

// 审批成功回调
function handleAuditSuccess(action: 'approve' | 'reject', result: any) {
  console.log(`审批${action === 'approve' ? '通过' : '驳回'}成功：`, result)
  alert(`审批${action === 'approve' ? '通过' : '驳回'}成功！`)
}

// 审批失败回调
function handleAuditError(action: 'approve' | 'reject', error: any) {
  console.error(`审批${action === 'approve' ? '通过' : '驳回'}失败：`, error)
  alert(`审批失败，请检查接口状态。`)
}

// 交付物面板关闭回调
function handleDeliveryClose() {
  console.log('交付物面板已关闭')
}
</script>
