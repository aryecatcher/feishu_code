import { appStore } from './store/appStore';
import { pipelineApi } from './services/pipelineApi';
import { messageHandler } from './events/messageHandler';

async function initBackground() {
  console.log('Pipeline Extension Background initialized');

  try {
    await appStore.init();                  // 初始化应用存储状态
    
    const config = appStore.getConfig();    // 获取应用已存储配置
    if (config.lastUpdated === 0) {
      pipelineApi.setApiConfig(config.serviceUrl);
    }

    messageHandler.init();                  // 初始化消息处理模块

    setupAutoRefresh();                     // 设置自动刷新，根据配置自动刷新任务状态

    console.log('[Pipeline Extension Background] All modules initialized successfully');
  } catch (error) {
    console.error('Failed to initialize background:', error);
  }
}

function setupAutoRefresh() {
  const refreshIntervals: Record<number, number | null> = {};

  // 监听应用配置变化，根据配置自动刷新任务状态
  appStore.subscribe(() => {
    const config = appStore.getConfig();
    const allTasks = appStore.getAllTasks();

    // 遍历所有任务，处理每个任务的轮询
    Object.values(allTasks).forEach(task => {
      const tabId = task.senderTabId!;
      const { executionId, status } = task.executionStatus;

      // 先清理当前任务的旧定时器
      if (refreshIntervals[tabId]) {
        clearInterval(refreshIntervals[tabId]!);
        refreshIntervals[tabId] = null;
      }

      // 满足条件才启动新的轮询：自动刷新开启 + 有有效执行ID + 状态为运行中
      if (config.autoRefresh && executionId && executionId !== 'null' && status === 'running') {
        refreshIntervals[tabId] = window.setInterval(async () => {
          try {
            // 调用API获取最新执行状态
            const latestStatus = await pipelineApi.getTaskState(executionId);
            
            // 更新对应tabId的任务状态
            await appStore.updateTask(tabId, { executionStatus: latestStatus });
            
            // 如果任务已经结束，停止轮询
            if (latestStatus.status !== 'running') {
              if (refreshIntervals[tabId]) {
                clearInterval(refreshIntervals[tabId]!);
                refreshIntervals[tabId] = null;
              }
            }
          } catch (error) {
            console.error(`Auto refresh failed for tab ${tabId}:`, error);
          }
        }, config.refreshInterval);
      }
    });

    // 清理已经不存在的任务的定时器
    const existingTabIds = new Set(Object.keys(allTasks).map(Number));
    Object.keys(refreshIntervals).map(Number).forEach(tabId => {
      if (!existingTabIds.has(tabId) && refreshIntervals[tabId]) {
        clearInterval(refreshIntervals[tabId]!);
        delete refreshIntervals[tabId];
      }
    });
  });
}

initBackground();
