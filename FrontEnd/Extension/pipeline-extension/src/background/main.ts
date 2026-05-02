import { appStore } from './store/appStore';
import { pipelineApi } from './services/pipelineApi';
import { messageHandler } from './events/messageHandler';

async function initBackground() {
  console.log('Pipeline Extension Background initialized');

  try {
    await appStore.init();
    
    const config = appStore.getConfig();
    if (config.apiKey) {
      pipelineApi.setApiConfig(config.apiKey, config.baseUrl);
    }

    messageHandler.init();

    setupAutoRefresh();

    console.log('All modules initialized successfully');
  } catch (error) {
    console.error('Failed to initialize background:', error);
  }
}

function setupAutoRefresh() {
  let refreshInterval: number | null = null;

  appStore.subscribe(() => {
    const config = appStore.getConfig();
    const state = appStore.getState();

    if (refreshInterval) {
      clearInterval(refreshInterval);
      refreshInterval = null;
    }

    if (config.autoRefresh && state.currentTaskId && state.isRunning) {
      refreshInterval = window.setInterval(async () => {
        try {
          const status = await pipelineApi.getPipelineStatus(state.currentTaskId!);
          await appStore.updateState({ pipelineStatus: status });
          
          if (status.status !== 'running') {
            await appStore.updateState({ isRunning: false });
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
