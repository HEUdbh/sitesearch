<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const activeMenu = ref('home')

const menuItems = [
  { key: 'home', label: '主页', icon: '🏠', path: '/' },
  { key: 'tasks', label: '任务信息查询', icon: '📋', path: '/task' }
]

const setActiveMenu = (menuKey: string) => {
  const menuItem = menuItems.find(item => item.key === menuKey)
  if (menuItem) {
    activeMenu.value = menuKey
    router.push(menuItem.path)
  }
}

// 监听路由变化，更新activeMenu
watch(() => route.path, (newPath) => {
  const menuItem = menuItems.find(item => item.path === newPath)
  if (menuItem) {
    activeMenu.value = menuItem.key
  }
}, { immediate: true })
</script>

<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>站点搜索系统</h2>
      </div>
      <nav class="sidebar-nav">
        <ul>
          <li 
            v-for="item in menuItems" 
            :key="item.key"
            :class="{ active: activeMenu === item.key }"
            @click="setActiveMenu(item.key)"
          >
            <span class="icon">{{ item.icon }}</span>
            <span class="label">{{ item.label }}</span>
          </li>
        </ul>
      </nav>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #34495e;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
}

.sidebar-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-nav li {
  padding: 15px 20px;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
}

.sidebar-nav li:hover {
  background: #34495e;
}

.sidebar-nav li.active {
  background: #3498db;
}

.sidebar-nav .icon {
  margin-right: 10px;
  font-size: 1.1rem;
}

.sidebar-nav .label {
  font-size: 0.95rem;
}

.main-content {
  flex: 1;
  background: #ecf0f1;
  overflow-y: auto;
}
</style>
