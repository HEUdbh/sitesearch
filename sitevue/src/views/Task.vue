<template>
  <div class="task-page">
    <h1>任务信息查询</h1>
    
    <!-- 任务统计信息 -->
    <div class="stats-section">
      <div class="stat-card">
        <h3>总任务数</h3>
        <p class="stat-number">{{ taskCount }}</p>
      </div>
      <div class="stat-card">
        <h3>进行中</h3>
        <p class="stat-number running">{{ runningCount }}</p>
      </div>
      <div class="stat-card">
        <h3>已完成</h3>
        <p class="stat-number completed">{{ completedCount }}</p>
      </div>
      <div class="stat-card">
        <h3>失败</h3>
        <p class="stat-number failed">{{ failedCount }}</p>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="task-list-section">
      <div class="list-header">
        <h2>任务列表</h2>
        <button @click="refreshTasks" :disabled="loading" class="refresh-btn">
          {{ loading ? '加载中...' : '刷新' }}
        </button>
      </div>
      
      <div v-if="loading" class="loading">
        <p>正在加载任务信息...</p>
      </div>
      
      <div v-else-if="tasks.length === 0" class="empty-state">
        <p>暂无任务记录</p>
      </div>
      
      <div v-else class="task-table">
        <table>
          <thead>
            <tr>
              <th>任务ID</th>
              <th>目标域名</th>
              <th>状态</th>
              <th>扫描参数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in tasks" :key="task.id" :class="getStatusClass(task.status)">
              <td class="task-id">{{ task.id }}</td>
              <td class="target">{{ task.target || task.targets || 'N/A' }}</td>
              <td class="status">
                <span :class="getStatusBadgeClass(task.status)">
                  {{ getStatusText(task.status) }}
                </span>
              </td>
              <td class="params">
                <div class="param-tags">
                  <span v-if="task.brute" class="tag">暴力破解</span>
                  <span v-if="task.dns" class="tag">DNS解析</span>
                  <span v-if="task.req" class="tag">HTTP请求</span>
                  <span v-if="task.port" class="tag">端口{{ task.port }}</span>
                  <span v-if="task.alive" class="tag">仅存活</span>
                  <span v-if="task.takeover" class="tag">子域名接管</span>
                </div>
              </td>
              <td class="actions">
                <button 
                  @click="viewDetails(task)" 
                  class="action-btn view"
                  title="查看详情"
                >
                  详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Task {
  id: string
  target?: string
  targets?: string
  brute: number
  dns: number
  req: number
  port?: string
  alive: number
  fmt?: string
  path?: string
  takeover: number
  status: string
}

const tasks = ref<Task[]>([])
const loading = ref(false)
const taskCount = ref(0)
const runningCount = ref(0)
const completedCount = ref(0)
const failedCount = ref(0)

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await fetch('http://127.0.0.1:5000/api/task')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    tasks.value = data.tasks || []
    taskCount.value = data.count || 0
    
    // 统计任务状态
    runningCount.value = tasks.value.filter(t => t.status === 'running').length
    completedCount.value = tasks.value.filter(t => t.status === 'completed').length
    failedCount.value = tasks.value.filter(t => t.status === 'failed').length
  } catch (error) {
    console.error('获取任务列表失败:', error)
    alert('获取任务列表失败，请检查后端服务是否正常运行')
  } finally {
    loading.value = false
  }
}

// 刷新任务列表
const refreshTasks = () => {
  fetchTasks()
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'running': '进行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取状态样式类
const getStatusClass = (status: string) => {
  return `status-${status}`
}

// 获取状态徽章样式类
const getStatusBadgeClass = (status: string) => {
  return `badge badge-${status}`
}

// 查看任务详情
const viewDetails = (task: Task) => {
  // 这里可以添加查看详情的逻辑
  console.log('查看任务详情:', task)
  alert(`任务ID: ${task.id}\n状态: ${getStatusText(task.status)}\n目标: ${task.target || task.targets || 'N/A'}`)
}

// 组件挂载时获取任务列表
onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.task-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  color: #333;
  margin-bottom: 30px;
}

/* 统计信息样式 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  border-left: 4px solid #007bff;
}

.stat-card h3 {
  margin: 0 0 10px 0;
  color: #666;
  font-size: 14px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
  color: #007bff;
}

.stat-number.running { color: #ffc107; }
.stat-number.completed { color: #28a745; }
.stat-number.failed { color: #dc3545; }

/* 列表头部样式 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.list-header h2 {
  margin: 0;
  color: #333;
}

.refresh-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.refresh-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 加载和空状态样式 */
.loading, .empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 表格样式 */
.task-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
}

/* 状态徽章样式 */
.badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.badge-pending { background: #ffc107; color: #212529; }
.badge-running { background: #17a2b8; color: white; }
.badge-completed { background: #28a745; color: white; }
.badge-failed { background: #dc3545; color: white; }

/* 参数标签样式 */
.param-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag {
  background: #e9ecef;
  color: #495057;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

/* 操作按钮样式 */
.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  font-size: 12px;
  cursor: pointer;
}

.action-btn.view {
  background: #17a2b8;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-page {
    padding: 10px;
  }
  
  .stats-section {
    grid-template-columns: 1fr 1fr;
  }
  
  .task-table {
    overflow-x: auto;
  }
  
  table {
    min-width: 800px;
  }
}
</style>