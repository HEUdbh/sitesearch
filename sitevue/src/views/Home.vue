<template>
  <div class="home-container">
    <!-- 上部分：参数选择 -->
    <div class="parameter-section">
      <div class="section-header">
        <h2>OneForAll 参数配置</h2>
        <p>配置子域名扫描参数</p>
      </div>
      
      <div class="parameter-form">
        <div class="form-row">
          <div class="form-group">
            <label for="target">目标域名</label>
            <input 
              id="target" 
              v-model="formData.target" 
              type="text" 
              placeholder="例如：iqiyi.com"
              class="form-input"
            >
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formData.brute">
              <span class="checkmark"></span>
              暴力破解扫描
            </label>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formData.dns">
              <span class="checkmark"></span>
              DNS解析扫描
            </label>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formData.req">
              <span class="checkmark"></span>
              HTTP请求扫描
            </label>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="port">端口扫描级别</label>
            <select id="port" v-model="formData.port" class="form-select">
              <option value="small">小型端口扫描</option>
              <option value="medium">中型端口扫描</option>
              <option value="large">大型端口扫描</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formData.alive">
              <span class="checkmark"></span>
              仅显示存活主机
            </label>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label for="fmt">输出格式</label>
            <select id="fmt" v-model="formData.fmt" class="form-select">
              <option value="csv">CSV格式</option>
              <option value="json">JSON格式</option>
              <option value="txt">文本格式</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="formData.takeover">
              <span class="checkmark"></span>
              子域名接管检测
            </label>
          </div>
        </div>
        
        <div class="form-actions">
          <button 
            @click="runScan" 
            :disabled="isLoading || !formData.target"
            class="btn-primary"
          >
            {{ isLoading ? '扫描中...' : '开始扫描' }}
          </button>
          <button @click="resetForm" class="btn-secondary">重置参数</button>
        </div>
      </div>
    </div>
    
    <!-- 下部分：扫描进度显示 -->
    <div class="progress-section">
      <div class="section-header">
        <h2>扫描进度</h2>
        <p>实时显示OneForAll扫描任务进度</p>
      </div>
      
      <div class="progress-content">
        <div v-if="progressTasks.length === 0" class="empty-state">
          <p>暂无扫描任务，请先配置参数并开始扫描</p>
        </div>
        
        <div v-else class="progress-list">
          <div 
            v-for="task in progressTasks" 
            :key="task.taskId" 
            class="progress-item"
            :class="getProgressStatusClass(task.status)"
          >
            <div class="progress-header">
              <span class="task-id">任务ID: {{ task.taskId }}</span>
              <span class="progress-status">{{ getProgressDisplayText(task) }}</span>
            </div>
            
            <div class="progress-bar-container">
              <div class="progress-bar" :style="getProgressBarStyle(task.progress_percentage)"></div>
            </div>
            
            <div class="progress-details">
              <div class="detail-row">
                <span class="detail-label">当前模块:</span>
                <span class="detail-value">{{ task.current_module }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">发现子域名:</span>
                <span class="detail-value">{{ task.subdomains_found }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">已用时间:</span>
                <span class="detail-value">{{ task.elapsed_time }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">预计剩余:</span>
                <span class="detail-value">{{ task.estimated_remaining_time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

interface TaskInfo {
  id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  result?: string
  error?: string
}

interface FormData {
  target: string
  brute: boolean
  dns: boolean
  req: boolean
  port: string
  alive: boolean
  fmt: string
  path: string | null
  takeover: boolean
}

interface ProgressInfo {
  taskId: string
  status: string
  progress_percentage: number
  current_module: string
  subdomains_found: number
  elapsed_time: string
  estimated_remaining_time: string
}

const formData = reactive<FormData>({
  target: '',
  brute: true,
  dns: true,
  req: true,
  port: 'medium',
  alive: false,
  fmt: 'csv',
  path: null,
  takeover: false
})

const isLoading = ref(false)
const currentTask = ref<TaskInfo | null>(null)
const progressTasks = ref<ProgressInfo[]>([])
const progressIntervals = ref<Map<string, number>>(new Map())

const runScan = async () => {
  if (!formData.target) {
    alert('请输入目标域名')
    return
  }
  
  isLoading.value = true
  
  try {
    const response = await fetch('http://127.0.0.1:5000/api/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    const taskId = result.task_id
    
    // 添加进度监测任务
    const progressInfo: ProgressInfo = {
      taskId: taskId,
      status: 'running',
      progress_percentage: 0,
      current_module: '初始化',
      subdomains_found: 0,
      elapsed_time: '0s',
      estimated_remaining_time: '未知'
    }
    
    progressTasks.value.push(progressInfo)
    
    // 开始监测进度
    startProgressMonitoring(taskId)
    
  } catch (error) {
    console.error('扫描失败:', error)
    alert('扫描任务提交失败，请检查后端服务是否正常运行')
  } finally {
    isLoading.value = false
  }
}

// 获取任务进度信息
const fetchTaskProgress = async (taskId: string) => {
  try {
    const response = await fetch(`http://127.0.0.1:5000/api/process?taskid=${taskId}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    
    if (data.success) {
      // 更新进度数据
      const index = progressTasks.value.findIndex(task => task.taskId === taskId)
      if (index !== -1) {
        progressTasks.value[index] = {
          ...progressTasks.value[index],
          ...data
        }
      }
      
      // 如果任务已完成或失败，停止监测
      if (data.status === 'completed' || data.status === 'failed') {
        stopProgressMonitoring(taskId)
      }
      
      return data
    } else {
      console.error('获取进度信息失败:', data.error)
      return null
    }
  } catch (error) {
    console.error('获取进度信息失败:', error)
    return null
  }
}

// 开始监测任务进度
const startProgressMonitoring = (taskId: string) => {
  if (!progressIntervals.value.has(taskId)) {
    // 立即获取一次进度信息
    fetchTaskProgress(taskId)
    
    // 设置定时器，每3秒获取一次进度信息
    const interval = setInterval(() => {
      fetchTaskProgress(taskId)
    }, 3000)
    
    progressIntervals.value.set(taskId, interval)
  }
}

// 停止监测任务进度
const stopProgressMonitoring = (taskId: string) => {
  const interval = progressIntervals.value.get(taskId)
  if (interval) {
    clearInterval(interval)
    progressIntervals.value.delete(taskId)
    
    // 3秒后从进度列表中移除已完成的任务
    setTimeout(() => {
      progressTasks.value = progressTasks.value.filter(task => task.taskId !== taskId)
    }, 3000)
  }
}

// 获取进度显示文本
const getProgressDisplayText = (task: ProgressInfo) => {
  if (task.status === 'completed') {
    return '✅ 已完成'
  } else if (task.status === 'failed') {
    return `❌ 失败: ${task.current_module}`
  } else if (task.status === 'running') {
    return `🔄 ${task.current_module} (${task.progress_percentage}%)`
  } else {
    return '⏳ 等待中'
  }
}

// 获取进度条样式
const getProgressBarStyle = (percentage: number) => {
  return { width: `${percentage}%` }
}

// 获取进度状态样式类
const getProgressStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    'running': 'progress-running',
    'completed': 'progress-completed',
    'failed': 'progress-failed',
    'pending': 'progress-pending'
  }
  return classMap[status] || ''
}

const resetForm = () => {
  Object.assign(formData, {
    target: 'iqiyi.com',
    brute: true,
    dns: true,
    req: true,
    port: 'medium',
    alive: false,
    fmt: 'csv',
    path: null,
    takeover: false
  })
  currentTask.value = null
  
  // 停止所有进度监测并清空进度任务列表
  progressIntervals.value.forEach((interval, taskId) => {
    clearInterval(interval)
  })
  progressIntervals.value.clear()
  progressTasks.value = []
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'running': '执行中',
    'success': '成功',
    'failed': '失败'
  }
  return statusMap[status] || status
}

const getStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    'pending': 'status-pending',
    'running': 'status-running',
    'success': 'status-success',
    'failed': 'status-failed'
  }
  return classMap[status] || ''
}
</script>

<style scoped>
.home-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.parameter-section, .result-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
}

.section-header h2 {
  margin: 0 0 5px 0;
  color: #2c3e50;
  font-size: 1.5rem;
}

.section-header p {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.parameter-form {
  max-width: 800px;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.form-group {
  flex: 1;
  min-width: 200px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #2c3e50;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #3498db;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-weight: normal;
  margin-top: 25px;
}

.checkbox-label input {
  margin-right: 8px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

.btn-primary, .btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.result-content {
  min-height: 200px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #7f8c8d;
  font-style: italic;
}

.task-details {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 4px;
  border-left: 4px solid #3498db;
}

.detail-item {
  display: flex;
  margin-bottom: 10px;
  align-items: center;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item .label {
  font-weight: 600;
  min-width: 80px;
  color: #2c3e50;
}

.detail-item .value {
  margin-left: 10px;
  color: #34495e;
}

.detail-item .value.error {
  color: #e74c3c;
}

.status-pending { color: #f39c12; }
.status-running { color: #3498db; }
.status-success { color: #27ae60; }
.status-failed { color: #e74c3c; }

/* 进度监测样式 */
.progress-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.progress-content {
  min-height: 200px;
}

.progress-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.progress-item {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 15px;
  background: #f8f9fa;
  transition: all 0.3s ease;
}

.progress-item.progress-running {
  border-left: 4px solid #3498db;
  background: #f0f8ff;
}

.progress-item.progress-completed {
  border-left: 4px solid #27ae60;
  background: #f0fff4;
}

.progress-item.progress-failed {
  border-left: 4px solid #e74c3c;
  background: #fff0f0;
}

.progress-item.progress-pending {
  border-left: 4px solid #f39c12;
  background: #fff8e1;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.task-id {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

.progress-status {
  font-size: 14px;
  font-weight: 600;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2980b9);
  border-radius: 4px;
  transition: width 0.5s ease;
  min-width: 8px;
}

.progress-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.detail-value {
  font-size: 12px;
  color: #333;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .progress-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .progress-details {
    grid-template-columns: 1fr;
  }
  
  .detail-row {
    justify-content: space-between;
  }
}
</style>