import { ExecutionStatus, StartTaskRequest, CheckpointStatus } from '../services/pipelineApi';

export interface AppConfig {
  serviceUrl: string;       // 服务端URL
  pipelineIdList: string[]; // Pipeline列表
  autoRefresh: boolean;     // 自动刷新开关
  refreshInterval: number;  // 刷新间隔（毫秒）
  lastUpdated: number;      // 最后更新时间
}

export interface TaskState {
  senderTabId: number;
  startTaskRequest?: StartTaskRequest;
  checkpoints: CheckpointStatus[];
  executionStatus: ExecutionStatus;
}

const DEFAULT_CONFIG: AppConfig = {
  serviceUrl: '',
  pipelineIdList: [],
  autoRefresh: true,        // 默认开启
  refreshInterval: 30000,   // 默认30秒刷新一次
  lastUpdated: 0
};

const DEFAULT_TASK_STATE: Omit<TaskState, 'senderTabId'> = {
  checkpoints: [],
  executionStatus: {
    pipelineId: 'null',
    executionId: 'null',
    status: 'idle',
    currentStageId: undefined,
    totalDuration: undefined,
    lastUpdated: Date.now()
  }
};



class AppStore {
  private config: AppConfig = { ...DEFAULT_CONFIG };
  private tasks: Record<number, TaskState> = {};
  private listeners: Set<() => void> = new Set();

  async init() {
    await this.loadFromStorage();
    this.setupStorageChangeListener();
  }

  private async loadFromStorage() {
    if (chrome?.storage?.local) {
      const result = await chrome.storage.local.get(['appConfig', 'tasks']);
      
      if (result.appConfig) {
        this.config = { ...DEFAULT_CONFIG, ...result.appConfig };
      }
      
      if (result.tasks) {
        this.tasks = {...DEFAULT_TASK_STATE, ...result.tasks};
      }
    }
    
    this.notifyListeners();
  }

  private setupStorageChangeListener() {
    if (chrome?.storage?.onChanged) {
      chrome.storage.onChanged.addListener((changes, area) => {
        if (area === 'local') {
          if (changes.appConfig) {
            const newValue = changes.appConfig.newValue;
            const configValue = typeof newValue === 'object' && newValue !== null ? newValue : {};    // 确保newValue是对象
            this.config = { ...DEFAULT_CONFIG, ...configValue };
          }
          if (changes.tasks) {
            const newValue = changes.tasks.newValue;
            const tasksValue = typeof newValue === 'object' && newValue !== null ? newValue : {};
            this.tasks = { ...DEFAULT_TASK_STATE, ...tasksValue }
          }
          this.notifyListeners();
        }
      });
    }
  }

  getConfig(): AppConfig {
    return { ...this.config };
  }

  async updateConfig(config: Partial<AppConfig>) {
    this.config = { ...this.config, ...config };
    if (chrome?.storage?.local) {
      await chrome.storage.local.set({ appConfig: this.config });
    }
    this.notifyListeners();
  }

  // 获取所有任务
  getAllTasks(): Record<number, TaskState> {
    return { ...this.tasks };
  }

  // 根据tabId获取对应任务
  getTaskByTabId(senderTabId: number): TaskState | undefined {
    return this.tasks[senderTabId] ? { ...this.tasks[senderTabId] } : undefined;
  }

  // 创建新任务
  async createTask(senderTabId: number, initialState: Partial<TaskState> = {}): Promise<TaskState> {
    const newTask: TaskState = {
      senderTabId,
      ...DEFAULT_TASK_STATE,
      ...initialState
    };
    
    this.tasks[senderTabId] = newTask;
    await this.persistTasks();
    this.notifyListeners();
    
    return newTask;
  }

  // 更新指定tabId的任务
  async updateTask(senderTabId: number, state: Partial<TaskState>): Promise<TaskState | undefined> {
    if (!this.tasks[senderTabId]) {
      return undefined;
    }
    
    this.tasks[senderTabId] = { ...this.tasks[senderTabId], ...state };
    await this.persistTasks();
    this.notifyListeners();
    
    return this.tasks[senderTabId];
  }

  // 给任务添加检查点
  async addCheckpointToTask(senderTabId: number, checkpoint: Partial<CheckpointStatus> & { checkpointId: string; executionId: string }): Promise<TaskState | undefined> {
    const task = this.tasks[senderTabId];
    if (!task) {
      return undefined;
    }
    
    const newCheckpoint: CheckpointStatus = {
      reviews: '',
      action: undefined,
      prompt: undefined,
      ...checkpoint
    };
    
    task.checkpoints.push(newCheckpoint);
    await this.persistTasks();
    this.notifyListeners();
    
    return task;
  }

  // 更新检查点
  async updateCheckpoint(senderTabId: number, checkpointId: string, updates: Partial<CheckpointStatus>): Promise<TaskState | undefined> {
    const task = this.tasks[senderTabId];
    if (!task) {
      return undefined;
    }
    
    const checkpointIndex = task.checkpoints.findIndex(cp => cp.checkpointId === checkpointId);
    if (checkpointIndex === -1) {
      return undefined;
    }
    
    task.checkpoints[checkpointIndex] = {
      ...task.checkpoints[checkpointIndex],
      ...updates
    };
    
    await this.persistTasks();
    this.notifyListeners();
    
    return task;
  }

  // 重置指定tabId的任务
  async resetTask(senderTabId: number) {
    if (this.tasks[senderTabId]) {
      delete this.tasks[senderTabId];
      await this.persistTasks();
      this.notifyListeners();
    }
  }

  // 重置所有任务
  async resetAllTasks() {
    this.tasks = {};
    await this.persistTasks();
    this.notifyListeners();
  }

  // 持久化任务到存储
  private async persistTasks() {
    if (chrome?.storage?.local) {
      await chrome.storage.local.set({ tasks: this.tasks });
    }
  }

  // -------------------------- 兼容原有API --------------------------
  // 获取当前任务状态
  getState(): TaskState {
    // 默认返回第一个任务，或空任务
    const taskIds = Object.keys(this.tasks);
    if (taskIds.length > 0) {
      return { ...this.tasks[Number(taskIds[0])] };
    }
    return {
      senderTabId: 0,
      ...DEFAULT_TASK_STATE
    };
  }

  // 更新当前任务状态
  async updateState(state: Partial<TaskState>) {
    const senderTabId = state.senderTabId || 0;
    if (senderTabId === 0) return;
    
    if (this.tasks[senderTabId]) {
      this.tasks[senderTabId] = { ...this.tasks[senderTabId], ...state };
    } else {
      this.tasks[senderTabId] = {
        senderTabId,
        ...DEFAULT_TASK_STATE,
        ...state
      };
    }
    await this.persistTasks();
    this.notifyListeners();
  }

  // 重置当前任务状态
  async resetState() {
    await this.resetAllTasks();
  }

  // 订阅任务状态变化
  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // 任务状态变化了，通知所有订阅者
  private notifyListeners() {
    this.listeners.forEach(listener => listener());
  }
}

export const appStore = new AppStore();
