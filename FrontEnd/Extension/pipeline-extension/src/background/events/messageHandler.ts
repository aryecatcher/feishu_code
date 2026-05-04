import { pipelineApi, StartTaskRequest, CheckpointStatus } from '../services/pipelineApi';
import { TaskState } from '../store/appStore';
import { appStore, AppConfig } from '../store/appStore';

export type MessageType = 
  | 'GET_PIPELINES'
  | 'GET_PIPELINE_CONFIG'
  | 'GET_APP_CONFIG'
  | 'UPDATE_APP_CONFIG'
  | 'START_TASK'
  | 'CHECKPOINT_PROMPT'
  | 'GET_TASK_STATE'
  | 'CHANGE_TASK_STATE';              // 消息类型

export interface BaseMessage {        // 基础消息接口
  type: MessageType;
  payload?: any;
}

export interface MessageResponse {    // 消息响应接口
  success: boolean;
  data?: any;
  error?: string;
}

class MessageHandler {
  init() {
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
  }         // 初始化 -注册全局消息监听、绑定消息处理函数

  private async handleMessage(
    message: BaseMessage,
    sender: chrome.runtime.MessageSender,
    sendResponse: (response: MessageResponse) => void
   ) {
    try {
      switch (message.type) {
        case 'GET_PIPELINES':
          return this.handleGetPipelines(sendResponse);
        
        case 'GET_PIPELINE_CONFIG':
          return this.handleGetPipelineConfig(message.payload, sendResponse);
        
        case 'GET_APP_CONFIG':
          return this.handleGetAppConfig(sendResponse);
        
        case 'UPDATE_APP_CONFIG':
          return this.handleUpdateAppConfig(message.payload, sendResponse);
        
        case 'START_TASK':
          return this.handleStartTask(message.payload, sender, sendResponse);

        case 'CHECKPOINT_PROMPT':
          return this.handleCheckpointPrompt(message.payload, sender, sendResponse);

        case 'GET_TASK_STATE':
          return this.handleGetTaskState(message.payload, sendResponse);
        
        case 'CHANGE_TASK_STATE':
          return this.handleChangeTaskState(message.payload, sendResponse);
        
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

  // GetPipelines - 获取所有Pipeline列表
  private async handleGetPipelines(sendResponse: (response: MessageResponse) => void) {
    const pipelines = await pipelineApi.getPipelines();
    sendResponse({
      success: true,
      data: pipelines
    });
  }

  // GetPipelineConfig - 获取指定Pipeline的配置
  private async handleGetPipelineConfig(pipelineId: string, sendResponse: (response: MessageResponse) => void) {
    const pipelineConfig = await pipelineApi.getPipelineConfig(pipelineId);
    sendResponse({
      success: true,
      data: pipelineConfig
    });
  }

  // GetAppConfig - 获取应用配置
  private async handleGetAppConfig(sendResponse: (response: MessageResponse) => void) {
    sendResponse({
      success: true,
      data: appStore.getConfig()
    });
  }

  // UpdateAppConfig - 更新应用配置
  private async handleUpdateAppConfig(config: AppConfig, sendResponse: (response: MessageResponse) => void) {
    appStore.updateConfig(config);
    sendResponse({
      success: true,
    });
  }

  // StartTask - 启动新任务，提交用户反馈
  private async handleStartTask(request: StartTaskRequest, sender: chrome.runtime.MessageSender, sendResponse: (response: MessageResponse) => void) {
    // 持久化任务数据到store，防止后台重启丢失
    await appStore.updateState({
      senderTabId: sender.tab?.id,
      startTaskRequest: { ...request }
    });
    
    const result = await pipelineApi.startTask(request);
    sendResponse({
      success: true,
      data: result
    });
  }

  // CheckpointPrompt - 提交检查点反馈
  private async handleCheckpointPrompt(request: CheckpointStatus, sender: chrome.runtime.MessageSender, sendResponse: (response: MessageResponse) => void) {
    // 持久化检查点数据到store
    await appStore.updateState({ checkpointStatus: { ...request } });
    
    const result = await pipelineApi.checkpointPrompt(request);
    sendResponse({
      success: true,
      data: result
    });
  }


  // GetTaskState - 获取当前任务状态
  private async handleGetTaskState(taskId: string, sendResponse: (response: MessageResponse) => void) {
    const state = await pipelineApi.getTaskState(taskId);
    sendResponse({
      success: true,
      data: state
    });
  }

  // ChangeTaskState - 改变任务状态
  private async handleChangeTaskState(state: TaskState, sendResponse: (response: MessageResponse) => void) {
    appStore.updateState(state);
    sendResponse({
      success: true,
    });
  }
}

export const messageHandler = new MessageHandler();