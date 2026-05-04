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
  let refreshInterval: number | null = null;

  // 监听应用配置变化，根据配置自动刷新任务状态
  appStore.subscribe(() => {
    const config = appStore.getConfig();
    const state = appStore.getState();

    // 清空上一个定时器，防止重复轮询
    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }

    const { executionId, status } = state.executionStatus;
    // 满足条件才启动新的轮询：自动刷新开启 + 有有效执行ID + 状态为运行中
    if (config.autoRefresh && executionId && executionId !== 'null' && status === 'running') {
      refreshInterval = window.setInterval(async () => {
        try {
          // 调用API获取最新执行状态
          const latestStatus = await pipelineApi.getTaskState(executionId);
          
          // 更新全局状态
          await appStore.updateState({ executionStatus: latestStatus });
          
          // 如果任务已经结束，停止轮询
          if (latestStatus.status !== 'running') {
            if (refreshInterval) {
              clearInterval(refreshInterval);
              refreshInterval = null;
            }
          }
        } catch (error) {
          console.error('Auto refresh failed:', error);
        }
      }, config.refreshInterval);
    }
  });
}

initBackground();
