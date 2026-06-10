<template>
  <div class="settings">
    <h1>系统设置</h1>
    <div class="settings-content">
      <div class="settings-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="tab-button"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <section v-if="activeTab === 'appearance'" class="setting-section">
        <h2>外观设置</h2>
        <div class="setting-item">
          <label>系统主题色</label>
          <div class="theme-grid">
            <button
              v-for="theme in themeStore.themes"
              :key="theme.key"
              type="button"
              class="theme-card"
              :class="{ active: themeStore.currentThemeKey === theme.key }"
              @click="themeStore.applyTheme(theme.key)"
            >
              <span class="theme-preview-group">
                <span class="theme-preview primary" :style="{ background: theme.previewColor }"></span>
                <span class="theme-preview soft" :style="{ background: theme.variables['--theme-color-soft'] }"></span>
                <span class="theme-preview reading" :style="{ background: theme.variables['--reading-bg'] }"></span>
              </span>
              <span class="theme-info">
                <strong>{{ theme.name }}</strong>
                <small>{{ theme.description }}</small>
              </span>
              <span v-if="themeStore.currentThemeKey === theme.key" class="theme-current">当前使用</span>
            </button>
          </div>
        </div>
      </section>

      <section v-else-if="activeTab === 'basic'" class="setting-section">
        <h2>基本设置</h2>
        <div class="setting-item">
          <label>默认作者名</label>
          <input v-model="settings.defaultAuthor" type="text" />
        </div>
        <div class="setting-item">
          <label>默认目标字数</label>
          <input v-model.number="settings.defaultTargetWords" type="number" />
        </div>
      </section>

      <section v-else-if="activeTab === 'prompts'" class="setting-section">
        <div class="section-header">
          <h2>系统提示词管理</h2>
          <button class="btn-primary" @click="openPromptDialog()">添加提示词</button>
        </div>

        <div v-if="promptsLoading" class="loading">加载中...</div>
        <div v-else-if="prompts.length === 0" class="empty-logs">暂无提示词</div>
        <div v-else class="prompts-container">
          <div class="prompt-type-selector">
            <label>提示词类型：</label>
            <select v-model="activePromptType">
              <option v-for="type in promptTypes" :key="type" :value="type">{{ type }}</option>
            </select>
            <button class="btn-text" @click="showTypeManager = true">管理类型</button>
          </div>

          <div class="prompt-tabs">
            <button
              v-for="prompt in filteredPrompts"
              :key="prompt.id"
              class="prompt-tab"
              :class="{ active: activePromptId === prompt.id }"
              @click="activePromptId = prompt.id"
            >
              {{ prompt.name }}
            </button>
          </div>

          <div v-if="selectedPrompt" class="prompt-detail">
            <div class="prompt-detail-header">
              <h3>{{ selectedPrompt.name }}</h3>
              <span v-if="selectedPrompt.use_case" class="prompt-tag">{{ selectedPrompt.use_case }}</span>
            </div>
            <div class="prompt-detail-content">
              <textarea
                :value="selectedPrompt.system_prompt"
                class="prompt-textarea"
                rows="12"
                @blur="updatePromptContent($event, selectedPrompt.id)"
              ></textarea>
            </div>
          </div>
        </div>
      </section>

      <section v-else-if="activeTab === 'backup'" class="setting-section">
        <h2>备份设置</h2>
        <div class="setting-item checkbox-item">
          <label>自动备份</label>
          <input v-model="settings.autoBackup" type="checkbox" />
        </div>
        <div class="setting-item">
          <label>备份保留天数</label>
          <input v-model.number="settings.backupRetentionDays" type="number" />
        </div>
        <button class="btn-primary" @click="createBackup">立即备份</button>
      </section>

      <section v-else-if="activeTab === 'logs'" class="setting-section logs-section">
        <div class="section-header">
          <div>
            <h2>AI 调用日志</h2>
            <p>查看每次模型调用的接口、渠道、模型和脱敏请求参数。</p>
          </div>
          <button class="btn-primary" type="button" :disabled="logsLoading" @click="loadLogs">
            {{ logsLoading ? '加载中...' : '刷新' }}
          </button>
        </div>

        <div class="log-filters">
          <label>
            生成类型
            <select v-model="logFilters.generation_type" @change="resetAndLoadLogs">
              <option value="">全部类型</option>
              <option v-for="type in generationTypes" :key="type.value" :value="type.value">
                {{ type.label }}
              </option>
            </select>
          </label>
          <label>
            状态
            <select v-model="logFilters.status" @change="resetAndLoadLogs">
              <option value="">全部状态</option>
              <option value="success">成功</option>
              <option value="failed">失败</option>
              <option value="stopped">已停止</option>
            </select>
          </label>
        </div>

        <div v-if="logsError" class="log-error">{{ logsError }}</div>
        <div v-else-if="!logsLoading && logs.length === 0" class="empty-logs">暂无调用日志</div>
        <div v-else class="logs-table-wrapper">
          <table class="logs-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>接口</th>
                <th>渠道</th>
                <th>模型</th>
                <th>Token</th>
                <th>耗时</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td>{{ formatDateTime(log.created_at) }}</td>
                <td class="mono-cell">{{ log.api_endpoint || '-' }}</td>
                <td>{{ formatChannel(log) }}</td>
                <td>{{ formatModel(log) }}</td>
                <td>{{ formatTokens(log) }}</td>
                <td>{{ formatDuration(log.duration_seconds) }}</td>
                <td>
                  <span class="status-badge" :class="`status-${log.status || 'unknown'}`">
                    {{ formatStatus(log.status) }}
                  </span>
                </td>
                <td>
                  <button class="btn-link" type="button" @click="selectedLog = log">详情</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination">
          <button type="button" :disabled="logFilters.offset === 0 || logsLoading" @click="previousPage">
            上一页
          </button>
          <span>第 {{ currentPage }} 页</span>
          <button type="button" :disabled="logs.length < logFilters.limit || logsLoading" @click="nextPage">
            下一页
          </button>
        </div>
      </section>

      <section v-else class="setting-section">
        <h2>关于</h2>
        <p>AI小说写作系统 v1.0.0</p>
        <p>基于AI的本地小说创作工具</p>
      </section>
    </div>

    <div v-if="showPromptDialog" class="modal-overlay" @click.self="closePromptDialog">
      <div class="log-dialog">
        <div class="dialog-header">
          <h3>{{ editingPrompt ? '编辑提示词' : '添加提示词' }}</h3>
          <button type="button" class="close-button" @click="closePromptDialog">×</button>
        </div>
        <form @submit.prevent="savePrompt">
          <div class="form-group">
            <label>名称</label>
            <input v-model="promptForm.name" type="text" required />
          </div>
          <div class="form-group">
            <label>提示词类型</label>
            <select v-model="promptForm.prompt_type" required>
              <option v-for="type in promptTypes" :key="type" :value="type">{{ type }}</option>
              <option value="__new__">+ 新增类型</option>
            </select>
            <input
              v-if="promptForm.prompt_type === '__new__'"
              v-model="newPromptType"
              type="text"
              placeholder="输入新类型名称"
              style="margin-top: 8px"
              @blur="handleNewType"
            />
          </div>
          <div class="form-group">
            <label>提示词角色</label>
            <input v-model="promptForm.prompt_role" type="text" list="role-list" placeholder="例如：资深网文作家、角色设计专家" required />
            <datalist id="role-list">
              <option v-for="role in promptRoles" :key="role" :value="role" />
            </datalist>
          </div>
          <div class="form-group">
            <label>使用场景</label>
            <input v-model="promptForm.use_case" type="text" placeholder="例如：plan_novel、expand_character" />
          </div>
          <div class="form-group">
            <label>系统提示词</label>
            <textarea v-model="promptForm.system_prompt" rows="8" required></textarea>
          </div>
          <div class="dialog-actions">
            <button type="button" class="btn-secondary" @click="closePromptDialog">取消</button>
            <button type="submit" class="btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showTypeManager" class="modal-overlay" @click.self="showTypeManager = false">
      <div class="log-dialog">
        <div class="dialog-header">
          <h3>类型管理</h3>
          <button type="button" class="close-button" @click="showTypeManager = false">×</button>
        </div>
        <div class="type-manager-content">
          <div class="form-group">
            <label>添加新类型</label>
            <div style="display: flex; gap: 8px;">
              <input v-model="newTypeName" type="text" placeholder="输入类型名称" @keyup.enter="addType" />
              <button type="button" class="btn-primary" @click="addType">添加</button>
            </div>
          </div>
          <div class="type-list">
            <div v-for="type in promptTypes" :key="type" class="type-item">
              <span>{{ type }}</span>
              <button type="button" class="btn-text danger" @click="deleteType(type)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedLog" class="modal-overlay" @click.self="selectedLog = null">
      <div class="log-dialog">
        <div class="dialog-header">
          <h3>调用日志详情</h3>
          <button type="button" class="close-button" @click="selectedLog = null">×</button>
        </div>
        <div class="detail-grid">
          <span>请求接口</span>
          <strong>{{ selectedLog.api_endpoint || '-' }}</strong>
          <span>渠道</span>
          <strong>{{ formatChannel(selectedLog) }}</strong>
          <span>模型</span>
          <strong>{{ formatModel(selectedLog) }}</strong>
          <span>状态</span>
          <strong>{{ formatStatus(selectedLog.status) }}</strong>
          <span>调用时间</span>
          <strong>{{ formatDateTime(selectedLog.created_at) }}</strong>
        </div>
        <div class="detail-block">
          <h4>请求参数</h4>
          <pre>{{ formatRequestParams(selectedLog.request_params) }}</pre>
        </div>
        <div v-if="selectedLog.error_message" class="detail-block">
          <h4>错误信息</h4>
          <pre>{{ selectedLog.error_message }}</pre>
        </div>
      </div>
    </div>
    <ConfirmDialog ref="confirmDialog" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { logsApi } from '../api'
import { useThemeStore } from '../stores/theme'
import type { AIGenerationLog, GenerationLogsQuery } from '../types'
import ConfirmDialog from '../components/ConfirmDialog.vue'

type SettingsTab = 'appearance' | 'basic' | 'prompts' | 'backup' | 'logs' | 'about'

interface SystemPrompt {
  id: number
  name: string
  prompt_type: string
  prompt_role: string
  system_prompt: string
  use_case?: string
  is_default: boolean
  created_at: string
  updated_at: string
}

const tabs: Array<{ key: SettingsTab; label: string }> = [
  { key: 'appearance', label: '外观' },
  { key: 'basic', label: '基本' },
  { key: 'prompts', label: '系统提示词' },
  { key: 'backup', label: '备份' },
  { key: 'logs', label: '日志' },
  { key: 'about', label: '关于' },
]

const generationTypes = [
  { value: 'outline', label: '小说大纲' },
  { value: 'chapter_outline', label: '章节大纲' },
  { value: 'outline_polish', label: '大纲润色' },
  { value: 'character', label: '角色' },
  { value: 'content_generate', label: '正文生成' },
  { value: 'content_rewrite', label: '正文重写' },
  { value: 'content_selection_rewrite', label: '选区改写' },
  { value: 'content_polish', label: '正文润色' },
]

const themeStore = useThemeStore()
const activeTab = ref<SettingsTab>('appearance')
const confirmDialog = ref<InstanceType<typeof ConfirmDialog>>()

const prompts = ref<SystemPrompt[]>([])
const promptsLoading = ref(false)
const showPromptDialog = ref(false)
const editingPrompt = ref<SystemPrompt | null>(null)
const promptForm = ref({
  name: '',
  prompt_type: 'default',
  prompt_role: '',
  system_prompt: '',
  use_case: ''
})
const promptTypes = ref<string[]>([])
const promptRoles = ref<string[]>([])
const activePromptType = ref('default')
const activePromptId = ref<number | null>(null)
const newPromptType = ref('')
const showTypeManager = ref(false)
const newTypeName = ref('')

const filteredPrompts = computed(() => {
  return prompts.value.filter(p => p.prompt_type === activePromptType.value)
})

const selectedPrompt = computed(() => {
  return prompts.value.find(p => p.id === activePromptId.value) || null
})

// 监听类型切换，自动选中第一个提示词
watch(activePromptType, () => {
  const filtered = prompts.value.filter(p => p.prompt_type === activePromptType.value)
  if (filtered.length > 0) {
    activePromptId.value = filtered[0].id
  } else {
    activePromptId.value = null
  }
})

const handleNewType = () => {
  if (newPromptType.value.trim()) {
    promptForm.value.prompt_type = newPromptType.value.trim()
    if (!promptTypes.value.includes(promptForm.value.prompt_type)) {
      promptTypes.value.push(promptForm.value.prompt_type)
    }
    newPromptType.value = ''
  }
}

const logs = ref<AIGenerationLog[]>([])
const logsLoading = ref(false)
const logsError = ref('')
const selectedLog = ref<AIGenerationLog | null>(null)
const logFilters = ref<Required<GenerationLogsQuery>>({
  limit: 20,
  offset: 0,
  generation_type: '',
  status: '',
})
const settings = ref({
  defaultAuthor: '默认作者',
  defaultTargetWords: 1000000,
  autoBackup: true,
  backupRetentionDays: 30,
})

const currentPage = computed(() => Math.floor(logFilters.value.offset / logFilters.value.limit) + 1)

const createBackup = () => {
  alert('备份功能开发中')
}

const switchTab = (tab: SettingsTab) => {
  activeTab.value = tab
  if (tab === 'logs' && logs.value.length === 0) {
    loadLogs()
  }
  if (tab === 'prompts' && prompts.value.length === 0) {
    loadPrompts()
  }
}

const loadPrompts = async () => {
  promptsLoading.value = true
  try {
    const [promptsRes, typesRes, rolesRes] = await Promise.all([
      fetch('http://localhost:8000/api/prompts/'),
      fetch('http://localhost:8000/api/prompts/types/'),
      fetch('http://localhost:8000/api/prompts/roles/')
    ])
    prompts.value = await promptsRes.json()
    promptTypes.value = await typesRes.json()
    promptRoles.value = await rolesRes.json()

    // 自动选中第一个提示词
    if (prompts.value.length > 0) {
      activePromptId.value = prompts.value[0].id
    }
  } catch (error) {
    console.error('加载提示词失败:', error)
  } finally {
    promptsLoading.value = false
  }
}

const openPromptDialog = (prompt?: SystemPrompt) => {
  if (prompt) {
    editingPrompt.value = prompt
    promptForm.value = {
      name: prompt.name,
      prompt_type: prompt.prompt_type,
      prompt_role: prompt.prompt_role,
      system_prompt: prompt.system_prompt,
      use_case: prompt.use_case || ''
    }
  } else {
    editingPrompt.value = null
    promptForm.value = { name: '', prompt_type: 'default', prompt_role: '', system_prompt: '', use_case: '' }
  }
  showPromptDialog.value = true
}

const closePromptDialog = () => {
  showPromptDialog.value = false
  editingPrompt.value = null
}

const savePrompt = async () => {
  try {
    if (editingPrompt.value) {
      await fetch(`http://localhost:8000/api/prompts/${editingPrompt.value.id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(promptForm.value)
      })
    } else {
      await fetch('http://localhost:8000/api/prompts/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(promptForm.value)
      })
    }
    await loadPrompts()
    closePromptDialog()
  } catch (error) {
    console.error('保存提示词失败:', error)
  }
}

const deletePrompt = async (id: number) => {
  const confirmed = await confirmDialog.value?.show({
    title: '删除提示词',
    message: '确定要删除这个系统提示词吗？',
    confirmText: '删除',
    type: 'danger'
  })

  if (!confirmed) return

  try {
    await fetch(`http://localhost:8000/api/prompts/${id}/`, { method: 'DELETE' })
    await loadPrompts()
  } catch (error) {
    console.error('删除提示词失败:', error)
  }
}

const addType = () => {
  const name = newTypeName.value.trim()
  if (name && !promptTypes.value.includes(name)) {
    promptTypes.value.push(name)
    activePromptType.value = name
    newTypeName.value = ''
  }
}

const deleteType = async (type: string) => {
  const count = prompts.value.filter(p => p.prompt_type === type).length
  const confirmed = await confirmDialog.value?.show({
    title: '删除类型',
    message: `确定要删除类型"${type}"吗？${count > 0 ? `该类型下有 ${count} 个提示词。` : ''}`,
    confirmText: '删除',
    type: 'danger'
  })

  if (!confirmed) return

  promptTypes.value = promptTypes.value.filter(t => t !== type)
  if (activePromptType.value === type && promptTypes.value.length > 0) {
    activePromptType.value = promptTypes.value[0]
  }
}

const updatePromptContent = async (event: Event, id: number) => {
  const textarea = event.target as HTMLTextAreaElement
  const newContent = textarea.value.trim()
  const prompt = prompts.value.find(p => p.id === id)

  if (!prompt || newContent === prompt.system_prompt) return

  try {
    await fetch(`http://localhost:8000/api/prompts/${id}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...prompt, system_prompt: newContent })
    })
    prompt.system_prompt = newContent
  } catch (error) {
    console.error('保存提示词失败:', error)
    textarea.value = prompt.system_prompt
  }
}

const buildLogQuery = () => {
  const query: GenerationLogsQuery = {
    limit: logFilters.value.limit,
    offset: logFilters.value.offset,
  }

  if (logFilters.value.generation_type) {
    query.generation_type = logFilters.value.generation_type
  }
  if (logFilters.value.status) {
    query.status = logFilters.value.status
  }

  return query
}

const loadLogs = async () => {
  logsLoading.value = true
  logsError.value = ''

  try {
    const response = await logsApi.list(buildLogQuery())
    logs.value = response.data
  } catch (error: any) {
    logsError.value = error.response?.data?.detail || error.message || '日志加载失败'
  } finally {
    logsLoading.value = false
  }
}

const resetAndLoadLogs = () => {
  logFilters.value.offset = 0
  loadLogs()
}

const previousPage = () => {
  logFilters.value.offset = Math.max(0, logFilters.value.offset - logFilters.value.limit)
  loadLogs()
}

const nextPage = () => {
  logFilters.value.offset += logFilters.value.limit
  loadLogs()
}

const formatDateTime = (value: string) => new Date(value).toLocaleString('zh-CN')

const formatDuration = (value?: number) => {
  if (value === undefined || value === null) return '-'
  return `${value.toFixed(2)}s`
}

const formatTokens = (log: AIGenerationLog) => `${log.input_tokens || 0}/${log.output_tokens || 0}`

const formatChannel = (log: AIGenerationLog) => {
  if (!log.channel_name && !log.channel_provider) return '-'
  return [log.channel_name, log.channel_provider].filter(Boolean).join(' / ')
}

const formatModel = (log: AIGenerationLog) => {
  if (!log.model_name && !log.model_identifier) return '-'
  return [log.model_name, log.model_identifier].filter(Boolean).join(' / ')
}

const formatStatus = (status?: string) => {
  const statusMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    stopped: '已停止',
  }
  return status ? statusMap[status] || status : '-'
}

const formatRequestParams = (params?: string) => {
  if (!params) return '无请求参数'

  try {
    return JSON.stringify(JSON.parse(params), null, 2)
  } catch {
    return params
  }
}
</script>

<style scoped>
.settings {
  max-width: 75%;
  margin: 0 auto;
  padding: 24px;
}

.settings h1 {
  margin-bottom: 30px;
  color: var(--text-primary);
  font-size: 28px;
}

.settings-content {
  padding: 30px;
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: var(--shadow-soft);
}

.settings-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 28px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.tab-button {
  padding: 9px 18px;
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover,
.tab-button.active {
  color: white;
  background: var(--theme-color);
  border-color: var(--theme-color);
}

.setting-section h2 {
  margin-bottom: 20px;
  padding-bottom: 10px;
  color: var(--text-primary);
  font-size: 20px;
  border-bottom: 2px solid var(--theme-color-border);
}

.setting-section p {
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.setting-item {
  margin-bottom: 20px;
}

.setting-item label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-primary);
  font-weight: 600;
}

.setting-item input[type="text"],
.setting-item input[type="number"],
.log-filters select {
  width: 100%;
  padding: 10px;
  color: var(--text-primary);
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-sizing: border-box;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.checkbox-item label {
  margin-bottom: 0;
}

.setting-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--theme-color);
  cursor: pointer;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.theme-card {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  min-height: 92px;
  padding: 14px;
  text-align: left;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s, background 0.2s;
}

.theme-card:hover {
  background: color-mix(in srgb, var(--theme-color-soft) 46%, var(--panel-bg));
  border-color: var(--theme-color-border);
  box-shadow: var(--shadow-soft);
  transform: translateY(-1px);
}

.theme-card.active {
  background: color-mix(in srgb, var(--theme-color-soft) 62%, var(--panel-bg));
  border-color: var(--theme-color);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--theme-color) 12%, transparent);
}

.theme-preview-group {
  display: grid;
  grid-template-columns: repeat(3, 18px);
  overflow: hidden;
  border: 3px solid var(--panel-bg);
  border-radius: 999px;
  box-shadow: 0 0 0 1px var(--border-color);
}

.theme-preview {
  width: 18px;
  height: 36px;
}

.theme-preview.primary {
  border-top-left-radius: 999px;
  border-bottom-left-radius: 999px;
}

.theme-preview.reading {
  border-top-right-radius: 999px;
  border-bottom-right-radius: 999px;
}

.theme-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.theme-info strong {
  color: var(--text-primary);
}

.theme-info small {
  color: var(--text-secondary);
  line-height: 1.5;
}

.theme-current {
  grid-column: 1 / -1;
  width: fit-content;
  padding: 3px 8px;
  color: var(--theme-color);
  background: var(--panel-bg);
  border: 1px solid var(--theme-color-border);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 6px 14px color-mix(in srgb, var(--theme-color) 10%, transparent);
}

.section-header,
.log-filters,
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.section-header {
  margin-bottom: 18px;
}

.log-filters {
  justify-content: flex-start;
  margin-bottom: 18px;
}

.log-filters label {
  display: grid;
  gap: 6px;
  min-width: 180px;
  color: var(--text-primary);
  font-weight: 600;
}

.logs-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border-color);
  border-radius: 10px;
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 860px;
}

.logs-table th,
.logs-table td {
  padding: 12px;
  color: var(--text-primary);
  text-align: left;
  border-bottom: 1px solid var(--border-color);
}

.logs-table th {
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  font-size: 13px;
}

.logs-table tr:last-child td {
  border-bottom: none;
}

.mono-cell {
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
}

.status-badge {
  display: inline-flex;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.status-success {
  color: var(--success-color);
  background: var(--success-bg);
  border: 1px solid var(--success-border);
}

.status-failed,
.status-unknown {
  color: var(--danger-color);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
}

.status-stopped {
  color: var(--warning-color);
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
}

.log-error,
.empty-logs {
  padding: 18px;
  border-radius: 10px;
}

.log-error {
  color: var(--danger-color);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
}

.empty-logs {
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
}

.pagination {
  justify-content: center;
  margin-top: 18px;
  color: var(--text-secondary);
}

.btn-primary,
.pagination button,
.btn-link,
.close-button {
  cursor: pointer;
}

.btn-primary {
  padding: 10px 20px;
  color: white;
  background: var(--theme-color);
  border: none;
  border-radius: 6px;
  font-size: 16px;
}

.btn-primary:hover:not(:disabled) {
  background: var(--theme-color-hover);
}

.btn-primary:disabled,
.pagination button:disabled {
  color: var(--disabled-text);
  background: var(--disabled-bg);
  cursor: not-allowed;
}

.pagination button,
.btn-link {
  padding: 7px 12px;
  color: var(--theme-color);
  background: var(--theme-color-soft);
  border: 1px solid var(--theme-color-border);
  border-radius: 6px;
}

.btn-link {
  padding: 5px 10px;
}

.prompts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.prompts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.prompt-type-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.prompt-type-selector label {
  color: var(--text-primary);
  font-weight: 600;
}

.prompt-type-selector select {
  padding: 8px 12px;
  color: var(--text-primary);
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  min-width: 150px;
}

.prompt-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  white-space: nowrap;
  padding-bottom: 8px;
}

.prompt-tabs::-webkit-scrollbar {
  height: 6px;
}

.prompt-tabs::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.prompt-tab {
  padding: 8px 16px;
  background: var(--panel-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.prompt-tab:hover {
  background: var(--theme-color-soft);
  color: var(--theme-color);
}

.prompt-tab.active {
  background: var(--theme-color);
  color: white;
  border-color: var(--theme-color);
}

.prompt-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.prompt-detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.prompt-detail-header h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.prompt-textarea {
  width: 100%;
  padding: 12px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-family: var(--font-mono, 'SF Mono', Monaco, 'Cascadia Code', monospace);
  font-size: 13px;
  line-height: 1.6;
  resize: vertical;
  min-height: 200px;
  transition: all 0.2s;
}

.prompt-textarea:focus {
  background: var(--panel-bg);
  border-color: var(--theme-color);
  outline: none;
  box-shadow: 0 0 0 3px var(--theme-color-soft);
}

.prompt-tag {
  padding: 4px 10px;
  background: var(--theme-color-soft);
  color: var(--theme-color);
  border-radius: 4px;
  font-size: 12px;
}

.prompt-detail-content {
  display: flex;
  flex-direction: column;
}

.prompt-actions {
  display: flex;
  gap: 8px;
}

.btn-text {
  color: var(--theme-color);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-text:hover {
  color: var(--theme-color-hover);
}

.btn-text.danger {
  color: var(--danger-color);
}

.type-manager-content {
  padding: 20px;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.type-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 6px;
}

.type-item span {
  color: var(--text-primary);
  font-weight: 500;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--panel-bg);
  color: var(--text-primary);
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--dialog-overlay);
}

.log-dialog {
  width: min(760px, 100%);
  max-height: 86vh;
  overflow-y: auto;
  padding: 24px;
  background: var(--dialog-bg);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: var(--shadow-soft);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.dialog-header h3 {
  margin: 0;
  color: var(--text-primary);
}

.close-button {
  width: 32px;
  height: 32px;
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 50%;
  font-size: 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 10px 16px;
  margin-bottom: 18px;
}

.detail-grid span {
  color: var(--text-secondary);
}

.detail-grid strong {
  color: var(--text-primary);
  word-break: break-all;
}

.detail-block h4 {
  margin: 16px 0 8px;
  color: var(--text-primary);
}

.detail-block pre {
  overflow-x: auto;
  max-height: 300px;
  padding: 14px;
  color: var(--text-primary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
