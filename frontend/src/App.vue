<template>
  <div id="app">
    <nav class="main-nav">
      <div class="nav-brand">AI小说写作系统</div>
      <div class="nav-links">
        <router-link to="/bookshelf">小说书架</router-link>
        <router-link to="/channels">AI渠道</router-link>
        <router-link to="/settings">系统设置</router-link>
      </div>
    </nav>
    <router-view />
    <ModelSwitcher />
  </div>
</template>

<script setup lang="ts">
import ModelSwitcher from './components/ModelSwitcher.vue'
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: #f5f5f5;
}

.main-nav {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.nav-links {
  display: flex;
  gap: 30px;
}

.nav-links a {
  color: #666;
  text-decoration: none;
  padding: 8px 16px;
  border-radius: 5px;
  transition: all 0.2s;
}

.nav-links a:hover {
  background: #f5f5f5;
  color: #333;
}

.nav-links a.router-link-active {
  background: #4CAF50;
  color: white;
}
</style>
