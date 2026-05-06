import { pipelineApi, StartTaskRequest, CheckpointStatus } from '../services/pipelineApi';
import { TaskState } from '../store/appStore';
import { appStore, AppConfig } from '../store/appStore';

export type MessageType = 
  | 'GET_PIPELINES'
  | 'GET_DEFAULT_PIPELINE'
  | 'GET_PIPELINE_CONFIG'
  | 'GET_APP_CONFIG'
  | 'UPDATE_APP_CONFIG'
  | 'START_TASK'
  | 'GET_CHECKPOINT'
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
        
        case 'GET_DEFAULT_PIPELINE':
          return this.handleGetDefaultPipeline(sendResponse);
        
        case 'GET_PIPELINE_CONFIG':
          return this.handleGetPipelineConfig(message.payload, sendResponse);
        
        case 'GET_APP_CONFIG':
          return this.handleGetAppConfig(sendResponse);
        
        case 'UPDATE_APP_CONFIG':
          return this.handleUpdateAppConfig(message.payload, sendResponse);
        
        case 'START_TASK':
          return this.handleStartTask(message.payload, sender, sendResponse);
        
        case 'GET_CHECKPOINT':
          return this.handleGetCheckpoint(message.payload, sender, sendResponse);
        
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
  
  // GetDefaultPipeline - 获取默认Pipeline
  private async handleGetDefaultPipeline(sendResponse: (response: MessageResponse) => void) {
    const defaultPipeline = await pipelineApi.getDefaultPipeline();
    sendResponse({
      success: true,
      data: defaultPipeline
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
    const senderTabId = sender.tab?.id;
    if (!senderTabId) {
      sendResponse({
        success: false,
        error: 'Invalid sender: missing tab ID'
      });
      return;
    }

    // 创建新任务
    await appStore.createTask(senderTabId, {
      startTaskRequest: { ...request }
    });
    
    const result = await pipelineApi.startTask(request);

    // 更新任务执行状态
    await appStore.updateTask(senderTabId, 
      {
        executionStatus: {
          pipelineId: result.pipeline_id as string,
          executionId: result.id as string,
          status: result.status as 'pending' | 'running' | 'completed' | 'failed' | 'waiting_approval' | 'approved' | 'rejected' | 'cancelled',
          currentStageId: result.current_stage_id as string,
          totalDuration: result.total_duration as number,
          lastUpdated: Date.now()
        }
      }
    );

    sendResponse({
      success: true,
      data: result
    });
  }

  // GetCheckpoint - 获取待审批检查点信息
  private async handleGetCheckpoint(message: { executionId: string, stageId: string }, sender: chrome.runtime.MessageSender, sendResponse: (response: MessageResponse) => void) {
    const { executionId, stageId } = message;
    const result = await pipelineApi.getCheckpoint(executionId, stageId);

    // 创建检查点状态
    await appStore.addCheckpointToTask(sender.tab?.id as number, 
      {
        executionId: result.execution_id as string,
        checkpointId: result.id as string,
        reviews: 'Need to be updated'
      } as CheckpointStatus
    )

    sendResponse({
      success: true,
      data: result
    });
  }
  
  // CheckpointPrompt - 提交检查点反馈
  private async handleCheckpointPrompt(request: CheckpointStatus, sender: chrome.runtime.MessageSender, sendResponse: (response: MessageResponse) => void) {
    const senderTabId = sender.tab?.id;
    if (!senderTabId) {
      sendResponse({
        success: false,
        error: 'Invalid sender: missing tab ID'
      });
      return;
    }

    const task = appStore.getTaskByTabId(senderTabId);
    if (!task) {
      sendResponse({
        success: false,
        error: 'No task found for this tab'
      });
      return;
    }
    
    // 提交检查点到API
    const result = await pipelineApi.checkpointPrompt(request);
    
    // 更新检查点状态
    await appStore.updateCheckpoint(senderTabId, 
      request.checkpointId,
      {
        action: request.action as 'approve' | 'reject',
        prompt: request.prompt
      } as CheckpointStatus
    );

    sendResponse({
      success: true,
      data: result
    });
  }


  // GetTaskState - 获取当前任务状态
  private async handleGetTaskState(payload: { taskId?: string; senderTabId?: number }, sendResponse: (response: MessageResponse) => void) {
    const senderTabId = payload?.senderTabId;
    if (!senderTabId) {
      sendResponse({
        success: false,
        error: 'Missing senderTabId parameter'
      });
      return;
    }

    const task = appStore.getTaskByTabId(senderTabId);
    if (!task) {
      sendResponse({
        success: false,
        error: 'No task found for this tab'
      });
      return;
    }

    // 如果提供了taskId，从API获取最新状态
    if (payload.taskId) {
      const state = await pipelineApi.getTaskState(payload.taskId);
      await appStore.updateTask(senderTabId, 
        {
          executionStatus: {
            status: state.status as 'pending' | 'running' | 'completed' | 'failed' | 'waiting_approval' | 'approved' | 'rejected' | 'cancelled',
            currentStageId: state.current_stage_id as string,
            lastUpdated: Date.now()
          }
        } as TaskState
      );
      sendResponse({
        success: true,
        data: state
      });
    } else {
      // 否则返回本地存储的状态
      sendResponse({
        success: true,
        data: task.executionStatus
      });
    }
  }

  // ChangeTaskState - 改变任务状态
  private async handleChangeTaskState(payload: { state: Partial<TaskState>; senderTabId: number }, sendResponse: (response: MessageResponse) => void) {
    const senderTabId = payload?.senderTabId;
    if (!senderTabId) {
      sendResponse({
        success: false,
        error: 'Missing senderTabId parameter'
      });
      return;
    }

    const updatedTask = await appStore.updateTask(senderTabId, payload.state);
    if (!updatedTask) {
      sendResponse({
        success: false,
        error: 'No task found for this tab'
      });
      return;
    }

    sendResponse({
      success: true,
      data: updatedTask
    });
  }
}

export const messageHandler = new MessageHandler();