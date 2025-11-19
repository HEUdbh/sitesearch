<template>
  <div class="task-page">
    <h1>任务信息查询</h1>
    
    <!-- 报告详情弹窗 -->
    <div v-if="showReportModal" class="modal-overlay" @click="closeReportModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>任务报告详情</h3>
          <button class="close-btn" @click="closeReportModal">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 报告摘要信息 -->
          <div v-if="currentTask" class="report-summary">
            <p><strong>任务ID:</strong> {{ currentTask.id }}</p>
            <p><strong>目标域名:</strong> {{ currentTask.target || currentTask.targets || 'N/A' }}</p>
            <p v-if="reportData"><strong>扫描结果总数:</strong> {{ reportData.count || 0 }}</p>
            <p v-if="reportData"><strong>文件格式:</strong> {{ reportData.format || '未知' }}</p>
          </div>
          
          <!-- 数据表格 -->
          <div v-if="reportData && reportData.data && reportData.data.length > 0" class="data-table-section">
            <div class="table-header">
              <h4>扫描结果详情 ({{ reportData.count || 0 }} 条记录)</h4>
              <div class="table-controls">
                <button @click="toggleAllFields" class="control-btn">
                  {{ showAllFields ? '隐藏空字段' : '显示所有字段' }}
                </button>
                <button @click="exportToCSV" class="control-btn export">导出CSV</button>
              </div>
            </div>
            
            <div class="table-container">
              <table class="data-table">
                <thead>
                  <tr>
                    <th v-for="field in visibleFields" :key="field" :class="getFieldClass(field)">
                      {{ getFieldDisplayName(field) }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, index) in reportData.data" :key="index">
                    <td v-for="field in visibleFields" :key="field" :class="getFieldClass(field)">
                      <span v-if="field === 'alive'" :class="getAliveClass(item[field])">
                        {{ formatAliveStatus(item[field]) }}
                      </span>
                      <span v-else-if="field === 'url' || field === 'addr'" class="url-field">
                        {{ item[field] || 'N/A' }}
                      </span>
                      <span v-else-if="field === 'title'" class="title-field">
                        {{ item[field] || 'N/A' }}
                      </span>
                      <span v-else-if="field === 'status_code'" :class="getStatusCodeClass(item[field])">
                        {{ item[field] || 'N/A' }}
                      </span>
                      <span v-else-if="field === 'banner' || field === 'header'" class="code-field">
                        {{ truncateText(item[field], 50) }}
                      </span>
                      <span v-else>
                        {{ formatFieldValue(item[field]) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <!-- 字段说明 -->
            <div class="field-info">
              <h5>字段说明:</h5>
              <div class="field-list">
                <span v-for="field in allFields" :key="field" 
                      :class="{'active': visibleFields.includes(field)}"
                      @click="toggleField(field)"
                      class="field-tag">
                  {{ getFieldDisplayName(field) }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-else-if="!reportData && !reportError" class="loading-message">
            <div class="loading-spinner"></div>
            正在加载报告数据...
          </div>
          
          <!-- 错误信息 -->
          <div v-else-if="reportError" class="error-message">
            <div class="error-icon">⚠️</div>
            <p>{{ reportError }}</p>
          </div>
          
          <!-- 空数据状态 -->
          <div v-else-if="reportData && (!reportData.data || reportData.data.length === 0)" class="no-data">
            <div class="empty-icon">📊</div>
            <p>该任务没有扫描结果数据</p>
          </div>
        </div>
      </div>
    </div>
    
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
                <button 
                  @click="queryReport(task)" 
                  class="action-btn report"
                  title="查询报告"
                >
                  报告
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

// 报告弹窗相关状态
const showReportModal = ref(false)
const reportData = ref<any>(null)
const reportError = ref<string>('')
const currentTask = ref<Task | null>(null)

// 字段管理相关状态
const showAllFields = ref(false)
const allFields = ref<string[]>([])
const visibleFields = ref<string[]>([])

// 常用字段优先级（根据实际数据格式调整，排除response字段）
const priorityFields = [
  'url', 'subdomain', 'ip', 'port', 'status', 'alive', 'title', 'source',
  'addr', 'asn', 'cidr', 'isp', 'org', 'cname', 'module', 'resolver',
  'banner', 'header', 'history', 'reason', 'request', 'resolve', 'public', 'cdn'
]

// 其他可能字段（排除response字段）
const otherFields = [
  'elapse', 'find', 'ip_times', 'cname_times', 'ttl', 'level', 'port'
]

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

// 查询任务报告
const queryReport = async (task: Task) => {
  // 重置状态
  reportData.value = null
  reportError.value = ''
  currentTask.value = task
  showReportModal.value = true
  showAllFields.value = false
  allFields.value = []
  visibleFields.value = []
  
  try {
    // 使用域名作为参数，优先使用target，如果没有则使用targets
    const domain = task.target || task.targets || task.id
    const response = await fetch(`http://127.0.0.1:5000/api/result?domain=${encodeURIComponent(domain)}`)
    const data = await response.json()
    
    // 解析返回的数据结构
    if (data.success) {
      // 成功获取数据，显示在弹窗表格中
      reportData.value = data
      
      // 提取所有字段
      if (data.data && data.data.length > 0) {
        allFields.value = extractAllFields(data.data)
        
        // 默认显示有数据的字段
        visibleFields.value = allFields.value.filter(field => {
          return data.data.some((item: any) => item[field])
        })
        
        // 如果没有字段有数据，显示前几个字段
        if (visibleFields.value.length === 0 && allFields.value.length > 0) {
          visibleFields.value = allFields.value.slice(0, Math.min(8, allFields.value.length))
        }
      }
    } else {
      // 后端返回的错误信息
      reportError.value = data.error || data.message || '查询失败'
    }
  } catch (error) {
    console.error('查询报告失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    reportError.value = `网络请求失败: ${errorMessage}`
  }
}

// 关闭报告弹窗
const closeReportModal = () => {
  showReportModal.value = false
  reportData.value = null
  reportError.value = ''
  currentTask.value = null
  showAllFields.value = false
  allFields.value = []
  visibleFields.value = []
}

// 提取所有字段（排除response字段）
const extractAllFields = (data: any[]) => {
  const fields = new Set<string>()
  data.forEach(item => {
    Object.keys(item).forEach(key => {
      // 排除response字段
      if (key !== 'response') {
        fields.add(key)
      }
    })
  })
  
  // 按优先级排序
  const sortedFields = Array.from(fields).sort((a, b) => {
    const aIndex = priorityFields.indexOf(a)
    const bIndex = priorityFields.indexOf(b)
    
    if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex
    if (aIndex !== -1) return -1
    if (bIndex !== -1) return 1
    return a.localeCompare(b)
  })
  
  return sortedFields
}

// 获取字段显示名称
const getFieldDisplayName = (field: string) => {
  const fieldNames: Record<string, string> = {
    'url': 'URL地址',
    'subdomain': '子域名',
    'ip': 'IP地址',
    'port': '端口',
    'status': '状态码',
    'alive': '存活状态',
    'title': '页面标题',
    'source': '来源',
    'addr': '地理位置',
    'asn': 'ASN编号',
    'cidr': 'CIDR段',
    'isp': '运营商',
    'org': '组织',
    'cname': 'CNAME记录',
    'module': '扫描模块',
    'resolver': 'DNS解析器',
    'banner': 'Banner信息',
    'header': '响应头',
    'history': '跳转历史',
    'reason': '响应原因',
    'request': '请求状态',
    'resolve': '解析状态',
    'public': '公网IP',
    'cdn': 'CDN状态',
    'elapse': '扫描耗时',
    'find': '发现数量',
    'ip_times': 'IP出现次数',
    'cname_times': 'CNAME出现次数',
    'ttl': 'TTL值',
    'level': '域名级别'
  }
  return fieldNames[field] || field
}

// 获取字段样式类
const getFieldClass = (field: string) => {
  const fieldClasses: Record<string, string> = {
    'url': 'url-col',
    'subdomain': 'subdomain-col',
    'ip': 'ip-col',
    'port': 'port-col',
    'status': 'status-col',
    'alive': 'alive-col',
    'title': 'title-col',
    'source': 'source-col',
    'addr': 'addr-col',
    'asn': 'asn-col',
    'cidr': 'cidr-col',
    'isp': 'isp-col',
    'org': 'org-col'
  }
  return fieldClasses[field] || ''
}

// 格式化存活状态
const formatAliveStatus = (alive: any) => {
  if (alive === true || alive === 1 || alive === '1') return '存活'
  if (alive === false || alive === 0 || alive === '0') return '不存活'
  return '未知'
}

// 获取存活状态样式类
const getAliveClass = (alive: any) => {
  if (alive === true || alive === 1 || alive === '1') return 'alive-true'
  if (alive === false || alive === 0 || alive === '0') return 'alive-false'
  return 'alive-unknown'
}

// 获取状态码样式类
const getStatusCodeClass = (statusCode: any) => {
  if (!statusCode) return 'status-unknown'
  const code = parseInt(statusCode)
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 300 && code < 400) return 'status-redirect'
  if (code >= 400 && code < 500) return 'status-client-error'
  if (code >= 500) return 'status-server-error'
  return 'status-unknown'
}

// 格式化字段值
const formatFieldValue = (value: any) => {
  if (value === null || value === undefined || value === '') return 'N/A'
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (typeof value === 'number') return value.toString()
  if (typeof value === 'object') return JSON.stringify(value)
  return value.toString()
}

// 截断长文本
const truncateText = (text: string, maxLength: number) => {
  if (!text) return 'N/A'
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 切换字段显示
const toggleField = (field: string) => {
  const index = visibleFields.value.indexOf(field)
  if (index > -1) {
    visibleFields.value.splice(index, 1)
  } else {
    visibleFields.value.push(field)
  }
}

// 切换所有字段显示
const toggleAllFields = () => {
  showAllFields.value = !showAllFields.value
  
  if (showAllFields.value) {
    // 显示所有字段
    visibleFields.value = [...allFields.value]
  } else {
    // 只显示有数据的字段
    visibleFields.value = allFields.value.filter(field => {
      return reportData.value?.data?.some((item: any) => item[field])
    })
  }
}

// 导出为CSV
const exportToCSV = () => {
  if (!reportData.value?.data) return
  
  const data = reportData.value.data
  const fields = visibleFields.value
  
  // 创建CSV头部
  const headers = fields.map(field => getFieldDisplayName(field))
  const csvContent = [headers.join(',')]
  
  // 添加数据行
  data.forEach((item: any) => {
    const row = fields.map(field => {
      const value = item[field]
      // 处理特殊字符和逗号
      let formattedValue = formatFieldValue(value)
      if (formattedValue.includes(',') || formattedValue.includes('"') || formattedValue.includes('\n')) {
        formattedValue = `"${formattedValue.replace(/"/g, '""')}"`
      }
      return formattedValue
    })
    csvContent.push(row.join(','))
  })
  
  // 创建下载链接
  const blob = new Blob([csvContent.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `scan_report_${currentTask.value?.id || 'unknown'}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
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

.action-btn.report {
  background: #28a745;
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

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
  max-height: calc(90vh - 100px);
  overflow-y: auto;
}

.report-summary {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.report-summary p {
  margin: 5px 0;
  color: #333;
}

.data-table-section h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
}

.data-table tr:hover {
  background: #f5f5f5;
}

.no-data,
.error-message,
.loading-message {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  color: #dc3545;
}

/* 响应式弹窗 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .modal-body {
    padding: 15px;
  }
  
  .data-table th,
  .data-table td {
    padding: 8px;
    font-size: 12px;
  }
}

/* 报告页面增强样式 */
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.table-header h4 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.table-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.control-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.control-btn:hover {
  background: #f5f5f5;
  border-color: #ccc;
}

.control-btn.export {
  background: #28a745;
  color: white;
  border-color: #28a745;
}

.control-btn.export:hover {
  background: #218838;
  border-color: #1e7e34;
}

/* 字段标签样式 */
.field-info {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.field-info h5 {
  margin: 0 0 10px 0;
  color: #333;
}

.field-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.field-tag {
  padding: 4px 8px;
  background: #e9ecef;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-tag:hover {
  background: #dee2e6;
}

.field-tag.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

/* 特殊字段样式 */
.url-col {
  min-width: 200px;
  max-width: 300px;
}

.addr-col {
  min-width: 150px;
}

.ip-col {
  min-width: 120px;
}

.port-col {
  min-width: 60px;
  text-align: center;
}

.status-col {
  min-width: 80px;
  text-align: center;
}

.alive-col {
  min-width: 80px;
  text-align: center;
}

.title-col {
  min-width: 150px;
  max-width: 250px;
}

.source-col {
  min-width: 100px;
}

/* 运营商字段样式 - 确保横向排列 */
.isp-col {
  min-width: 120px;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asn-col, .cidr-col, .org-col {
  min-width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 状态样式 */
.alive-true {
  color: #28a745;
  font-weight: 600;
}

.alive-false {
  color: #dc3545;
  font-weight: 600;
}

.alive-unknown {
  color: #6c757d;
}

.status-success {
  color: #28a745;
  font-weight: 600;
}

.status-redirect {
  color: #ffc107;
  font-weight: 600;
}

.status-client-error {
  color: #fd7e14;
  font-weight: 600;
}

.status-server-error {
  color: #dc3545;
  font-weight: 600;
}

.status-unknown {
  color: #6c757d;
}

/* 文本字段样式 */
.url-field {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.title-field {
  font-weight: 500;
}

.code-field {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f8f9fa;
  padding: 2px 4px;
  border-radius: 2px;
}

/* 加载和状态图标 */
.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon, .empty-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.error-message, .no-data, .loading-message {
  text-align: center;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.error-message {
  color: #dc3545;
}

.no-data {
  color: #6c757d;
}

.loading-message {
  color: #007bff;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .table-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .table-controls {
    justify-content: center;
  }
  
  .url-col {
    min-width: 150px;
    max-width: 200px;
  }
  
  .title-col {
    min-width: 120px;
    max-width: 180px;
  }
}

@media (max-width: 768px) {
  .field-list {
    justify-content: center;
  }
  
  .table-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-btn {
    width: 100%;
    text-align: center;
  }
}
</style>