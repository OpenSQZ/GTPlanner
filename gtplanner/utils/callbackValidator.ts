/**
 * 回调验证工具
 * 
 * 提供回调函数的验证、测试和调试功能，
 * 确保回调接口的正确性和一致性。
 */

import { ChatCallbacks } from '@/types/callbacks';

// ============================================================================
// 验证规则类型
// ============================================================================

export interface ValidationRule<T = any> {
  name: string;
  validate: (value: T) => boolean;
  message: string;
}

export interface CallbackValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface CallbackTestResult {
  success: boolean;
  executionTime: number;
  error?: Error;
  result?: any;
}

// ============================================================================
// 预定义验证规则
// ============================================================================

/**
 * 函数存在性验证
 */
export const functionExistsRule: ValidationRule<Function | undefined> = {
  name: 'functionExists',
  validate: (fn) => typeof fn === 'function',
  message: 'Callback must be a function'
};

/**
 * 异步函数验证
 */
export const asyncFunctionRule: ValidationRule<Function> = {
  name: 'asyncFunction',
  validate: (fn) => fn.constructor.name === 'AsyncFunction',
  message: 'Callback must be an async function'
};

/**
 * 参数数量验证
 */
export const createArityRule = (expectedArity: number): ValidationRule<Function> => ({
  name: `arity${expectedArity}`,
  validate: (fn) => fn.length === expectedArity,
  message: `Callback must accept exactly ${expectedArity} parameter(s)`
});

/**
 * 返回值类型验证
 */
export const createReturnTypeRule = (expectedType: string): ValidationRule<Function> => ({
  name: `returnType${expectedType}`,
  validate: () => true, // 运行时验证
  message: `Callback must return ${expectedType}`
});

// ============================================================================
// 回调验证器类
// ============================================================================

export class CallbackValidator {
  private rules: Map<string, ValidationRule[]> = new Map();
  private testResults: Map<string, CallbackTestResult[]> = new Map();

  /**
   * 添加验证规则
   */
  addRule(callbackName: string, rule: ValidationRule): void {
    const existing = this.rules.get(callbackName) || [];
    existing.push(rule);
    this.rules.set(callbackName, existing);
  }

  /**
   * 添加多个验证规则
   */
  addRules(callbackName: string, rules: ValidationRule[]): void {
    const existing = this.rules.get(callbackName) || [];
    existing.push(...rules);
    this.rules.set(callbackName, existing);
  }

  /**
   * 验证单个回调
   */
  validateCallback(
    callbackName: string, 
    callback: Function | undefined
  ): CallbackValidationResult {
    const rules = this.rules.get(callbackName) || [];
    const errors: string[] = [];
    const warnings: string[] = [];

    // 检查回调是否存在
    if (!callback) {
      if (rules.some(rule => rule.name === 'required')) {
        errors.push(`Required callback '${callbackName}' is missing`);
      } else {
        warnings.push(`Optional callback '${callbackName}' is not provided`);
      }
      return { isValid: errors.length === 0, errors, warnings };
    }

    // 应用验证规则
    for (const rule of rules) {
      try {
        if (!rule.validate(callback)) {
          errors.push(`${callbackName}: ${rule.message}`);
        }
      } catch (error) {
        errors.push(`${callbackName}: Validation error - ${error}`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * 验证所有回调
   */
  validateCallbacks(callbacks: Partial<ChatCallbacks>): CallbackValidationResult {
    const allErrors: string[] = [];
    const allWarnings: string[] = [];

    // 验证每个已注册的回调
    for (const [callbackName] of this.rules) {
      const callback = (callbacks as any)[callbackName];
      const result = this.validateCallback(callbackName, callback);
      
      allErrors.push(...result.errors);
      allWarnings.push(...result.warnings);
    }

    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      warnings: allWarnings
    };
  }

  /**
   * 测试回调执行
   */
  async testCallback(
    callback: Function,
    args: any[] = [],
    timeout: number = 5000
  ): Promise<CallbackTestResult> {
    const startTime = performance.now();

    try {
      // 设置超时
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Callback execution timeout')), timeout);
      });

      // 执行回调
      const executionPromise = Promise.resolve(callback(...args));
      const result = await Promise.race([executionPromise, timeoutPromise]);

      const executionTime = performance.now() - startTime;

      return {
        success: true,
        executionTime,
        result
      };
    } catch (error) {
      const executionTime = performance.now() - startTime;

      return {
        success: false,
        executionTime,
        error: error instanceof Error ? error : new Error(String(error))
      };
    }
  }

  /**
   * 批量测试回调
   */
  async testCallbacks(
    callbacks: Partial<ChatCallbacks>,
    testCases: Record<string, any[]> = {}
  ): Promise<Record<string, CallbackTestResult>> {
    const results: Record<string, CallbackTestResult> = {};

    for (const [name, callback] of Object.entries(callbacks)) {
      if (typeof callback === 'function') {
        const args = testCases[name] || [];
        results[name] = await this.testCallback(callback, args);
      }
    }

    return results;
  }

  /**
   * 获取测试历史
   */
  getTestHistory(callbackName?: string): CallbackTestResult[] | Record<string, CallbackTestResult[]> {
    if (callbackName) {
      return this.testResults.get(callbackName) || [];
    }
    
    const history: Record<string, CallbackTestResult[]> = {};
    for (const [name, results] of this.testResults) {
      history[name] = results;
    }
    return history;
  }

  /**
   * 清除测试历史
   */
  clearTestHistory(callbackName?: string): void {
    if (callbackName) {
      this.testResults.delete(callbackName);
    } else {
      this.testResults.clear();
    }
  }

  /**
   * 生成验证报告
   */
  generateReport(callbacks: Partial<ChatCallbacks>): string {
    const validation = this.validateCallbacks(callbacks);
    const callbackCount = Object.keys(callbacks).length;
    const ruleCount = Array.from(this.rules.values()).reduce((sum, rules) => sum + rules.length, 0);

    let report = `# Callback Validation Report\n\n`;
    report += `**Summary:**\n`;
    report += `- Total callbacks: ${callbackCount}\n`;
    report += `- Total validation rules: ${ruleCount}\n`;
    report += `- Validation status: ${validation.isValid ? '✅ PASSED' : '❌ FAILED'}\n\n`;

    if (validation.errors.length > 0) {
      report += `**Errors (${validation.errors.length}):**\n`;
      validation.errors.forEach(error => {
        report += `- ❌ ${error}\n`;
      });
      report += '\n';
    }

    if (validation.warnings.length > 0) {
      report += `**Warnings (${validation.warnings.length}):**\n`;
      validation.warnings.forEach(warning => {
        report += `- ⚠️ ${warning}\n`;
      });
      report += '\n';
    }

    // 添加回调详情
    report += `**Callback Details:**\n`;
    for (const [name, callback] of Object.entries(callbacks)) {
      const status = typeof callback === 'function' ? '✅' : '❌';
      const type = typeof callback === 'function' ? 
        (callback.constructor.name === 'AsyncFunction' ? 'async' : 'sync') : 
        typeof callback;
      report += `- ${status} \`${name}\` (${type})\n`;
    }

    return report;
  }
}

// ============================================================================
// 预配置验证器
// ============================================================================

/**
 * 创建标准的回调验证器
 */
export function createStandardValidator(): CallbackValidator {
  const validator = new CallbackValidator();

  // 消息相关回调验证规则
  validator.addRules('onSendMessage', [
    functionExistsRule,
    asyncFunctionRule,
    createArityRule(2)
  ]);

  validator.addRules('onUpdateMessage', [
    functionExistsRule,
    asyncFunctionRule,
    createArityRule(2)
  ]);

  validator.addRules('onDeleteMessage', [
    functionExistsRule,
    asyncFunctionRule,
    createArityRule(1)
  ]);

  validator.addRules('onViewDocument', [
    functionExistsRule,
    createArityRule(1)
  ]);

  // 会话相关回调验证规则
  validator.addRules('onLoadSessions', [
    functionExistsRule,
    asyncFunctionRule
  ]);

  validator.addRules('onRenameSession', [
    functionExistsRule,
    asyncFunctionRule,
    createArityRule(2)
  ]);

  validator.addRules('onDeleteSession', [
    functionExistsRule,
    asyncFunctionRule,
    createArityRule(1)
  ]);

  validator.addRules('onSessionSelect', [
    functionExistsRule,
    createArityRule(1)
  ]);

  validator.addRules('onNewSession', [
    functionExistsRule,
    createArityRule(0)
  ]);

  // 状态变更回调验证规则
  validator.addRules('onInlineEditingChange', [
    functionExistsRule,
    createArityRule(2)
  ]);

  validator.addRules('onSearchQueryChange', [
    functionExistsRule,
    createArityRule(1)
  ]);

  return validator;
}

// ============================================================================
// 调试工具
// ============================================================================

/**
 * 回调调试器
 */
export class CallbackDebugger {
  private logs: Array<{
    timestamp: number;
    callbackName: string;
    args: any[];
    result?: any;
    error?: Error;
    executionTime: number;
  }> = [];

  /**
   * 包装回调以添加调试信息
   */
  wrapCallback<T extends Function>(name: string, callback: T): T {
    return ((...args: any[]) => {
      const startTime = performance.now();
      const timestamp = Date.now();

      try {
        const result = callback(...args);
        const executionTime = performance.now() - startTime;

        this.logs.push({
          timestamp,
          callbackName: name,
          args,
          result,
          executionTime
        });

        console.log(`[CallbackDebugger] ${name}:`, {
          args,
          result,
          executionTime: `${executionTime.toFixed(2)}ms`
        });

        return result;
      } catch (error) {
        const executionTime = performance.now() - startTime;
        const err = error instanceof Error ? error : new Error(String(error));

        this.logs.push({
          timestamp,
          callbackName: name,
          args,
          error: err,
          executionTime
        });

        console.error(`[CallbackDebugger] ${name} error:`, {
          args,
          error: err,
          executionTime: `${executionTime.toFixed(2)}ms`
        });

        throw error;
      }
    }) as T;
  }

  /**
   * 获取调试日志
   */
  getLogs(callbackName?: string) {
    if (callbackName) {
      return this.logs.filter(log => log.callbackName === callbackName);
    }
    return [...this.logs];
  }

  /**
   * 清除调试日志
   */
  clearLogs(callbackName?: string): void {
    if (callbackName) {
      this.logs = this.logs.filter(log => log.callbackName !== callbackName);
    } else {
      this.logs = [];
    }
  }

  /**
   * 生成性能报告
   */
  generatePerformanceReport(): string {
    const stats = new Map<string, {
      count: number;
      totalTime: number;
      avgTime: number;
      minTime: number;
      maxTime: number;
      errorCount: number;
    }>();

    // 计算统计信息
    for (const log of this.logs) {
      const existing = stats.get(log.callbackName) || {
        count: 0,
        totalTime: 0,
        avgTime: 0,
        minTime: Infinity,
        maxTime: 0,
        errorCount: 0
      };

      existing.count++;
      existing.totalTime += log.executionTime;
      existing.minTime = Math.min(existing.minTime, log.executionTime);
      existing.maxTime = Math.max(existing.maxTime, log.executionTime);
      if (log.error) existing.errorCount++;

      existing.avgTime = existing.totalTime / existing.count;
      stats.set(log.callbackName, existing);
    }

    // 生成报告
    let report = `# Callback Performance Report\n\n`;
    report += `| Callback | Calls | Avg Time | Min Time | Max Time | Errors |\n`;
    report += `|----------|-------|----------|----------|----------|--------|\n`;

    for (const [name, stat] of stats) {
      report += `| ${name} | ${stat.count} | ${stat.avgTime.toFixed(2)}ms | ${stat.minTime.toFixed(2)}ms | ${stat.maxTime.toFixed(2)}ms | ${stat.errorCount} |\n`;
    }

    return report;
  }
}
