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
    
    <!-- 下部分：结果显示 -->
    <div class="result-section">
      <div class="section-header">
        <h2>扫描结果</h2>
        <p v-if="currentTask">任务状态: {{ getStatusText(currentTask.status) }}</p>
      </div>
      
      <div class="result-content">
        <div v-if="!currentTask" class="empty-state">
          <p>暂无扫描结果，请先配置参数并开始扫描</p>
        </div>
        
        <div v-else class="task-info">
          <div class="task-details">
            <div class="detail-item">
              <span class="label">任务ID:</span>
              <span class="value">{{ currentTask.id }}</span>
            </div>
            <div class="detail-item">
              <span class="label">状态:</span>
              <span class="value" :class="getStatusClass(currentTask.status)">
                {{ getStatusText(currentTask.status) }}
              </span>
            </div>
            <div v-if="currentTask.result" class="detail-item">
              <span class="label">结果文件:</span>
              <span class="value">{{ currentTask.result }}</span>
            </div>
            <div v-if="currentTask.error" class="detail-item">
              <span class="label">错误信息:</span>
              <span class="value error">{{ currentTask.error }}</span>
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
    
    // 模拟任务信息（实际应该从后端获取）
    currentTask.value = {
      id: result.taskId || 'task_' + Date.now(),
      status: 'running',
      result: '',
      error: ''
    }
    
    // 模拟任务状态更新（实际应该通过WebSocket或轮询获取）
    setTimeout(() => {
      if (currentTask.value) {
        currentTask.value.status = 'success'
        currentTask.value.result = `/results/scan_${Date.now()}.${formData.fmt}`
      }
    }, 3000)
    
  } catch (error) {
    console.error('扫描失败:', error)
    currentTask.value = {
      id: 'task_' + Date.now(),
      status: 'failed',
      error: error instanceof Error ? error.message : '未知错误'
    }
  } finally {
    isLoading.value = false
  }
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
</style>