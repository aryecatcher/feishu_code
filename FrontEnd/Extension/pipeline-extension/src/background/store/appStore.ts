import { PipelineStatus } from '../services/pipelineApi';

export interface AppConfig {
  apiKey: string;
  baseUrl?: string;
  autoRefresh: boolean;
  refreshInterval: number;
}

export interface TaskState {
  currentTaskId?: string;
  pipelineStatus?: PipelineStatus;
  isRunning: boolean;
  lastError?: string;
  lastUpdated: number;
}

const DEFAULT_CONFIG: AppConfig = {
  apiKey: '',
  autoRefresh: true,
  refreshInterval: 30000
};

const DEFAULT_STATE: TaskState = {
  isRunning: false,
  lastUpdated: Date.now()
};

class AppStore {
  private config: AppConfig = { ...DEFAULT_CONFIG };
  private state: TaskState = { ...DEFAULT_STATE };
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
      this.state = { ...DEFAULT_STATE, ...result.taskState };
    }
    
    this.notifyListeners();
  }

  private setupStorageChangeListener() {
    chrome.storage.onChanged.addListener((changes, area) => {
      if (area === 'local') {
        if (changes.appConfig) {
          this.config = { ...DEFAULT_CONFIG, ...changes.appConfig.newValue };
        }
        if (changes.taskState) {
          this.state = { ...DEFAULT_STATE, ...changes.taskState.newValue };
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
    return { ...this.state };
  }

  async updateState(state: Partial<TaskState>) {
    this.state = { ...this.state, ...state, lastUpdated: Date.now() };
    await chrome.storage.local.set({ taskState: this.state });
    this.notifyListeners();
  }

  async resetState() {
    this.state = { ...DEFAULT_STATE, lastUpdated: Date.now() };
    await chrome.storage.local.set({ taskState: this.state });
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
