/**
 * 状态同步管理器
 * 
 * 优化状态同步机制，解决分叉后工具调用顺序等问题，
 * 实现状态变更的批量更新和事务性操作。
 */

import React from 'react';
import { Message, ToolCallState } from '@/types/chat';

// ============================================================================
// 状态同步类型定义
// ============================================================================

export interface StateTransaction {
  id: string;
  timestamp: number;
  operations: StateOperation[];
  status: 'pending' | 'committed' | 'rolled_back';
}

export interface StateOperation {
  type: 'message_update' | 'tool_call_update' | 'fork_update' | 'ui_update';
  target: string; // 目标ID
  payload: any;
  timestamp: number;
  dependencies?: string[]; // 依赖的其他操作
}

export interface SyncResult {
  success: boolean;
  transactionId: string;
  appliedOperations: number;
  errors: string[];
}

export interface TimestampSyncOptions {
  preserveOriginalTimestamps?: boolean;
  syncToLatest?: boolean;
  customTimestamp?: number;
}

// ============================================================================
// 状态同步管理器实现
// ============================================================================

export class StateSyncManager {
  private transactions: Map<string, StateTransaction> = new Map();
  private pendingOperations: StateOperation[] = [];
  private operationQueue: StateOperation[] = [];
  private isProcessing = false;

  /**
   * 开始新的事务
   */
  beginTransaction(): string {
    const transactionId = `tx_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const transaction: StateTransaction = {
      id: transactionId,
      timestamp: Date.now(),
      operations: [],
      status: 'pending'
    };

    this.transactions.set(transactionId, transaction);
    return transactionId;
  }

  /**
   * 添加操作到事务
   */
  addOperation(
    transactionId: string,
    operation: Omit<StateOperation, 'timestamp'>
  ): boolean {
    const transaction = this.transactions.get(transactionId);
    if (!transaction || transaction.status !== 'pending') {
      return false;
    }

    const fullOperation: StateOperation = {
      ...operation,
      timestamp: Date.now()
    };

    transaction.operations.push(fullOperation);
    return true;
  }

  /**
   * 提交事务
   */
  async commitTransaction(transactionId: string): Promise<SyncResult> {
    const transaction = this.transactions.get(transactionId);
    if (!transaction || transaction.status !== 'pending') {
      return {
        success: false,
        transactionId,
        appliedOperations: 0,
        errors: ['Transaction not found or not in pending status']
      };
    }

    try {
      // 验证操作依赖
      const validationResult = this.validateOperationDependencies(transaction.operations);
      if (!validationResult.isValid) {
        return {
          success: false,
          transactionId,
          appliedOperations: 0,
          errors: validationResult.errors
        };
      }

      // 排序操作（按依赖关系和时间戳）
      const sortedOperations = this.sortOperationsByDependencies(transaction.operations);

      // 应用操作
      const appliedCount = await this.applyOperations(sortedOperations);

      // 标记事务为已提交
      transaction.status = 'committed';

      return {
        success: true,
        transactionId,
        appliedOperations: appliedCount,
        errors: []
      };
    } catch (error) {
      // 回滚事务
      await this.rollbackTransaction(transactionId);
      
      return {
        success: false,
        transactionId,
        appliedOperations: 0,
        errors: [error instanceof Error ? error.message : String(error)]
      };
    }
  }

  /**
   * 回滚事务
   */
  async rollbackTransaction(transactionId: string): Promise<boolean> {
    const transaction = this.transactions.get(transactionId);
    if (!transaction) {
      return false;
    }

    try {
      // 这里应该实现回滚逻辑
      // 由于状态管理的复杂性，实际实现可能需要快照机制
      transaction.status = 'rolled_back';
      return true;
    } catch (error) {
      console.error('Failed to rollback transaction:', error);
      return false;
    }
  }

  /**
   * 批量更新状态
   */
  async batchUpdate(operations: Omit<StateOperation, 'timestamp'>[]): Promise<SyncResult> {
    const transactionId = this.beginTransaction();

    // 添加所有操作到事务
    for (const operation of operations) {
      this.addOperation(transactionId, operation);
    }

    // 提交事务
    return await this.commitTransaction(transactionId);
  }

  /**
   * 同步消息和工具调用的时间戳
   */
  syncTimestamps(
    messages: Message[],
    toolCalls: ToolCallState[],
    options: TimestampSyncOptions = {}
  ): { messages: Message[], toolCalls: ToolCallState[] } {
    const { preserveOriginalTimestamps = false, syncToLatest = true, customTimestamp } = options;

    // 创建时间戳映射
    const timestampMap = new Map<string, number>();
    
    if (customTimestamp) {
      // 使用自定义时间戳
      messages.forEach(msg => timestampMap.set(msg.id!, customTimestamp));
      toolCalls.forEach(tc => timestampMap.set(tc.id, customTimestamp));
    } else if (syncToLatest) {
      // 同步到最新时间戳
      const allTimestamps = [
        ...messages.map(m => m.timestamp || 0),
        ...toolCalls.map(tc => tc.timestamp || 0)
      ];
      const latestTimestamp = Math.max(...allTimestamps);
      
      messages.forEach(msg => {
        if (!preserveOriginalTimestamps || !msg.timestamp) {
          timestampMap.set(msg.id!, latestTimestamp);
        }
      });
      
      toolCalls.forEach(tc => {
        if (!preserveOriginalTimestamps || !tc.timestamp) {
          timestampMap.set(tc.id, latestTimestamp);
        }
      });
    }

    // 应用时间戳同步
    const syncedMessages = messages.map(msg => ({
      ...msg,
      timestamp: timestampMap.get(msg.id!) || msg.timestamp
    }));

    const syncedToolCalls = toolCalls.map(tc => ({
      ...tc,
      timestamp: timestampMap.get(tc.id) || tc.timestamp
    }));

    return { messages: syncedMessages, toolCalls: syncedToolCalls };
  }

  /**
   * 解决分叉后的工具调用关联问题
   */
  resolveForkToolCallAssociation(
    originalMessage: Message,
    forkedMessage: Message,
    toolCalls: ToolCallState[]
  ): ToolCallState[] {
    // 找到与原始消息关联的工具调用
    const associatedToolCalls = toolCalls.filter(tc => 
      tc.messageId === originalMessage.id || 
      (tc.timestamp && originalMessage.timestamp && tc.timestamp >= originalMessage.timestamp)
    );

    // 更新工具调用以关联到分叉消息
    return toolCalls.map(tc => {
      if (associatedToolCalls.includes(tc)) {
        return {
          ...tc,
          messageId: forkedMessage.id,
          timestamp: forkedMessage.timestamp,
          // 保留原始关联信息用于追踪
          metadata: {
            ...tc.metadata,
            originalMessageId: originalMessage.id,
            forkTimestamp: Date.now()
          }
        };
      }
      return tc;
    });
  }

  /**
   * 优化排序逻辑
   */
  optimizeMessageOrder(
    messages: Message[],
    toolCalls: ToolCallState[]
  ): { messages: Message[], toolCalls: ToolCallState[] } {
    // 按时间戳排序消息
    const sortedMessages = [...messages].sort((a, b) => {
      const timestampA = a.timestamp || 0;
      const timestampB = b.timestamp || 0;
      
      if (timestampA !== timestampB) {
        return timestampA - timestampB;
      }
      
      // 如果时间戳相同，按创建顺序排序
      return (a.id || '').localeCompare(b.id || '');
    });

    // 按时间戳和消息关联排序工具调用
    const sortedToolCalls = [...toolCalls].sort((a, b) => {
      const timestampA = a.timestamp || 0;
      const timestampB = b.timestamp || 0;
      
      if (timestampA !== timestampB) {
        return timestampA - timestampB;
      }
      
      // 如果时间戳相同，按ID排序
      return a.id.localeCompare(b.id);
    });

    return { messages: sortedMessages, toolCalls: sortedToolCalls };
  }

  /**
   * 验证操作依赖
   */
  private validateOperationDependencies(operations: StateOperation[]): { isValid: boolean, errors: string[] } {
    const errors: string[] = [];
    const operationIds = new Set(operations.map(op => op.target));

    for (const operation of operations) {
      if (operation.dependencies) {
        for (const dependency of operation.dependencies) {
          if (!operationIds.has(dependency)) {
            errors.push(`Operation ${operation.target} depends on missing operation ${dependency}`);
          }
        }
      }
    }

    return { isValid: errors.length === 0, errors };
  }

  /**
   * 按依赖关系排序操作
   */
  private sortOperationsByDependencies(operations: StateOperation[]): StateOperation[] {
    const sorted: StateOperation[] = [];
    const remaining = [...operations];
    const processed = new Set<string>();

    while (remaining.length > 0) {
      const canProcess = remaining.filter(op => 
        !op.dependencies || 
        op.dependencies.every(dep => processed.has(dep))
      );

      if (canProcess.length === 0) {
        // 检测循环依赖
        throw new Error('Circular dependency detected in operations');
      }

      // 按时间戳排序可处理的操作
      canProcess.sort((a, b) => a.timestamp - b.timestamp);

      for (const op of canProcess) {
        sorted.push(op);
        processed.add(op.target);
        const index = remaining.indexOf(op);
        remaining.splice(index, 1);
      }
    }

    return sorted;
  }

  /**
   * 应用操作
   */
  private async applyOperations(operations: StateOperation[]): Promise<number> {
    let appliedCount = 0;

    for (const operation of operations) {
      try {
        await this.applyOperation(operation);
        appliedCount++;
      } catch (error) {
        console.error(`Failed to apply operation ${operation.target}:`, error);
        throw error;
      }
    }

    return appliedCount;
  }

  /**
   * 应用单个操作
   */
  private async applyOperation(operation: StateOperation): Promise<void> {
    // 这里应该根据操作类型调用相应的状态更新函数
    // 实际实现需要与状态管理系统集成
    
    switch (operation.type) {
      case 'message_update':
        // 更新消息状态
        break;
      case 'tool_call_update':
        // 更新工具调用状态
        break;
      case 'fork_update':
        // 更新分叉状态
        break;
      case 'ui_update':
        // 更新UI状态
        break;
      default:
        throw new Error(`Unknown operation type: ${operation.type}`);
    }
  }

  /**
   * 获取事务历史
   */
  getTransactionHistory(): StateTransaction[] {
    return Array.from(this.transactions.values());
  }

  /**
   * 清理已完成的事务
   */
  cleanupTransactions(olderThan: number = 24 * 60 * 60 * 1000): number {
    const cutoff = Date.now() - olderThan;
    let cleaned = 0;

    for (const [id, transaction] of this.transactions) {
      if (transaction.timestamp < cutoff && transaction.status !== 'pending') {
        this.transactions.delete(id);
        cleaned++;
      }
    }

    return cleaned;
  }
}

// ============================================================================
// React Hook 集成
// ============================================================================

/**
 * 使用状态同步管理器的 React Hook
 */
export function useStateSyncManager() {
  const managerRef = React.useRef<StateSyncManager>();
  
  if (!managerRef.current) {
    managerRef.current = new StateSyncManager();
  }

  const batchUpdate = React.useCallback(async (operations: Omit<StateOperation, 'timestamp'>[]) => {
    return await managerRef.current!.batchUpdate(operations);
  }, []);

  const syncTimestamps = React.useCallback((
    messages: Message[],
    toolCalls: ToolCallState[],
    options?: TimestampSyncOptions
  ) => {
    return managerRef.current!.syncTimestamps(messages, toolCalls, options);
  }, []);

  const resolveForkAssociation = React.useCallback((
    originalMessage: Message,
    forkedMessage: Message,
    toolCalls: ToolCallState[]
  ) => {
    return managerRef.current!.resolveForkToolCallAssociation(originalMessage, forkedMessage, toolCalls);
  }, []);

  const optimizeOrder = React.useCallback((
    messages: Message[],
    toolCalls: ToolCallState[]
  ) => {
    return managerRef.current!.optimizeMessageOrder(messages, toolCalls);
  }, []);

  return {
    batchUpdate,
    syncTimestamps,
    resolveForkAssociation,
    optimizeOrder,
    manager: managerRef.current
  };
}
