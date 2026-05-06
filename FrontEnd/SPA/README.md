# DevFlow 前端项目
AI驱动的可视化工作流编排平台前端，支持拖拽编排AI流水线、人工审批、多Agent协同执行等功能。
---
## 🛠️ 技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.x | 核心框架，Composition API + <script setup> 语法 |
| TypeScript | 5.x | 类型安全 |
| Vite | 8.x | 构建工具，开发热更新、构建速度快 |
| Vue Router | 4.x | 路由管理 |
| Vue Flow | 1.x | 专业流程图/画布引擎 |
| Axios | 1.x | 网络请求 |
| OpenAPI TypeScript Codegen | 0.30.x | 自动生成带类型的接口客户端 |
---
## 📁 目录结构
```
src/
├── api/                    # 接口层
│   ├── generated/          # 自动生成的OpenAPI接口代码（不要手动修改）
│   │   ├── core/           # 请求底层封装
│   │   ├── models/         # 接口入参/返回值TS类型定义
│   │   └── services/       # 所有接口方法
│   └── index.ts            # 导出自动生成的API客户端
├── assets/                 # 静态资源（图片、图标等）
├── components/             # 全局公共组件
│   ├── AppHeader.vue       # 全局顶部导航组件
│   ├── AuditModal.vue      # 通用审批弹窗组件
│   └── HelloWorld.vue      # 示例组件
├── pages/                  # 页面组件（路由级组件）
│   ├── HomePage.vue        # 首页（产品介绍页）
│   └── WorkflowPage.vue    # 核心工作流编排页
├── router/                 # 路由配置
│   └── index.ts            # 路由规则定义
├── utils/                  # 工具函数
│   └── request.ts          # 手动封装的Axios实例（备用）
├── App.vue                 # 根组件
├── main.ts                 # 项目入口文件
├── style.css               # 全局样式
└── vite-env.d.ts           # Vite环境类型声明
```
---
## 📄 页面说明
### 1. 首页 `/` → [HomePage.vue](src/pages/HomePage.vue)
**功能定位**：产品营销介绍页，面向首次访问的用户
**页面结构**：
- Hero区块：产品标语、核心卖点、进入工作流入口按钮
- 特性展示区：3个核心功能卡片（可视化编排、多智能体协同、企业级管控）
- CTA区块：号召用户使用的引导区
**交互逻辑**：点击「进入引擎」按钮跳转到工作流页面
---
### 2. 工作流页 `/workflow` → [WorkflowPage.vue](src/pages/WorkflowPage.vue)
**功能定位**：核心功能工作台，用户编排和运行流水线的主页面
**页面结构（三栏布局）**：
| 区域 | 位置 | 功能 |
|------|------|------|
| 节点库 | 左侧栏 | 展示可拖拽的节点分类：<br/>· AI节点：LLM对话、多Agent协作、RAG检索<br/>· 工具节点：HTTP请求、Python执行、数据库查询<br/>· 控制流：条件分支、并行执行、重试策略 |
| 画布区 | 中间 | 工作流编排主区域：<br/>· 顶部操作栏：打开审批、运行流水线按钮<br/>· 画布：拖拽编排节点、连线，可视化展示流水线结构<br/>· 示例节点：触发器、需求分析Agent、知识检索、代码执行、汇总输出 |
| 配置面板 | 右侧栏 | 选中节点的属性配置：<br/>· 节点名称<br/>· 模型选择（GPT-4o/DeepSeek-V3/Claude Sonnet）<br/>· 系统提示词<br/>· 最大Token限制 |
**核心功能**：
- 点击「运行流水线」按钮：调用后端接口启动流水线执行，自动轮询状态
- 流水线执行到审批节点时：自动弹出审批弹窗，支持通过/驳回操作
- 审批完成后自动继续执行，直到流水线结束
---
## 🧩 核心公共组件
### 1. [AppHeader.vue](src/components/AppHeader.vue)
全局顶部导航，所有页面共用：
- 左侧：品牌Logo和名称，点击跳转首页
- 中间：导航链接（首页、流水线引擎）
- 右侧：「立即体验」按钮，跳转到工作流页
### 2. [AuditModal.vue](src/components/AuditModal.vue)
通用人工审批弹窗组件：
- 功能：展示待审批方案、基础信息、原始返回数据
- 操作：支持通过/驳回，自动对接后端审批接口
- 调用方式：支持`v-model:visible`双向绑定显隐，传入`audit-data`和`run-id`即可使用
- 事件：`@success`/`@error`回调审批结果
---
## 🚀 快速开始
### 1. 安装依赖
```bash
npm install
```
### 2. 配置后端地址
在 `src/main.ts` 中修改API地址为你后端的实际地址：
```ts
BASE: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
```
或者在根目录新建 `.env.local` 文件配置：
```
VITE_API_BASE_URL=http://你的后端地址
```
### 3. 启动开发服务
```bash
npm run dev
```
默认访问地址：`http://localhost:5173`
### 4. 生产构建
```bash
npm run build
```
构建产物输出到 `dist` 目录
### 5. 重新生成接口代码
如果后端接口有更新，执行以下命令自动拉取最新的OpenAPI规范生成接口代码：
```bash
npm run gen-api
```
---
## 🔌 后端对接说明
### 接口调用方式
所有接口都通过全局`apiClient`调用，已经在`main.ts`初始化完成，直接导入使用即可：
```ts
import { apiClient } from './main'
// 示例：调用创建执行接口
const result = await apiClient.default.postApiV1PipelinesRun('default', {
  demand: '你的需求内容'
})
```
所有接口都有完整的TS类型提示，输入`apiClient.default.`编辑器会自动列出所有可用接口。
### 后端地址要求
- 后端基于FastAPI开发，默认端口8000
- 启动后端后可以访问 `http://localhost:8000/docs` 查看完整接口文档
---
## 💡 常用命令
| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务 |
| `npm run build` | 生产构建 |
| `npm run preview` | 预览构建产物 |
| `npm run typecheck` | 执行TypeScript类型检查 |
| `npm run gen-api` | 根据后端OpenAPI规范重新生成接口代码 |