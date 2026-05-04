import { ExecutionStatus, StartTaskRequest, CheckpointStatus } from '../services/pipelineApi';

export interface AppConfig {
  serviceUrl: string;       // 服务端URL
  pipelineIdList: string[]; // Pipeline列表
  autoRefresh: boolean;     // 自动刷新开关
  refreshInterval: number;  // 刷新间隔（毫秒）
  lastUpdated: number;      // 最后更新时间
}

export interface TaskState {
  senderTabId?: number;
  startTaskRequest?: StartTaskRequest;
  checkpointStatus?: CheckpointStatus;
  executionStatus: ExecutionStatus;
}

const DEFAULT_CONFIG: AppConfig = {
  serviceUrl: '',
  pipelineIdList: [],
  autoRefresh: true,        // 默认开启
  refreshInterval: 30000,   // 默认30秒刷新一次
  lastUpdated: 0
};

const DEFAULT_STATE: TaskState = {
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
  private taskState: TaskState = { ...DEFAULT_STATE };
  private listeners: Set<() => void> = new Set();

  async init() {
    await this.loadFromStorage();
    this.setupStorageChangeListener();
  }

  private async loadFromStorage() {
    const result = await chrome.storage.local.get(['appConfig', 'taskState']);
    
    if (result.appConfig) {
      this.config = { ...DEFAULT_CONFIG, ...result.appConfig };
    }
    
    if (result.taskState) {
      this.taskState = { ...DEFAULT_STATE, ...result.taskState };
    }
    
    this.notifyListeners();
  }

  private setupStorageChangeListener() {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local') {
        if (changes.appConfig) {
          const newValue = changes.appConfig.newValue;
          // 类型校验：确保是对象才展开，否则使用空对象兜底
          const configValue = typeof newValue === 'object' && newValue !== null ? newValue : {};
          this.config = { ...DEFAULT_CONFIG, ...configValue };
        }
        if (changes.taskState) {
          const newValue = changes.taskState.newValue;
          // 类型校验：确保是对象才展开，否则使用空对象兜底
          const stateValue = typeof newValue === 'object' && newValue !== null ? newValue : {};
          this.taskState = { ...DEFAULT_STATE, ...stateValue };
        }
        this.notifyListeners();
      }
    });
  }

  getConfig(): AppConfig {
    return { ...this.config };
  }

  async updateConfig(config: Partial<AppConfig>) {
    this.config = { ...this.config, ...config };
    await chrome.storage.local.set({ appConfig: this.config });
    this.notifyListeners();
  }

  getState(): TaskState {
    return { ...this.taskState };
  }

  async updateState(state: Partial<TaskState>) {
    this.taskState = { ...this.taskState, ...state};
    await chrome.storage.local.set({ taskState: this.taskState });
    this.notifyListeners();
  }

  async resetState() {
    this.taskState = { ...DEFAULT_STATE };
    await chrome.storage.local.set({ taskState: this.taskState });
    this.notifyListeners();
  }

  subscribe(listener: () => void) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener());
  }
}

export const appStore = new AppStore();
