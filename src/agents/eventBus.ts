/**
 * EventBus — Agent 通信总线
 * 
 * 实现发布-订阅模式，支持事件优先级、异步处理和事件持久化
 */

import { randomUUID } from "node:crypto";
import type { AgentEvent, EventType } from "./types.js";

export interface EventBusSubscriber {
  /** 订阅者 ID */
  id: string;
  /** 订阅的事件类型（* 表示订阅所有事件） */
  eventType: EventType | "*";
  /** 回调函数 */
  callback: (event: AgentEvent) => Promise<void> | void;
  /** 订阅优先级（数字越大优先级越高） */
  priority: number;
  /** 是否一次性订阅（处理一次后自动取消） */
  once: boolean;
}

export interface EventBusStats {
  /** 总事件数 */
  totalEvents: number;
  /** 当前队列长度 */
  queueLength: number;
  /** 活跃订阅者数 */
  activeSubscribers: number;
  /** 事件处理成功率 */
  successRate: number;
  /** 平均处理时间（毫秒） */
  avgProcessingTimeMs: number;
}

export class EventBus {
  private subscribers: EventBusSubscriber[] = [];
  private eventQueue: AgentEvent[] = [];
  private processing = false;
  private stats: EventBusStats = {
    totalEvents: 0,
    queueLength: 0,
    activeSubscribers: 0,
    successRate: 100,
    avgProcessingTimeMs: 0
  };
  private totalProcessingTime = 0;
  private successfulProcesses = 0;
  private totalProcesses = 0;

  /** 订阅事件 */
  subscribe(subscriber: EventBusSubscriber): void {
    this.subscribers.push(subscriber);
    this.subscribers.sort((a, b) => b.priority - a.priority);
    this.stats.activeSubscribers = this.subscribers.length;
  }

  /** 取消订阅 */
  unsubscribe(subscriberId: string): void {
    this.subscribers = this.subscribers.filter(s => s.id !== subscriberId);
    this.stats.activeSubscribers = this.subscribers.length;
  }

  /** 发布事件 */
  async publish(event: Omit<AgentEvent, "eventId" | "timestamp">): Promise<string> {
    const fullEvent: AgentEvent = {
      eventId: randomUUID(),
      timestamp: new Date().toISOString(),
      ...event
    };

    this.eventQueue.push(fullEvent);
    this.eventQueue.sort((a, b) => b.priority - a.priority);
    this.stats.queueLength = this.eventQueue.length;
    this.stats.totalEvents++;

    // 如果当前没有在处理事件，启动处理循环
    if (!this.processing) {
      this.processQueue();
    }

    return fullEvent.eventId;
  }

  /** 处理事件队列 */
  private async processQueue(): Promise<void> {
    if (this.processing || this.eventQueue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.eventQueue.length > 0) {
      const event = this.eventQueue.shift()!;
      this.stats.queueLength = this.eventQueue.length;

      const startTime = Date.now();
      const matchingSubscribers = this.getMatchingSubscribers(event.type);

      for (const subscriber of matchingSubscribers) {
        try {
          await subscriber.callback(event);
          this.totalProcesses++;
          this.successfulProcesses++;
        } catch (error) {
          console.error(`[EventBus] Subscriber ${subscriber.id} failed to handle event ${event.eventId}:`, error);
        }

        // 一次性订阅自动取消
        if (subscriber.once) {
          this.unsubscribe(subscriber.id);
        }
      }

      const processingTime = Date.now() - startTime;
      this.totalProcessingTime += processingTime;
      this.stats.avgProcessingTimeMs = Math.round(
        this.totalProcessingTime / this.totalProcesses
      );
      this.stats.successRate = this.totalProcesses > 0
        ? Math.round((this.successfulProcesses / this.totalProcesses) * 100)
        : 100;
    }

    this.processing = false;
  }

  /** 获取匹配事件类型的订阅者 */
  private getMatchingSubscribers(eventType: EventType): EventBusSubscriber[] {
    return this.subscribers.filter(
      s => s.eventType === "*" || s.eventType === eventType
    );
  }

  /** 获取统计信息 */
  getStats(): EventBusStats {
    return { ...this.stats };
  }

  /** 清空队列 */
  clearQueue(): void {
    this.eventQueue = [];
    this.stats.queueLength = 0;
  }

  /** 获取当前队列中的事件（用于调试） */
  getPendingEvents(): AgentEvent[] {
    return [...this.eventQueue];
  }
}

/** 创建全局 EventBus 单例 */
let globalEventBus: EventBus | null = null;

export function getGlobalEventBus(): EventBus {
  if (!globalEventBus) {
    globalEventBus = new EventBus();
  }
  return globalEventBus;
}
