/**
 * 批量状态更新工具
 * 
 * 提供高效的批量状态更新机制，
 * 减少重复渲染，优化性能。
 */

import { useCallback, useRef, useMemo } from 'react';

// ============================================================================
// 批量更新类型定义
// ============================================================================

export interface BatchUpdate {
  id: string;
  updates: StateUpdate[];
  timestamp: number;
  priority: 'low' | 'normal' | 'high';
}

export interface StateUpdate {
  path: string; // 状态路径，如 'messageListState.showScrollButton'
  value: any;
  type: 'set' | 'merge' | 'delete';
  condition?: (currentValue: any) => boolean; // 条件更新
}

export interface BatchUpdateOptions {
  debounceMs?: number;
  maxBatchSize?: number;
  priority?: 'low' | 'normal' | 'high';
  onBatchComplete?: (batchId: string, updatesApplied: number) => void;
  onError?: (error: Error, batch: BatchUpdate) => void;
}

export interface UpdateQueue {
  pending: BatchUpdate[];
  processing: BatchUpdate | null;
  completed: BatchUpdate[];
}

// ============================================================================
// 批量状态更新器实现
// ============================================================================

export class BatchStateUpdater {
  private queue: UpdateQueue = {
    pending: [],
    processing: null,
    completed: []
  };
  
  private debounceTimers: Map<string, ReturnType<typeof setTimeout>> = new Map();
  private options: Required<BatchUpdateOptions>;
  private isProcessing = false;

  constructor(options: BatchUpdateOptions = {}) {
    this.options = {
      debounceMs: 16, // 一帧的时间
      maxBatchSize: 50,
      priority: 'normal',
      onBatchComplete: () => {},
      onError: (error) => console.error('Batch update error:', error),
      ...options
    };
  }

  /**
   * 添加状态更新到批次
   */
  addUpdate(
    path: string,
    value: any,
    type: 'set' | 'merge' | 'delete' = 'set',
    options?: {
      priority?: 'low' | 'normal' | 'high';
      condition?: (currentValue: any) => boolean;
      debounceKey?: string;
    }
  ): string {
    const update: StateUpdate = {
      path,
      value,
      type,
      condition: options?.condition
    };

    const priority = options?.priority || this.options.priority;
    const debounceKey = options?.debounceKey || path;

    // 清除之前的防抖定时器
    const existingTimer = this.debounceTimers.get(debounceKey);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // 创建新的批次或添加到现有批次
    const batchId = this.createOrUpdateBatch(update, priority);

    // 设置防抖定时器
    const timer = setTimeout(() => {
      this.processBatch(batchId);
      this.debounceTimers.delete(debounceKey);
    }, this.options.debounceMs);

    this.debounceTimers.set(debounceKey, timer);

    return batchId;
  }

  /**
   * 立即执行批量更新
   */
  flush(batchId?: string): Promise<void> {
    if (batchId) {
      return this.processBatch(batchId);
    }

    // 处理所有待处理的批次
    const promises = this.queue.pending.map(batch => this.processBatch(batch.id));
    return Promise.all(promises).then(() => {});
  }

  /**
   * 创建或更新批次
   */
  private createOrUpdateBatch(update: StateUpdate, priority: 'low' | 'normal' | 'high'): string {
    // 查找现有的相同优先级批次
    let existingBatch = this.queue.pending.find(batch => 
      batch.priority === priority && 
      batch.updates.length < this.options.maxBatchSize
    );

    if (!existingBatch) {
      // 创建新批次
      const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      existingBatch = {
        id: batchId,
        updates: [],
        timestamp: Date.now(),
        priority
      };
      this.queue.pending.push(existingBatch);
    }

    // 检查是否已存在相同路径的更新
    const existingUpdateIndex = existingBatch.updates.findIndex(u => u.path === update.path);
    if (existingUpdateIndex >= 0) {
      // 替换现有更新
      existingBatch.updates[existingUpdateIndex] = update;
    } else {
      // 添加新更新
      existingBatch.updates.push(update);
    }

    return existingBatch.id;
  }

  /**
   * 处理批次
   */
  private async processBatch(batchId: string): Promise<void> {
    const batchIndex = this.queue.pending.findIndex(batch => batch.id === batchId);
    if (batchIndex === -1) {
      return; // 批次不存在或已处理
    }

    const batch = this.queue.pending[batchIndex];
    this.queue.pending.splice(batchIndex, 1);
    this.queue.processing = batch;

    try {
      // 按优先级排序更新
      const sortedUpdates = this.sortUpdatesByPriority(batch.updates);
      
      // 应用更新
      let appliedCount = 0;
      for (const update of sortedUpdates) {
        if (await this.applyUpdate(update)) {
          appliedCount++;
        }
      }

      // 移动到已完成队列
      this.queue.completed.push(batch);
      this.queue.processing = null;

      // 调用完成回调
      this.options.onBatchComplete(batch.id, appliedCount);

    } catch (error) {
      this.queue.processing = null;
      this.options.onError(
        error instanceof Error ? error : new Error(String(error)),
        batch
      );
    }
  }

  /**
   * 应用单个更新
   */
  private async applyUpdate(update: StateUpdate): Promise<boolean> {
    try {
      // 这里应该与实际的状态管理系统集成
      // 例如调用 Redux dispatch 或 React setState
      
      // 模拟状态更新
      console.log(`Applying update: ${update.path} = ${JSON.stringify(update.value)}`);
      
      return true;
    } catch (error) {
      console.error(`Failed to apply update for path ${update.path}:`, error);
      return false;
    }
  }

  /**
   * 按优先级排序更新
   */
  private sortUpdatesByPriority(updates: StateUpdate[]): StateUpdate[] {
    // 可以根据路径或其他条件定义优先级
    return [...updates].sort((a, b) => {
      // UI 相关的更新优先级较高
      const aIsUI = a.path.includes('UI') || a.path.includes('ui');
      const bIsUI = b.path.includes('UI') || b.path.includes('ui');
      
      if (aIsUI && !bIsUI) return -1;
      if (!aIsUI && bIsUI) return 1;
      
      return 0;
    });
  }

  /**
   * 获取队列状态
   */
  getQueueStatus(): {
    pending: number;
    processing: boolean;
    completed: number;
  } {
    return {
      pending: this.queue.pending.length,
      processing: this.queue.processing !== null,
      completed: this.queue.completed.length
    };
  }

  /**
   * 清理已完成的批次
   */
  cleanup(olderThan: number = 5 * 60 * 1000): number {
    const cutoff = Date.now() - olderThan;
    const initialLength = this.queue.completed.length;
    
    this.queue.completed = this.queue.completed.filter(
      batch => batch.timestamp > cutoff
    );
    
    return initialLength - this.queue.completed.length;
  }

  /**
   * 取消待处理的更新
   */
  cancel(batchId?: string): boolean {
    if (batchId) {
      const index = this.queue.pending.findIndex(batch => batch.id === batchId);
      if (index >= 0) {
        this.queue.pending.splice(index, 1);
        return true;
      }
      return false;
    }

    // 取消所有待处理的批次
    const canceledCount = this.queue.pending.length;
    this.queue.pending = [];
    
    // 清除所有防抖定时器
    for (const timer of this.debounceTimers.values()) {
      clearTimeout(timer);
    }
    this.debounceTimers.clear();
    
    return canceledCount > 0;
  }
}

// ============================================================================
// React Hook 集成
// ============================================================================

/**
 * 使用批量状态更新器的 React Hook
 */
export function useBatchStateUpdater(options?: BatchUpdateOptions) {
  const updaterRef = useRef<BatchStateUpdater>();
  
  if (!updaterRef.current) {
    updaterRef.current = new BatchStateUpdater(options);
  }

  const addUpdate = useCallback((
    path: string,
    value: any,
    type: 'set' | 'merge' | 'delete' = 'set',
    updateOptions?: {
      priority?: 'low' | 'normal' | 'high';
      condition?: (currentValue: any) => boolean;
      debounceKey?: string;
    }
  ) => {
    return updaterRef.current!.addUpdate(path, value, type, updateOptions);
  }, []);

  const flush = useCallback((batchId?: string) => {
    return updaterRef.current!.flush(batchId);
  }, []);

  const cancel = useCallback((batchId?: string) => {
    return updaterRef.current!.cancel(batchId);
  }, []);

  const getStatus = useCallback(() => {
    return updaterRef.current!.getQueueStatus();
  }, []);

  // 清理函数
  const cleanup = useCallback(() => {
    updaterRef.current!.cleanup();
  }, []);

  return {
    addUpdate,
    flush,
    cancel,
    getStatus,
    cleanup,
    updater: updaterRef.current
  };
}

// ============================================================================
// 高级批量更新工具
// ============================================================================

/**
 * 创建批量更新构建器
 */
export class BatchUpdateBuilder {
  private updates: StateUpdate[] = [];
  private options: BatchUpdateOptions;

  constructor(options: BatchUpdateOptions = {}) {
    this.options = options;
  }

  /**
   * 设置状态值
   */
  set(path: string, value: any, condition?: (currentValue: any) => boolean): this {
    this.updates.push({ path, value, type: 'set', condition });
    return this;
  }

  /**
   * 合并状态对象
   */
  merge(path: string, value: any, condition?: (currentValue: any) => boolean): this {
    this.updates.push({ path, value, type: 'merge', condition });
    return this;
  }

  /**
   * 删除状态属性
   */
  delete(path: string, condition?: (currentValue: any) => boolean): this {
    this.updates.push({ path, value: undefined, type: 'delete', condition });
    return this;
  }

  /**
   * 条件更新
   */
  when(condition: boolean): this {
    // 为最后一个更新添加条件
    if (this.updates.length > 0 && condition) {
      const lastUpdate = this.updates[this.updates.length - 1];
      const originalCondition = lastUpdate.condition;
      lastUpdate.condition = originalCondition ? 
        (value) => originalCondition(value) && condition :
        () => condition;
    } else if (!condition && this.updates.length > 0) {
      // 移除最后一个更新
      this.updates.pop();
    }
    return this;
  }

  /**
   * 构建并执行批量更新
   */
  async execute(updater: BatchStateUpdater): Promise<string> {
    if (this.updates.length === 0) {
      throw new Error('No updates to execute');
    }

    // 创建批次
    const batchId = `builder_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 添加所有更新
    for (const update of this.updates) {
      updater.addUpdate(update.path, update.value, update.type, {
        condition: update.condition,
        debounceKey: batchId // 使用相同的防抖键确保它们在同一批次中
      });
    }

    // 立即执行
    await updater.flush(batchId);
    
    return batchId;
  }

  /**
   * 重置构建器
   */
  reset(): this {
    this.updates = [];
    return this;
  }

  /**
   * 获取当前更新数量
   */
  getUpdateCount(): number {
    return this.updates.length;
  }
}

/**
 * 创建批量更新构建器的便捷函数
 */
export function createBatchUpdateBuilder(options?: BatchUpdateOptions): BatchUpdateBuilder {
  return new BatchUpdateBuilder(options);
}
