<template>
  <div class="model-switcher" v-if="availableModels.length > 0">
    <div class="switcher-button" @click="showDropdown = !showDropdown">
      <div class="current-model">
        <span class="model-icon">🤖</span>
        <div class="model-info">
          <div class="model-name">{{ currentModel?.model_name || '未选择模型' }}</div>
          <div class="model-provider">{{ currentModel?.provider || '-' }}</div>
        </div>
      </div>
      <span class="arrow" :class="{ open: showDropdown }">▼</span>
    </div>

    <transition name="dropdown">
      <div v-if="showDropdown" class="dropdown-menu" @click.stop>
        <div class="dropdown-header">
          <h4>选择AI模型</h4>
          <button class="close-btn" @click="showDropdown = false">✕</button>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <span>加载中...</span>
        </div>

        <div v-else class="models-list">
          <div
            v-for="model in availableModels"
            :key="model.id"
            class="model-option"
            :class="{ active: currentModelId === model.id, disabled: !model.is_enabled }"
            @click="selectModel(model)"
          >
            <div class="option-content">
              <div class="option-main">
                <span class="option-name">{{ model.model_name }}</span>
                <span v-if="!model.is_enabled" class="disabled-badge">已禁用</span>
              </div>
              <div class="option-meta">
                <span class="provider-tag">{{ model.provider }}</span>
                <span v-if="model.response_time_ms" class="speed-tag">{{ model.response_time_ms }}ms</span>
              </div>
            </div>
            <span v-if="currentModelId === model.id" class="check-icon">✓</span>
          </div>

          <div v-if="availableModels.length === 0" class="empty-state">
            <p>暂无可用模型</p>
            <router-link to="/channels" class="link-button">去添加模型</router-link>
          </div>
        </div>
      </div>
    </transition>

    <!-- 点击外部关闭 -->
    <div v-if="showDropdown" class="overlay" @click="showDropdown = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { channelApi, modelApi } from '../api'
import type { AIChannel, AIModel } from '../types'

interface ModelWithProvider extends AIModel {
  provider: string
}

const showDropdown = ref(false)
const loading = ref(false)
const channels = ref<AIChannel[]>([])
const allModels = ref<AIModel[]>([])
const currentModelId = ref<number | null>(null)

// 获取所有可用模型（带提供商信息）
const availableModels = computed<ModelWithProvider[]>(() => {
  return allModels.value
    .filter(model => model.is_enabled)
    .map(model => {
      const channel = channels.value.find(c => c.id === model.channel_id)
      return {
        ...model,
        provider: channel?.provider || 'unknown',
      }
    })
})

// 当前选中的模型
const currentModel = computed(() => {
  if (!currentModelId.value) return null
  return availableModels.value.find(m => m.id === currentModelId.value)
})

onMounted(async () => {
  await loadModels()
  loadCurrentModel()
})

const loadModels = async () => {
  loading.value = true
  try {
    // 获取所有渠道
    const channelsRes = await channelApi.list()
    channels.value = channelsRes.data.filter(c => c.is_enabled)

    // 获取所有渠道的模型
    const modelPromises = channels.value.map(channel => modelApi.list(channel.id))
    const modelsResponses = await Promise.all(modelPromises)

    allModels.value = modelsResponses.flatMap(res => res.data)
  } catch (error) {
    console.error('加载模型失败:', error)
  } finally {
    loading.value = false
  }
}

const loadCurrentModel = () => {
  const saved = localStorage.getItem('selected_model_id')
  if (saved) {
    currentModelId.value = parseInt(saved)
  } else if (availableModels.value.length > 0) {
    // 默认选择第一个模型
    currentModelId.value = availableModels.value[0].id
    localStorage.setItem('selected_model_id', String(currentModelId.value))
  }
}

const selectModel = (model: ModelWithProvider) => {
  if (!model.is_enabled) return

  currentModelId.value = model.id
  localStorage.setItem('selected_model_id', String(model.id))
  showDropdown.value = false

  // 触发全局事件通知其他组件
  window.dispatchEvent(new CustomEvent('model-changed', { detail: model }))
}
</script>

<style scoped>
.model-switcher {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 999;
}

.switcher-button {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.2s;
  min-width: 220px;
}

.switcher-button:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  border-color: #4CAF50;
}

.current-model {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.model-icon {
  font-size: 24px;
}

.model-info {
  flex: 1;
}

.model-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.model-provider {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
}

.arrow {
  font-size: 10px;
  color: #999;
  transition: transform 0.2s;
}

.arrow.open {
  transform: rotate(180deg);
}

.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}

.dropdown-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 10px;
  width: 320px;
  max-height: 400px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}

.dropdown-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #f0f0f0;
  border-top: 3px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.models-list {
  overflow-y: auto;
  max-height: 340px;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f5f5f5;
}

.model-option:last-child {
  border-bottom: none;
}

.model-option:hover {
  background: #f9f9f9;
}

.model-option.active {
  background: #e8f5e9;
}

.model-option.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-option.disabled:hover {
  background: white;
}

.option-content {
  flex: 1;
}

.option-main {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.option-name {
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.disabled-badge {
  font-size: 10px;
  padding: 2px 6px;
  background: #ffebee;
  color: #c62828;
  border-radius: 3px;
}

.option-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.provider-tag {
  padding: 2px 6px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 3px;
  text-transform: uppercase;
  font-weight: 500;
}

.speed-tag {
  padding: 2px 6px;
  background: #e8f5e9;
  color: #2e7d32;
  border-radius: 3px;
}

.check-icon {
  color: #4CAF50;
  font-size: 18px;
  font-weight: bold;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state p {
  margin: 0 0 15px 0;
  color: #999;
}

.link-button {
  display: inline-block;
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  text-decoration: none;
  border-radius: 4px;
  font-size: 14px;
}

.link-button:hover {
  background: #45a049;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
