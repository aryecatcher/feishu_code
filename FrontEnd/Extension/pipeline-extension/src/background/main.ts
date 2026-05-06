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

    console.log('[Pipeline Extension Background] All modules initialized successfully');
  } catch (error) {
    console.error('Failed to initialize background:', error);
  }
}

initBackground();
