<template>
  <div class="channels">
    <div class="header">
      <h1>AI渠道管理</h1>
      <button class="btn-primary" @click="showCreateDialog = true">
        + 添加渠道
      </button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="channels-list">
      <div
        v-for="channel in channels"
        :key="channel.id"
        class="channel-card"
        :class="{ disabled: !channel.is_enabled }"
      >
        <div class="channel-header">
          <div class="channel-title">
            <h3>{{ channel.name }}</h3>
            <span class="provider-badge">{{ channel.provider }}</span>
            <span class="model-count">{{ channel.model_count }} 个模型</span>
          </div>
          <div class="actions">
            <button class="btn-icon" @click="viewModels(channel)">
              管理模型
            </button>
            <button class="btn-icon" @click="toggleChannel(channel)">
              {{ channel.is_enabled ? '禁用' : '启用' }}
            </button>
            <button class="btn-icon" @click="editChannel(channel)">编辑</button>
            <button class="btn-icon btn-danger" @click="deleteChannel(channel.id)">
              删除
            </button>
          </div>
        </div>
        <div class="channel-info">
          <div class="info-item">
            <span class="label">API地址：</span>
            <span>{{ channel.base_url || '默认' }}</span>
          </div>
          <div class="info-item">
            <span class="label">创建时间：</span>
            <span>{{ formatDate(channel.created_at) }}</span>
          </div>
        </div>
        <div v-if="!channel.is_enabled" class="disabled-badge">已禁用</div>
      </div>
    </div>

    <!-- 创建/编辑渠道对话框 -->
    <div v-if="showCreateDialog || editingChannel" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog">
        <h2>{{ editingChannel ? '编辑渠道' : '添加渠道' }}</h2>
        <form @submit.prevent="handleSaveChannel">
          <div class="form-group">
            <label>渠道名称</label>
            <input v-model="formData.name" type="text" required />
          </div>
          <div class="form-group">
            <label>提供商</label>
            <select v-model="formData.provider" required :disabled="!!editingChannel">
              <option value="newapi">NewAPI</option>
            </select>
          </div>
          <div class="form-group">
            <label>API密钥</label>
            <input v-model="formData.api_key" type="password" placeholder="保持为空则不修改" />
          </div>
          <div class="form-group">
            <label>API地址（可选）</label>
            <input v-model="formData.base_url" type="text" placeholder="留空使用默认地址" />
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="closeDialog">
              取消
            </button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 模型管理对话框 -->
    <div v-if="showModelsDialog" class="dialog-overlay" @click.self="showModelsDialog = false">
      <div class="dialog dialog-large">
        <h2>{{ currentChannel?.name }} - 模型管理</h2>

        <!-- 添加模型按钮 -->
        <div class="models-header">
          <button class="btn-primary" @click="showAddModel">
            + 添加模型
          </button>
        </div>

        <!-- 模型列表 -->
        <div v-if="loadingModels" class="loading">加载中...</div>
        <div v-else class="models-list">
          <div v-if="models.length === 0" class="empty-state">
            暂无模型，请点击"添加模型"开始
          </div>
          <div
            v-for="model in models"
            :key="model.id"
            class="model-item"
            :class="{ disabled: !model.is_enabled }"
          >
            <div class="model-info">
              <h4>{{ model.model_name }}</h4>
              <p class="model-id">{{ model.model_id }}</p>
              <div class="model-meta">
                <span>温度: {{ model.temperature }}</span>
                <span>输入: ${{ model.cost_per_1k_input_tokens }}/1K</span>
                <span>输出: ${{ model.cost_per_1k_output_tokens }}/1K</span>
                <span v-if="model.response_time_ms" class="speed-badge">
                  {{ model.response_time_ms }}ms
                </span>
              </div>
            </div>
            <div class="model-actions">
              <button
                class="btn-icon"
                @click="testModelSpeed(model.id)"
                :disabled="testingModelId === model.id"
              >
                {{ testingModelId === model.id ? '测速中...' : '测速' }}
              </button>
              <button class="btn-icon" @click="toggleModel(model)">
                {{ model.is_enabled ? '禁用' : '启用' }}
              </button>
              <button class="btn-icon btn-danger" @click="deleteModel(model.id)">
                删除
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加模型对话框 -->
    <div v-if="showAddModelDialog" class="dialog-overlay" @click.self="showAddModelDialog = false">
      <div class="dialog dialog-wide">
        <h2>添加模型到 {{ currentChannel?.name }}</h2>

        <div v-if="loadingAvailableModels" class="loading">
          <div class="loading-spinner"></div>
          <p>正在获取模型列表...</p>
        </div>
        <div v-else>
          <div class="form-group">
            <label>
              选择模型 (共 {{ availableModels.length }} 个可用)
              <span class="hint">可多选，按住 Ctrl/Cmd 点击</span>
            </label>
            <div class="model-select-container">
              <div class="model-select-list">
                <div
                  v-for="availModel in availableModels"
                  :key="availModel.id"
                  class="model-select-item"
                  :class="{ selected: selectedModelIds.includes(availModel.id) }"
                  @click="toggleModelSelection(availModel.id)"
                >
                  <div class="model-select-checkbox">
                    <input
                      type="checkbox"
                      :checked="selectedModelIds.includes(availModel.id)"
                      :id="`model-${availModel.id}`"
                      @click.stop="toggleModelSelection(availModel.id)"
                    />
                  </div>
                  <label :for="`model-${availModel.id}`" class="model-select-info">
                    <div class="model-name">{{ availModel.name || availModel.id }}</div>
                    <div class="model-description">{{ availModel.description || availModel.id }}</div>
                  </label>
                </div>
              </div>
            </div>
            <div v-if="selectedModelIds.length > 0" class="selected-count">
              已选择 {{ selectedModelIds.length }} 个模型
            </div>
          </div>

          <div class="config-section">
            <h3>默认模型配置（可在添加后单独调整）</h3>
            <div class="form-row">
              <div class="form-group">
                <label>温度参数 (Temperature)</label>
                <input
                  v-model.number="modelFormData.temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  placeholder="0.8"
                />
                <small>控制输出随机性，0=确定性，2=最随机</small>
              </div>

              <div class="form-group">
                <label>输入成本 ($/1K tokens)</label>
                <input
                  v-model.number="modelFormData.cost_per_1k_input_tokens"
                  type="number"
                  step="0.001"
                  min="0"
                  placeholder="0.000"
                />
                <small>每1000个输入token的成本</small>
              </div>

              <div class="form-group">
                <label>输出成本 ($/1K tokens)</label>
                <input
                  v-model.number="modelFormData.cost_per_1k_output_tokens"
                  type="number"
                  step="0.001"
                  min="0"
                  placeholder="0.000"
                />
                <small>每1000个输出token的成本</small>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn-secondary" @click="showAddModelDialog = false">
              取消
            </button>
            <button
              type="button"
              class="btn-primary"
              @click="handleAddModels"
              :disabled="selectedModelIds.length === 0"
            >
              添加 {{ selectedModelIds.length }} 个模型
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { channelApi, modelApi } from '../api'
import type { AIChannel, AIModel, AvailableModel } from '../types'

const channels = ref<AIChannel[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const editingChannel = ref<AIChannel | null>(null)

const formData = ref({
  name: '',
  provider: 'newapi',
  api_key: '',
  base_url: '',
})

// 模型管理
const showModelsDialog = ref(false)
const currentChannel = ref<AIChannel | null>(null)
const models = ref<AIModel[]>([])
const loadingModels = ref(false)

// 添加模型
const showAddModelDialog = ref(false)
const availableModels = ref<AvailableModel[]>([])
const loadingAvailableModels = ref(false)
const selectedModelIds = ref<string[]>([])
const modelFormData = ref({
  temperature: 0.8,
  cost_per_1k_input_tokens: 0.0,
  cost_per_1k_output_tokens: 0.0,
})

// 测速
const testingModelId = ref<number | null>(null)

// 切换模型选择
const toggleModelSelection = (modelId: string) => {
  const index = selectedModelIds.value.indexOf(modelId)
  if (index > -1) {
    selectedModelIds.value.splice(index, 1)
  } else {
    selectedModelIds.value.push(modelId)
  }
}

onMounted(async () => {
  await loadChannels()
})

const loadChannels = async () => {
  loading.value = true
  try {
    const response = await channelApi.list()
    channels.value = response.data
  } catch (error) {
    console.error('加载渠道失败:', error)
    alert('加载渠道失败')
  } finally {
    loading.value = false
  }
}

const editChannel = (channel: AIChannel) => {
  editingChannel.value = channel
  formData.value = {
    name: channel.name,
    provider: channel.provider,
    api_key: '',
    base_url: channel.base_url || '',
  }
}

const toggleChannel = async (channel: AIChannel) => {
  try {
    await channelApi.update(channel.id, { is_enabled: !channel.is_enabled })
    await loadChannels()
  } catch (error) {
    alert('操作失败')
  }
}

const deleteChannel = async (id: number) => {
  if (!confirm('确定删除此渠道？这将同时删除其下所有模型。')) return

  try {
    await channelApi.delete(id)
    await loadChannels()
  } catch (error) {
    alert('删除失败')
  }
}

const handleSaveChannel = async () => {
  try {
    const data: any = {
      name: formData.value.name,
      base_url: formData.value.base_url || undefined,
    }

    if (formData.value.api_key) {
      data.api_key = formData.value.api_key
    }

    if (editingChannel.value) {
      await channelApi.update(editingChannel.value.id, data)
    } else {
      data.provider = formData.value.provider
      data.api_key = formData.value.api_key || undefined
      await channelApi.create(data)
    }

    await loadChannels()
    closeDialog()
  } catch (error) {
    alert('保存失败')
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  editingChannel.value = null
  formData.value = {
    name: '',
    provider: 'newapi',
    api_key: '',
    base_url: '',
  }
}

// 模型管理
const viewModels = async (channel: AIChannel) => {
  currentChannel.value = channel
  showModelsDialog.value = true
  await loadModels(channel.id)
}

const loadModels = async (channelId: number) => {
  loadingModels.value = true
  try {
    const response = await modelApi.list(channelId)
    models.value = response.data
  } catch (error) {
    console.error('加载模型失败:', error)
    alert('加载模型失败')
  } finally {
    loadingModels.value = false
  }
}

const showAddModel = async () => {
  if (!currentChannel.value) return

  showAddModelDialog.value = true
  loadingAvailableModels.value = true
  selectedModelIds.value = []

  try {
    const response = await channelApi.getAvailableModels(currentChannel.value.id)
    availableModels.value = response.data
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    alert('获取模型列表失败: ' + errorMsg)
    showAddModelDialog.value = false
  } finally {
    loadingAvailableModels.value = false
  }
}

const handleAddModels = async () => {
  if (!currentChannel.value || selectedModelIds.value.length === 0) return

  const addCount = selectedModelIds.value.length

  try {
    // 批量添加模型
    for (const modelId of selectedModelIds.value) {
      const selected = availableModels.value.find((m) => m.id === modelId)
      if (!selected) continue

      await modelApi.create({
        channel_id: currentChannel.value.id,
        model_name: selected.name,
        model_id: selected.id,
        temperature: modelFormData.value.temperature,
        cost_per_1k_input_tokens: modelFormData.value.cost_per_1k_input_tokens,
        cost_per_1k_output_tokens: modelFormData.value.cost_per_1k_output_tokens,
      })
    }

    await loadModels(currentChannel.value.id)
    await loadChannels()
    showAddModelDialog.value = false
    selectedModelIds.value = []
    alert(`成功添加 ${addCount} 个模型`)
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || error.message || '未知错误'
    alert('添加模型失败: ' + errorMsg)
  }
}

const toggleModel = async (model: AIModel) => {
  try {
    await modelApi.update(model.id, { is_enabled: !model.is_enabled })
    if (currentChannel.value) {
      await loadModels(currentChannel.value.id)
    }
  } catch (error) {
    alert('操作失败')
  }
}

const deleteModel = async (modelId: number) => {
  if (!confirm('确定删除此模型？')) return

  try {
    await modelApi.delete(modelId)
    if (currentChannel.value) {
      await loadModels(currentChannel.value.id)
      await loadChannels()
    }
  } catch (error) {
    alert('删除失败')
  }
}

const testModelSpeed = async (modelId: number) => {
  testingModelId.value = modelId

  try {
    const response = await modelApi.testSpeed(modelId)
    alert(`响应时间: ${response.data.response_time_ms}ms`)
    if (currentChannel.value) {
      await loadModels(currentChannel.value.id)
    }
  } catch (error: any) {
    alert('测速失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testingModelId.value = null
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}
</script>

<style scoped>
.channels {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: var(--text-primary);
}

.btn-primary {
  background: var(--success-color);
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: color-mix(in srgb, var(--success-color) 84%, var(--text-primary));
}

.btn-primary:disabled {
  background: var(--disabled-bg);
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--disabled-bg);
  color: var(--text-primary);
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: var(--hover-bg);
}

.dialog-wide {
  width: 800px;
  max-width: 95%;
}

.loading {
  text-align: center;
  padding: 50px;
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 15px;
  border: 4px solid var(--disabled-bg);
  border-top: 4px solid var(--success-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  margin: 0;
  font-size: 14px;
}

.channels-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.channel-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  position: relative;
}

.channel-card.disabled {
  opacity: 0.6;
}

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.channel-title {
  display: flex;
  align-items: center;
  gap: 15px;
}

.channel-title h3 {
  margin: 0;
  font-size: 20px;
}

.provider-badge {
  padding: 4px 10px;
  background: var(--info-color);
  color: white;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;
}

.model-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn-icon {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-icon:hover {
  background: var(--hover-bg);
}

.btn-danger {
  color: var(--danger-color);
  border-color: var(--danger-color);
}

.btn-danger:hover {
  background: var(--danger-bg);
}

.channel-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.info-item {
  display: flex;
  gap: 8px;
}

.info-item .label {
  font-weight: 500;
  color: var(--text-secondary);
}

.disabled-badge {
  position: absolute;
  top: 20px;
  right: 20px;
  background: var(--danger-color);
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--dialog-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 30px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-large {
  width: 900px;
}

.dialog h2 {
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  box-sizing: border-box;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: var(--text-muted);
  font-size: 12px;
}

.config-section {
  margin-top: 25px;
  padding-top: 25px;
  border-top: 1px solid var(--border-color);
}

.config-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: var(--text-primary);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
}

/* 模型管理 */
.models-header {
  margin-bottom: 20px;
}

.models-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.model-item.disabled {
  opacity: 0.5;
}

.model-info h4 {
  margin: 0 0 5px 0;
}

.model-id {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 5px 0;
}

.model-meta {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.speed-badge {
  background: var(--success-color);
  color: white;
  padding: 2px 8px;
  border-radius: 3px;
}

.model-actions {
  display: flex;
  gap: 8px;
}

/* 模型选择样式优化 */
.model-select-container {
  border: 1px solid var(--border-color);
  border-radius: 5px;
  background: var(--panel-bg-soft);
  padding: 10px;
}

.model-select-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-select-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 15px;
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.model-select-item:hover {
  border-color: var(--success-color);
  box-shadow: var(--shadow-soft);
}

.model-select-item.selected {
  background: var(--success-bg);
  border-color: var(--success-color);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--success-color) 20%, transparent);
}

.model-select-checkbox {
  display: flex;
  align-items: center;
  padding-top: 2px;
}

.model-select-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: normal;
}

.selected-count {
  margin-top: 10px;
  padding: 8px 12px;
  background: var(--success-bg);
  border-radius: 4px;
  color: var(--success-color);
  font-size: 14px;
  font-weight: 500;
}

.model-select-info {
  flex: 1;
  cursor: pointer;
  margin: 0;
}

.model-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.model-description {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.model-select-item.selected .model-name {
  color: var(--success-color);
}

.model-select-item.selected .model-description {
  color: var(--success-color);
}
</style>
