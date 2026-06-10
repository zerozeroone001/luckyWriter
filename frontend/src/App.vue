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
  background: var(--app-bg);
}

.main-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 30px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-soft);
}

.nav-brand {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 30px;
}

.nav-links a {
  padding: 8px 16px;
  color: var(--text-secondary);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.2s;
}

.nav-links a:hover {
  color: var(--theme-color);
  background: var(--theme-color-soft);
}

.nav-links a.router-link-active {
  color: white;
  background: var(--theme-color);
}
</style>
