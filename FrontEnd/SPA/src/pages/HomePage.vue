<template>
  <section class="hero container">
    <div class="hero-text">
      <p class="tag">AI 自动工作流平台</p>
      <h1>把复杂业务流程，编排成可执行的智能流水线</h1>
      <p class="desc">
        通过组件式能力拼装 LLM、检索、代码执行与审批节点，打造企业级自动化引擎。
      </p>
      <div class="hero-actions">
        <RouterLink class="btn btn-primary" to="/execute">新建执行</RouterLink>
        <RouterLink class="btn btn-outline" to="/workflow">编排引擎</RouterLink>
      </div>
      <ul class="hero-stats">
        <li><strong>99.9%</strong><span>任务稳定率</span></li>
        <li><strong>60%</strong><span>交付效率提升</span></li>
        <li><strong>120+</strong><span>可扩展节点</span></li>
      </ul>
    </div>
    <div class="hero-card">
      <h3>实时执行看板</h3>
      <div class="mini-flow">
        <span class="node start">触发器</span>
        <span class="arrow">→</span>
        <span class="node">LLM 分析</span>
        <span class="arrow">→</span>
        <span class="node">并行工具</span>
        <span class="arrow">→</span>
        <span class="node end">输出</span>
      </div>
      <p>支持多分支、重试策略、人工审批与执行日志追踪。</p>
    </div>
  </section>

  <!-- 快速开始区块 -->
  <section class="quick-start container">
    <h2>快速开始</h2>
    <div class="quick-cards">
      <RouterLink to="/execute" class="quick-card">
        <span class="quick-icon">🚀</span>
        <h3>新建执行</h3>
        <p>输入需求描述，AI 自动生成代码</p>
      </RouterLink>
      <RouterLink to="/workflow" class="quick-card">
        <span class="quick-icon">⚡</span>
        <h3>编排引擎</h3>
        <p>可视化配置流水线节点</p>
      </RouterLink>
      <RouterLink to="/executions" class="quick-card">
        <span class="quick-icon">📊</span>
        <h3>执行记录</h3>
        <p>查看历史执行和产物</p>
      </RouterLink>
    </div>
  </section>

  <section class="features container">
    <article class="feature-card" v-for="item in features" :key="item.title">
      <h3>{{ item.title }}</h3>
      <p>{{ item.desc }}</p>
    </article>
  </section>

  <section class="cta container">
    <h2>从官网介绍到流水线落地，一个项目完整打通</h2>
    <p>组件化 API + TypeScript 约束，让 AI 工作流前端更易维护和扩展。</p>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface FeatureItem {
  title: string
  desc: string
}

const features: FeatureItem[] = [
  {
    title: '可视化编排',
    desc: '拖拽节点，配置输入输出与依赖关系，快速生成任务 DAG。',
  },
  {
    title: '多智能体协同',
    desc: '支持主 Agent 调度子 Agent 并行执行，提升复杂任务处理效率。',
  },
  {
    title: '企业级管控',
    desc: '统一权限、审计日志、回放和告警，满足生产环境治理需求。',
  },
]
</script>
