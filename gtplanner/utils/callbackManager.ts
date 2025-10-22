/**
 * 回调管理器
 * 
 * 统一管理所有聊天相关的回调函数，
 * 提供性能优化、错误处理和调试功能。
 */

import { useCallback, useRef } from 'react';
import { 
  ChatCallbacks, 
  createAsyncCallback, 
  createSyncCallback,
  createDebouncedCallback,
  createThrottledCallback,
  combineCallbacks
} from '@/types/callbacks';

// ============================================================================
// 回调管理器类型
// ============================================================================

export interface CallbackManagerOptions {
  // 性能优化选项
  enableDebounce?: boolean;
  debounceDelay?: number;
  enableThrottle?: boolean;
  throttleDelay?: number;
  
  // 错误处理选项
  enableErrorHandling?: boolean;
  onError?: (error: Error, context: string) => void;
  
  // 调试选项
  enableLogging?: boolean;
  logPrefix?: string;
}

export interface CallbackMetrics {
  totalCalls: number;
  errorCount: number;
  lastCallTime: number;
  averageExecutionTime: number;
}

// ============================================================================
// 回调管理器实现
// ============================================================================

export class CallbackManager {
  private options: Required<CallbackManagerOptions>;
  private metrics: Map<string, CallbackMetrics> = new Map();
  private callbacks: Map<string, Function> = new Map();

  constructor(options: CallbackManagerOptions = {}) {
    this.options = {
      enableDebounce: false,
      debounceDelay: 300,
      enableThrottle: false,
      throttleDelay: 300,
      enableErrorHandling: true,
      onError: (error, context) => console.error(`Callback error in ${context}:`, error),
      enableLogging: false,
      logPrefix: '[CallbackManager]',
      ...options
    };
  }

  /**
   * 注册回调函数
   */
  register<TArgs extends any[], TResult>(
    name: string,
    callback: (...args: TArgs) => TResult,
    options?: {
      debounce?: boolean;
      throttle?: boolean;
      async?: boolean;
    }
  ): (...args: TArgs) => TResult | Promise<TResult> {
    const callbackOptions = {
      debounce: this.options.enableDebounce,
      throttle: this.options.enableThrottle,
      async: false,
      ...options
    };

    let processedCallback = callback;

    // 添加性能监控
    if (this.options.enableLogging) {
      processedCallback = this.addMetrics(name, processedCallback);
    }

    // 添加错误处理
    if (this.options.enableErrorHandling) {
      if (callbackOptions.async) {
        processedCallback = createAsyncCallback(
          processedCallback as any,
          (error) => this.options.onError(error, name)
        ) as any;
      } else {
        processedCallback = createSyncCallback(
          processedCallback,
          (error) => this.options.onError(error, name)
        ) as any;
      }
    }

    // 添加防抖
    if (callbackOptions.debounce && !callbackOptions.async) {
      processedCallback = createDebouncedCallback(
        processedCallback as any,
        this.options.debounceDelay
      ) as any;
    }

    // 添加节流
    if (callbackOptions.throttle && !callbackOptions.async) {
      processedCallback = createThrottledCallback(
        processedCallback as any,
        this.options.throttleDelay
      ) as any;
    }

    this.callbacks.set(name, processedCallback);
    return processedCallback;
  }

  /**
   * 获取回调函数
   */
  get<TArgs extends any[], TResult>(
    name: string
  ): ((...args: TArgs) => TResult) | undefined {
    return this.callbacks.get(name) as any;
  }

  /**
   * 移除回调函数
   */
  unregister(name: string): boolean {
    this.metrics.delete(name);
    return this.callbacks.delete(name);
  }

  /**
   * 获取回调指标
   */
  getMetrics(name?: string): CallbackMetrics | Map<string, CallbackMetrics> {
    if (name) {
      return this.metrics.get(name) || {
        totalCalls: 0,
        errorCount: 0,
        lastCallTime: 0,
        averageExecutionTime: 0
      };
    }
    return new Map(this.metrics);
  }

  /**
   * 清除所有回调和指标
   */
  clear(): void {
    this.callbacks.clear();
    this.metrics.clear();
  }

  /**
   * 添加性能监控
   */
  private addMetrics<TArgs extends any[], TResult>(
    name: string,
    callback: (...args: TArgs) => TResult
  ): (...args: TArgs) => TResult {
    return (...args: TArgs): TResult => {
      const startTime = performance.now();
      
      try {
        const result = callback(...args);
        this.updateMetrics(name, startTime, false);
        
        if (this.options.enableLogging) {
          console.log(`${this.options.logPrefix} ${name} executed successfully`);
        }
        
        return result;
      } catch (error) {
        this.updateMetrics(name, startTime, true);
        throw error;
      }
    };
  }

  /**
   * 更新回调指标
   */
  private updateMetrics(name: string, startTime: number, isError: boolean): void {
    const executionTime = performance.now() - startTime;
    const existing = this.metrics.get(name) || {
      totalCalls: 0,
      errorCount: 0,
      lastCallTime: 0,
      averageExecutionTime: 0
    };

    const newMetrics: CallbackMetrics = {
      totalCalls: existing.totalCalls + 1,
      errorCount: existing.errorCount + (isError ? 1 : 0),
      lastCallTime: Date.now(),
      averageExecutionTime: (existing.averageExecutionTime * existing.totalCalls + executionTime) / (existing.totalCalls + 1)
    };

    this.metrics.set(name, newMetrics);
  }
}

// ============================================================================
// React Hook 集成
// ============================================================================

/**
 * 使用回调管理器的 React Hook
 */
export function useCallbackManager(options?: CallbackManagerOptions) {
  const managerRef = useRef<CallbackManager>();
  
  if (!managerRef.current) {
    managerRef.current = new CallbackManager(options);
  }

  const registerCallback = useCallback(<TArgs extends any[], TResult>(
    name: string,
    callback: (...args: TArgs) => TResult,
    callbackOptions?: {
      debounce?: boolean;
      throttle?: boolean;
      async?: boolean;
    }
  ) => {
    return managerRef.current!.register(name, callback, callbackOptions);
  }, []);

  const getCallback = useCallback(<TArgs extends any[], TResult>(name: string) => {
    return managerRef.current!.get<TArgs, TResult>(name);
  }, []);

  const getMetrics = useCallback((name?: string) => {
    return managerRef.current!.getMetrics(name);
  }, []);

  return {
    register: registerCallback,
    get: getCallback,
    getMetrics,
    manager: managerRef.current
  };
}

// ============================================================================
// 预定义回调工厂
// ============================================================================

/**
 * 创建消息相关回调
 */
export function createMessageCallbacks(
  manager: CallbackManager,
  handlers: {
    onSendMessage?: (content: string, editMessageUuid?: string) => Promise<any>;
    onUpdateMessage?: (messageId: string, newContent: string) => Promise<any>;
    onDeleteMessage?: (messageId: string) => Promise<void>;
    onViewDocument?: (content: string) => void;
    onCopyMessage?: (messageId: string) => Promise<void>;
  }
): Partial<ChatCallbacks> {
  const callbacks: Partial<ChatCallbacks> = {};

  if (handlers.onSendMessage) {
    callbacks.onSendMessage = manager.register(
      'onSendMessage',
      handlers.onSendMessage,
      { async: true }
    ) as any;
  }

  if (handlers.onUpdateMessage) {
    callbacks.onUpdateMessage = manager.register(
      'onUpdateMessage',
      handlers.onUpdateMessage,
      { async: true }
    ) as any;
  }

  if (handlers.onDeleteMessage) {
    callbacks.onDeleteMessage = manager.register(
      'onDeleteMessage',
      handlers.onDeleteMessage,
      { async: true }
    ) as any;
  }

  if (handlers.onViewDocument) {
    callbacks.onViewDocument = manager.register(
      'onViewDocument',
      handlers.onViewDocument
    );
  }

  if (handlers.onCopyMessage) {
    callbacks.onCopyMessage = manager.register(
      'onCopyMessage',
      handlers.onCopyMessage,
      { async: true }
    ) as any;
  }

  return callbacks;
}

/**
 * 创建会话相关回调
 */
export function createSessionCallbacks(
  manager: CallbackManager,
  handlers: {
    onLoadSessions?: (page?: number, append?: boolean) => Promise<{ sessions: any[], hasMore: boolean }>;
    onRenameSession?: (sessionId: string, newTitle: string) => Promise<boolean>;
    onDeleteSession?: (sessionId: string) => Promise<boolean>;
    onSessionSelect?: (sessionId: string) => void;
    onNewSession?: () => void;
  }
): Partial<ChatCallbacks> {
  const callbacks: Partial<ChatCallbacks> = {};

  if (handlers.onLoadSessions) {
    callbacks.onLoadSessions = manager.register(
      'onLoadSessions',
      handlers.onLoadSessions,
      { async: true }
    ) as any;
  }

  if (handlers.onRenameSession) {
    callbacks.onRenameSession = manager.register(
      'onRenameSession',
      handlers.onRenameSession,
      { async: true, debounce: true }
    ) as any;
  }

  if (handlers.onDeleteSession) {
    callbacks.onDeleteSession = manager.register(
      'onDeleteSession',
      handlers.onDeleteSession,
      { async: true }
    ) as any;
  }

  if (handlers.onSessionSelect) {
    callbacks.onSessionSelect = manager.register(
      'onSessionSelect',
      handlers.onSessionSelect,
      { throttle: true }
    );
  }

  if (handlers.onNewSession) {
    callbacks.onNewSession = manager.register(
      'onNewSession',
      handlers.onNewSession
    );
  }

  return callbacks;
}
