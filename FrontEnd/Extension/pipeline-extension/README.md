# Pipeline Engine UI - Chrome Extension
React + Vite + CRXJS 实现的 Chrome 插件，用于实现 LarkAIDevFlow 前端圈选功能。
## 项目结构
```plaintext
pipeline-extension/
├─ manifest.json                # V3 核心配置文件
├─ src/
│  ├─ background/               # 后台 Service Worker 层（核心逻辑层）
│  │  ├─ index.ts               # Service Worker 入口
│  │  ├─ services/              # 后端API封装层
│  │  │  ├─ apiClient.ts        # 统一请求封装、认证、错误处理
│  │  │  └─ pipelineApi.ts      # Pipeline相关业务接口
│  │  ├─ store/                 # 全局状态与配置管理
│  │  │  ├─ configStore.ts      # API配置持久化（基于chrome.storage）
│  │  │  └─ taskStore.ts        # 运行中任务状态管理
│  │  └─ events/                # 事件监听与分发
│  │     ├─ messageHandlers.ts  # 处理来自content/popup的消息
│  │     └─ storageListeners.ts # 监听配置变更自动更新
│  ├─ content/                  # 页面注入层（和网页DOM交互）
│  │  ├─ hooks/                 # 钩子（useDrag等）
│  │  ├─ components/            # 现有UI组件
│  │  │  ├─ ContentBox.tsx      # 浮窗UI主组件
│  │  │  ├─ content-box-stages/ # 分阶段浮窗UI
│  │  │  ├─ FloatBox.tsx        # 悬浮窗按钮
│  │  │  └─ SelectionOverlay.tsx# 选区覆盖层
│  │  └─ index.ts               # Content Script 入口
│  ├─ popup/                    # 点击插件图标弹出的面板
│  │  ├─ index.html
│  │  └─ App.tsx                # 展示当前任务状态、快捷操作
```