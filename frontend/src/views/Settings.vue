<template>
  <div class="settings">
    <h1>系统设置</h1>
    <div class="settings-content">
      <div class="setting-section">
        <h2>基本设置</h2>
        <div class="setting-item">
          <label>默认作者名</label>
          <input v-model="settings.defaultAuthor" type="text" />
        </div>
        <div class="setting-item">
          <label>默认目标字数</label>
          <input v-model.number="settings.defaultTargetWords" type="number" />
        </div>
      </div>

      <div class="setting-section">
        <h2>备份设置</h2>
        <div class="setting-item">
          <label>自动备份</label>
          <input v-model="settings.autoBackup" type="checkbox" />
        </div>
        <div class="setting-item">
          <label>备份保留天数</label>
          <input v-model.number="settings.backupRetentionDays" type="number" />
        </div>
        <button class="btn-primary" @click="createBackup">立即备份</button>
      </div>

      <div class="setting-section">
        <h2>关于</h2>
        <p>AI小说写作系统 v1.0.0</p>
        <p>基于AI的本地小说创作工具</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const settings = ref({
  defaultAuthor: '默认作者',
  defaultTargetWords: 1000000,
  autoBackup: true,
  backupRetentionDays: 30,
})

const createBackup = () => {
  alert('备份功能开发中')
}
</script>

<style scoped>
.settings {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.settings h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 30px;
}

.settings-content {
  background: white;
  border-radius: 8px;
  padding: 30px;
}

.setting-section {
  margin-bottom: 40px;
}

.setting-section h2 {
  font-size: 20px;
  color: #333;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.setting-item input[type="text"],
.setting-item input[type="number"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-sizing: border-box;
}

.setting-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.btn-primary {
  background: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary:hover {
  background: #45a049;
}
</style>
