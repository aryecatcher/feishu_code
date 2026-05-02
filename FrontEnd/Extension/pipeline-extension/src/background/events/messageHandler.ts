import { pipelineApi } from '../services/pipelineApi';
import { appStore } from '../store/appStore';

export type MessageType = 
  | 'GET_PIPELINE_STATUS'
  | 'SUBMIT_PROMPT'
  | 'GET_APP_CONFIG'
  | 'UPDATE_APP_CONFIG'
  | 'GET_TASK_STATE'
  | 'RESET_TASK_STATE';

export interface BaseMessage {
  type: MessageType;
  payload?: any;
}

export interface MessageResponse {
  success: boolean;
  data?: any;
  error?: string;
}

class MessageHandler {
  init() {
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
  }

  private async handleMessage(
    message: BaseMessage,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response: MessageResponse) => void
  ) {
    try {
      switch (message.type) {
        case 'GET_PIPELINE_STATUS':
          return this.handleGetPipelineStatus(message.payload, sendResponse);
        
        case 'SUBMIT_PROMPT':
          return this.handleSubmitPrompt(message.payload, sendResponse);
        
        case 'GET_APP_CONFIG':
          return this.handleGetAppConfig(sendResponse);
        
        case 'UPDATE_APP_CONFIG':
          return this.handleUpdateAppConfig(message.payload, sendResponse);
        
        case 'GET_TASK_STATE':
          return this.handleGetTaskState(sendResponse);
        
        case 'RESET_TASK_STATE':
          return this.handleResetTaskState(sendResponse);
        
        default:
          sendResponse({
            success: false,
            error: `Unknown message type: ${message.type}`
          });
      }
    } catch (error) {
      sendResponse({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    return true;
  }

  private async handleGetPipelineStatus(payload: { pipelineId: string }, sendResponse: (response: MessageResponse) => void) {
    const status = await pipelineApi.getPipelineStatus(payload.pipelineId);
    await appStore.updateState({ pipelineStatus: status });
    
    sendResponse({
      success: true,
      data: status
    });
  }

  private async handleSubmitPrompt(payload: { prompt: string; taskId: string }, sendResponse: (response: MessageResponse) => void) {
    await appStore.updateState({ 
      currentTaskId: payload.taskId,
      isRunning: true,
      lastError: undefined
    });

    try {
      const response = await pipelineApi.submitPrompt(payload);
      
      await appStore.updateState({
        isRunning: false
      });

      sendResponse({
        success: true,
        data: response
      });
    } catch (error) {
      await appStore.updateState({
        isRunning: false,
        lastError: error instanceof Error ? error.message : 'Failed to submit prompt'
      });

      throw error;
    }
  }

  private async handleGetAppConfig(sendResponse: (response: MessageResponse) => void) {
    const config = appStore.getConfig();
    sendResponse({
      success: true,
      data: config
    });
  }

  private async handleUpdateAppConfig(payload: Partial<{ apiKey: string; baseUrl: string; autoRefresh: boolean; refreshInterval: number }>, sendResponse: (response: MessageResponse) => void) {
    await appStore.updateConfig(payload);
    
    if (payload.apiKey || payload.baseUrl) {
      pipelineApi.setApiConfig(
        payload.apiKey || appStore.getConfig().apiKey,
        payload.baseUrl || appStore.getConfig().baseUrl
      );
    }

    sendResponse({
      success: true,
      data: appStore.getConfig()
    });
  }

  private async handleGetTaskState(sendResponse: (response: MessageResponse) => void) {
    const state = appStore.getState();
    sendResponse({
      success: true,
      data: state
    });
  }

  private async handleResetTaskState(sendResponse: (response: MessageResponse) => void) {
    await appStore.resetState();
    sendResponse({
      success: true,
      data: appStore.getState()
    });
  }
}

export const messageHandler = new MessageHandler();
