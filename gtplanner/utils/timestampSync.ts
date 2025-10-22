/**
 * 时间戳同步工具
 * 
 * 解决分叉后工具调用顺序问题，
 * 确保消息和工具调用的正确时间关联。
 */

import { Message, ToolCallState } from '@/types/chat';

// ============================================================================
// 时间戳同步类型定义
// ============================================================================

export interface TimestampSyncResult {
  messages: Message[];
  toolCalls: ToolCallState[];
  syncedCount: number;
  conflicts: TimestampConflict[];
}

export interface TimestampConflict {
  type: 'message_tool_mismatch' | 'fork_timestamp_drift' | 'ordering_inconsistency';
  messageId?: string;
  toolCallId?: string;
  description: string;
  suggestedFix: string;
}

export interface SyncStrategy {
  name: string;
  description: string;
  apply: (messages: Message[], toolCalls: ToolCallState[]) => TimestampSyncResult;
}

export interface ForkContext {
  originalMessageId: string;
  forkedMessageId: string;
  forkTimestamp: number;
  associatedToolCalls: string[];
}

// ============================================================================
// 时间戳同步器实现
// ============================================================================

export class TimestampSynchronizer {
  private strategies: Map<string, SyncStrategy> = new Map();
  private forkContexts: Map<string, ForkContext> = new Map();

  constructor() {
    this.registerDefaultStrategies();
  }

  /**
   * 注册同步策略
   */
  registerStrategy(strategy: SyncStrategy): void {
    this.strategies.set(strategy.name, strategy);
  }

  /**
   * 同步时间戳
   */
  sync(
    messages: Message[],
    toolCalls: ToolCallState[],
    strategyName: string = 'comprehensive'
  ): TimestampSyncResult {
    const strategy = this.strategies.get(strategyName);
    if (!strategy) {
      throw new Error(`Unknown sync strategy: ${strategyName}`);
    }

    return strategy.apply(messages, toolCalls);
  }

  /**
   * 记录分叉上下文
   */
  recordForkContext(context: ForkContext): void {
    this.forkContexts.set(context.forkedMessageId, context);
  }

  /**
   * 获取分叉上下文
   */
  getForkContext(messageId: string): ForkContext | undefined {
    return this.forkContexts.get(messageId);
  }

  /**
   * 检测时间戳冲突
   */
  detectConflicts(messages: Message[], toolCalls: ToolCallState[]): TimestampConflict[] {
    const conflicts: TimestampConflict[] = [];

    // 检测消息-工具调用时间戳不匹配
    for (const toolCall of toolCalls) {
      const associatedMessage = messages.find(m => m.id === toolCall.messageId);
      if (associatedMessage) {
        const messageTime = associatedMessage.timestamp || 0;
        const toolCallTime = toolCall.timestamp || 0;
        
        // 工具调用应该在消息之后或同时
        if (toolCallTime < messageTime) {
          conflicts.push({
            type: 'message_tool_mismatch',
            messageId: associatedMessage.id,
            toolCallId: toolCall.id,
            description: `Tool call timestamp (${toolCallTime}) is before message timestamp (${messageTime})`,
            suggestedFix: 'Sync tool call timestamp to message timestamp'
          });
        }
      }
    }

    // 检测分叉时间戳漂移
    for (const [forkedId, context] of this.forkContexts) {
      const forkedMessage = messages.find(m => m.id === forkedId);
      const originalMessage = messages.find(m => m.id === context.originalMessageId);
      
      if (forkedMessage && originalMessage) {
        const timeDrift = Math.abs((forkedMessage.timestamp || 0) - (originalMessage.timestamp || 0));
        
        // 如果时间漂移超过阈值（例如1秒）
        if (timeDrift > 1000) {
          conflicts.push({
            type: 'fork_timestamp_drift',
            messageId: forkedId,
            description: `Fork timestamp drift of ${timeDrift}ms detected`,
            suggestedFix: 'Sync fork timestamp to original message timestamp'
          });
        }
      }
    }

    // 检测排序不一致
    const sortedMessages = [...messages].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    const sortedToolCalls = [...toolCalls].sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    
    // 检查是否有工具调用在其关联消息之前
    for (let i = 0; i < sortedToolCalls.length; i++) {
      const toolCall = sortedToolCalls[i];
      const messageIndex = sortedMessages.findIndex(m => m.id === toolCall.messageId);
      const toolCallMessageTime = sortedMessages[messageIndex]?.timestamp || 0;
      
      if (toolCall.timestamp && toolCall.timestamp < toolCallMessageTime) {
        conflicts.push({
          type: 'ordering_inconsistency',
          toolCallId: toolCall.id,
          messageId: toolCall.messageId,
          description: 'Tool call appears before its associated message in timeline',
          suggestedFix: 'Reorder tool call to appear after its message'
        });
      }
    }

    return conflicts;
  }

  /**
   * 注册默认同步策略
   */
  private registerDefaultStrategies(): void {
    // 基础同步策略：只同步明显错误的时间戳
    this.registerStrategy({
      name: 'basic',
      description: 'Basic timestamp synchronization for obvious errors',
      apply: (messages, toolCalls) => this.basicSync(messages, toolCalls)
    });

    // 保守同步策略：最小化更改
    this.registerStrategy({
      name: 'conservative',
      description: 'Conservative sync with minimal changes',
      apply: (messages, toolCalls) => this.conservativeSync(messages, toolCalls)
    });

    // 全面同步策略：解决所有检测到的问题
    this.registerStrategy({
      name: 'comprehensive',
      description: 'Comprehensive sync resolving all detected issues',
      apply: (messages, toolCalls) => this.comprehensiveSync(messages, toolCalls)
    });

    // 分叉优化策略：专门处理分叉相关的时间戳问题
    this.registerStrategy({
      name: 'fork_optimized',
      description: 'Optimized for fork-related timestamp issues',
      apply: (messages, toolCalls) => this.forkOptimizedSync(messages, toolCalls)
    });
  }

  /**
   * 基础同步实现
   */
  private basicSync(messages: Message[], toolCalls: ToolCallState[]): TimestampSyncResult {
    const syncedMessages = [...messages];
    const syncedToolCalls = [...toolCalls];
    let syncedCount = 0;
    const conflicts = this.detectConflicts(messages, toolCalls);

    // 只修复明显的时间戳错误
    for (const conflict of conflicts) {
      if (conflict.type === 'message_tool_mismatch' && conflict.toolCallId) {
        const toolCallIndex = syncedToolCalls.findIndex(tc => tc.id === conflict.toolCallId);
        const message = syncedMessages.find(m => m.id === conflict.messageId);
        
        if (toolCallIndex >= 0 && message) {
          syncedToolCalls[toolCallIndex] = {
            ...syncedToolCalls[toolCallIndex],
            timestamp: message.timestamp
          };
          syncedCount++;
        }
      }
    }

    return {
      messages: syncedMessages,
      toolCalls: syncedToolCalls,
      syncedCount,
      conflicts: this.detectConflicts(syncedMessages, syncedToolCalls)
    };
  }

  /**
   * 保守同步实现
   */
  private conservativeSync(messages: Message[], toolCalls: ToolCallState[]): TimestampSyncResult {
    const result = this.basicSync(messages, toolCalls);
    
    // 额外处理分叉时间戳漂移，但只在漂移很大时
    for (const conflict of result.conflicts) {
      if (conflict.type === 'fork_timestamp_drift' && conflict.messageId) {
        const context = this.getForkContext(conflict.messageId);
        if (context) {
          const messageIndex = result.messages.findIndex(m => m.id === conflict.messageId);
          const originalMessage = result.messages.find(m => m.id === context.originalMessageId);
          
          if (messageIndex >= 0 && originalMessage) {
            const timeDrift = Math.abs((result.messages[messageIndex].timestamp || 0) - (originalMessage.timestamp || 0));
            
            // 只在漂移超过5秒时修复
            if (timeDrift > 5000) {
              result.messages[messageIndex] = {
                ...result.messages[messageIndex],
                timestamp: originalMessage.timestamp
              };
              result.syncedCount++;
            }
          }
        }
      }
    }

    return {
      ...result,
      conflicts: this.detectConflicts(result.messages, result.toolCalls)
    };
  }

  /**
   * 全面同步实现
   */
  private comprehensiveSync(messages: Message[], toolCalls: ToolCallState[]): TimestampSyncResult {
    let syncedMessages = [...messages];
    let syncedToolCalls = [...toolCalls];
    let syncedCount = 0;

    // 1. 首先处理分叉上下文
    for (const [forkedId, context] of this.forkContexts) {
      const forkedMessageIndex = syncedMessages.findIndex(m => m.id === forkedId);
      const originalMessage = syncedMessages.find(m => m.id === context.originalMessageId);
      
      if (forkedMessageIndex >= 0 && originalMessage) {
        // 同步分叉消息时间戳
        syncedMessages[forkedMessageIndex] = {
          ...syncedMessages[forkedMessageIndex],
          timestamp: originalMessage.timestamp
        };
        
        // 同步关联的工具调用
        for (const toolCallId of context.associatedToolCalls) {
          const toolCallIndex = syncedToolCalls.findIndex(tc => tc.id === toolCallId);
          if (toolCallIndex >= 0) {
            syncedToolCalls[toolCallIndex] = {
              ...syncedToolCalls[toolCallIndex],
              messageId: forkedId,
              timestamp: originalMessage.timestamp
            };
            syncedCount++;
          }
        }
        syncedCount++;
      }
    }

    // 2. 处理消息-工具调用时间戳不匹配
    for (const toolCall of syncedToolCalls) {
      const associatedMessage = syncedMessages.find(m => m.id === toolCall.messageId);
      if (associatedMessage) {
        const messageTime = associatedMessage.timestamp || 0;
        const toolCallTime = toolCall.timestamp || 0;
        
        if (toolCallTime !== messageTime) {
          const toolCallIndex = syncedToolCalls.findIndex(tc => tc.id === toolCall.id);
          if (toolCallIndex >= 0) {
            syncedToolCalls[toolCallIndex] = {
              ...syncedToolCalls[toolCallIndex],
              timestamp: messageTime
            };
            syncedCount++;
          }
        }
      }
    }

    // 3. 确保正确的排序
    syncedMessages.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));
    syncedToolCalls.sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0));

    return {
      messages: syncedMessages,
      toolCalls: syncedToolCalls,
      syncedCount,
      conflicts: this.detectConflicts(syncedMessages, syncedToolCalls)
    };
  }

  /**
   * 分叉优化同步实现
   */
  private forkOptimizedSync(messages: Message[], toolCalls: ToolCallState[]): TimestampSyncResult {
    const syncedMessages = [...messages];
    const syncedToolCalls = [...toolCalls];
    let syncedCount = 0;

    // 专门处理分叉相关的时间戳问题
    for (const [forkedId, context] of this.forkContexts) {
      const forkedMessage = syncedMessages.find(m => m.id === forkedId);
      const originalMessage = syncedMessages.find(m => m.id === context.originalMessageId);
      
      if (forkedMessage && originalMessage) {
        // 创建新的时间戳，略晚于原始消息
        const newTimestamp = (originalMessage.timestamp || 0) + 1;
        
        // 更新分叉消息
        const forkedIndex = syncedMessages.findIndex(m => m.id === forkedId);
        if (forkedIndex >= 0) {
          syncedMessages[forkedIndex] = {
            ...syncedMessages[forkedIndex],
            timestamp: newTimestamp
          };
          syncedCount++;
        }
        
        // 更新关联的工具调用，使其时间戳递增
        context.associatedToolCalls.forEach((toolCallId, index) => {
          const toolCallIndex = syncedToolCalls.findIndex(tc => tc.id === toolCallId);
          if (toolCallIndex >= 0) {
            syncedToolCalls[toolCallIndex] = {
              ...syncedToolCalls[toolCallIndex],
              messageId: forkedId,
              timestamp: newTimestamp + index + 1 // 确保工具调用按顺序排列
            };
            syncedCount++;
          }
        });
      }
    }

    return {
      messages: syncedMessages,
      toolCalls: syncedToolCalls,
      syncedCount,
      conflicts: this.detectConflicts(syncedMessages, syncedToolCalls)
    };
  }
}

// ============================================================================
// 便捷函数
// ============================================================================

/**
 * 创建默认的时间戳同步器
 */
export function createTimestampSynchronizer(): TimestampSynchronizer {
  return new TimestampSynchronizer();
}

/**
 * 快速同步时间戳
 */
export function quickSync(
  messages: Message[],
  toolCalls: ToolCallState[],
  strategy: string = 'comprehensive'
): TimestampSyncResult {
  const synchronizer = createTimestampSynchronizer();
  return synchronizer.sync(messages, toolCalls, strategy);
}

/**
 * 处理分叉后的时间戳同步
 */
export function syncAfterFork(
  originalMessage: Message,
  forkedMessage: Message,
  associatedToolCalls: ToolCallState[]
): { message: Message, toolCalls: ToolCallState[] } {
  const synchronizer = createTimestampSynchronizer();
  
  // 记录分叉上下文
  synchronizer.recordForkContext({
    originalMessageId: originalMessage.id!,
    forkedMessageId: forkedMessage.id!,
    forkTimestamp: Date.now(),
    associatedToolCalls: associatedToolCalls.map(tc => tc.id)
  });
  
  // 执行分叉优化同步
  const result = synchronizer.sync([originalMessage, forkedMessage], associatedToolCalls, 'fork_optimized');
  
  return {
    message: result.messages.find(m => m.id === forkedMessage.id)!,
    toolCalls: result.toolCalls
  };
}
