// 行为事件采集器: 前端队列 + 定时批量上报 + 页面隐藏时兜底
// 原则: 只做客观记录; 事件即使丢失也不影响作答本身(作答走 saveAnswer)
import type { BehaviorEvent } from '../types/listening'
import { postBehaviorEvents } from './listeningApi'

const FLUSH_INTERVAL_MS = 5000

class EventCollector {
  private attemptId: string | null = null
  private studentId = 'anonymous'
  private queue: BehaviorEvent[] = []
  private timer: number | null = null
  private onPageHide = () => this.flush(true)

  start(attemptId: string, studentId: string) {
    this.stop()
    this.attemptId = attemptId
    this.studentId = studentId
    this.queue = []
    this.timer = window.setInterval(() => this.flush(false), FLUSH_INTERVAL_MS)
    window.addEventListener('pagehide', this.onPageHide)
  }

  stop() {
    if (this.timer !== null) {
      window.clearInterval(this.timer)
      this.timer = null
    }
    window.removeEventListener('pagehide', this.onPageHide)
    this.attemptId = null
    this.queue = []
  }

  track(event: BehaviorEvent) {
    if (!this.attemptId) return
    this.queue.push({
      ...event,
      client_at: event.client_at || new Date().toISOString()
    })
  }

  /** 把队列中的事件上报; keepalive 用于页面即将卸载时 */
  flush(keepalive = false) {
    if (!this.attemptId || this.queue.length === 0) return
    const batch = this.queue
    this.queue = []
    postBehaviorEvents(this.attemptId, this.studentId, batch, keepalive).catch(
      (error) => {
        // 上报失败把事件放回队列前部, 下轮重试; keepalive 场景不重试
        if (!keepalive) {
          this.queue = batch.concat(this.queue)
        }
        console.warn('行为事件上报失败, 稍后重试:', error)
      }
    )
  }
}

export const eventCollector = new EventCollector()

/** 生成/读取匿名学生 ID(持久在 localStorage, 服务端数据仍存 SQLite) */
export function getStudentId(): string {
  const key = 'aq_listening_student_id'
  let id = localStorage.getItem(key)
  if (!id) {
    id = `stu_${crypto.randomUUID().replace(/-/g, '').slice(0, 12)}`
    localStorage.setItem(key, id)
  }
  return id
}
