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
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import AuditModal from '../components/AuditModal.vue'

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
</script>
