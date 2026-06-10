<template>
  <div class="tab-content">
    <div class="tab-header">
      <h2>小说信息</h2>
      <div class="info-actions">
        <button class="btn-secondary" :disabled="loading || isSavingInfo" @click="loadNovelInfo">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
        <button class="btn-secondary" :disabled="loading || isSavingInfo" @click="loadStats">
          {{ loadingStats ? '统计中...' : '刷新统计' }}
        </button>
        <button
          v-if="!isEditingInfo"
          class="btn-primary"
          :disabled="!novel || loading"
          @click="startEditInfo"
        >
          编辑
        </button>
        <button
          v-if="!isEditingInfo"
          class="btn-danger"
          :disabled="!novel || loading"
          @click="deleteNovel"
        >
          删除小说
        </button>
        <template v-else>
          <button class="btn-secondary" :disabled="isSavingInfo" @click="cancelEditInfo">取消</button>
          <button class="btn-primary" :disabled="isSavingInfo" @click="saveNovelInfo">
            {{ isSavingInfo ? '保存中...' : '保存' }}
          </button>
        </template>
      </div>
    </div>

    <div v-if="infoError" class="error-message">
      <span>{{ infoError }}</span>
      <button type="button" @click="infoError = ''">关闭</button>
    </div>

    <div v-if="loading && !novel" class="loading">小说信息加载中...</div>

    <div v-else-if="novel" class="novel-info">
      <div v-if="!isEditingInfo" class="info-display">
        <div class="info-summary">
          <h3>{{ novel.title }}</h3>
          <span class="status-badge">{{ getStatusLabel(novel.status) }}</span>
        </div>

        <div class="info-section">
          <div class="section-header">
            <label>小说简介</label>
            <div class="section-actions">
              <button class="btn-secondary btn-sm" @click="generateSynopsis">{{ novel.synopsis ? '重新生成' : '生成' }}</button>
              <button v-if="novel.synopsis" class="btn-secondary btn-sm" @click="polishSynopsis">润色</button>
            </div>
          </div>
          <p class="section-content">{{ novel.synopsis || '暂无简介' }}</p>
        </div>

        <div class="info-section">
          <div class="section-header">
            <label>系统风格提示词</label>
            <div class="section-actions">
              <button class="btn-secondary btn-sm" @click="generateStylePrompt">{{ novel.style_prompt ? '重新生成' : '生成' }}</button>
              <button v-if="novel.style_prompt" class="btn-secondary btn-sm" @click="polishStylePrompt">润色</button>
            </div>
          </div>
          <p class="section-content">{{ novel.style_prompt || '暂无风格提示词' }}</p>
        </div>

        <div class="info-grid">
          <div class="info-card">
            <label>作者</label>
            <span>{{ novel.author || '默认作者' }}</span>
          </div>
          <div class="info-card">
            <label>类型</label>
            <span>{{ novel.genre || '未指定' }}</span>
          </div>
          <div class="info-card">
            <label>章节数</label>
            <span>{{ stats?.chapter_count ?? 0 }} 章</span>
          </div>
          <div class="info-card">
            <label>当前字数</label>
            <span>{{ formatNumber(stats?.total_words ?? novel.current_words) }} 字</span>
          </div>
          <div class="info-card">
            <label>目标字数</label>
            <span>{{ formatNumber(novel.target_words) }} 字</span>
          </div>
          <div class="info-card">
            <label>创建时间</label>
            <span>{{ formatDate(novel.created_at) }}</span>
          </div>
          <div class="info-card">
            <label>更新时间</label>
            <span>{{ formatDate(novel.updated_at) }}</span>
          </div>
        </div>

        <div class="info-progress">
          <div class="progress-header">
            <span>写作进度</span>
            <span>{{ stats?.progress ?? getProgressPercent(novel) }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${stats?.progress ?? getProgressPercent(novel)}%` }"></div>
          </div>
          <span class="progress-text">
            {{ formatNumber(stats?.total_words ?? novel.current_words) }} / {{ formatNumber(novel.target_words) }} 字
          </span>
        </div>
      </div>

      <form v-else class="info-form" @submit.prevent="saveNovelInfo">
        <div class="form-row">
          <div class="form-group">
            <label>小说标题</label>
            <input v-model="infoForm.title" type="text" required :disabled="isSavingInfo" />
          </div>
          <div class="form-group">
            <label>作者</label>
            <input v-model="infoForm.author" type="text" :disabled="isSavingInfo" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>类型</label>
            <select v-model="infoForm.genre" :disabled="isSavingInfo">
              <option value="">请选择</option>
              <option value="玄幻">玄幻</option>
              <option value="都市">都市</option>
              <option value="历史">历史</option>
              <option value="科幻">科幻</option>
              <option value="言情">言情</option>
              <option value="武侠">武侠</option>
            </select>
          </div>
          <div class="form-group">
            <label>状态</label>
            <select v-model="infoForm.status" :disabled="isSavingInfo">
              <option value="planning">规划中</option>
              <option value="writing">创作中</option>
              <option value="completed">已完成</option>
              <option value="paused">已暂停</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>目标字数</label>
          <input v-model.number="infoForm.target_words" type="number" min="1" required :disabled="isSavingInfo" />
        </div>
        <div class="form-group">
          <label>简介</label>
          <textarea v-model="infoForm.synopsis" rows="5" :disabled="isSavingInfo"></textarea>
        </div>
        <div class="form-group">
          <label>系统风格提示词</label>
          <textarea v-model="infoForm.style_prompt" rows="5" :disabled="isSavingInfo" placeholder="在此输入写作风格要求，AI 生成内容时会参考此提示词"></textarea>
        </div>
      </form>
    </div>

    <div v-if="showDialog" class="dialog-overlay" @click.self="closeDialog">
      <div class="dialog-box">
        <h3>{{ dialogTitle }}</h3>
        <textarea
          ref="dialogInput"
          v-model="dialogValue"
          :placeholder="dialogPlaceholder"
          rows="4"
          :disabled="isGenerating"
        ></textarea>
        <button v-if="!generatedContent && !isGenerating" class="btn-primary btn-full" @click="startGenerate">开始生成</button>
        <div v-if="isGenerating" class="generating-indicator">
          <div class="spinner"></div>
          <span>AI 生成中，请稍候...</span>
        </div>
        <div v-if="generatedContent" class="preview-section">
          <label>生成结果：</label>
          <div class="preview-content">{{ generatedContent }}</div>
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" :disabled="isGenerating" @click="closeDialog">{{ generatedContent ? '放弃' : '取消' }}</button>
          <button v-if="generatedContent" class="btn-primary" @click="confirmSave">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useNovelStore } from '../../stores/novel'
import { novelApi } from '../../api'
import type { Novel, NovelStats } from '../../types'

const props = defineProps<{
  novelId: number
}>()

const router = useRouter()
const novelStore = useNovelStore()
const { currentNovel: novel, loading } = storeToRefs(novelStore)

type NovelInfoForm = {
  title: string
  author: string
  genre: string
  status: string
  target_words: number
  synopsis: string
  style_prompt: string
}

const isEditingInfo = ref(false)
const isSavingInfo = ref(false)
const loadingStats = ref(false)
const infoError = ref('')
const stats = ref<NovelStats | null>(null)
const infoForm = ref<NovelInfoForm>(createInfoForm())

const showDialog = ref(false)
const dialogTitle = ref('')
const dialogPlaceholder = ref('')
const dialogValue = ref('')
const dialogLoading = ref(false)
const dialogCallback = ref<((value: string) => Promise<void>) | null>(null)
const generatedContent = ref('')
const isGenerating = ref(false)
const dialogInput = ref<HTMLTextAreaElement | null>(null)

onMounted(() => {
  void loadNovelInfo()
  void loadStats()
})

function createInfoForm(): NovelInfoForm {
  return {
    title: '',
    author: '默认作者',
    genre: '',
    status: 'planning',
    target_words: 1000000,
    synopsis: '',
    style_prompt: '',
  }
}

const loadNovelInfo = async () => {
  infoError.value = ''

  try {
    await novelStore.loadNovel(props.novelId)
  } catch (error) {
    infoError.value = getErrorMessage(error, '加载小说信息失败')
  }
}

const startEditInfo = () => {
  if (!novel.value) return

  infoForm.value = {
    title: novel.value.title,
    author: novel.value.author || '默认作者',
    genre: novel.value.genre || '',
    status: novel.value.status || 'planning',
    target_words: novel.value.target_words,
    synopsis: novel.value.synopsis || '',
    style_prompt: novel.value.style_prompt || '',
  }
  infoError.value = ''
  isEditingInfo.value = true
}

const cancelEditInfo = () => {
  if (isSavingInfo.value) return
  infoError.value = ''
  isEditingInfo.value = false
}

const saveNovelInfo = async () => {
  infoError.value = ''

  const payload = {
    title: infoForm.value.title.trim(),
    author: infoForm.value.author.trim() || '默认作者',
    genre: infoForm.value.genre.trim() || undefined,
    status: infoForm.value.status,
    target_words: Number(infoForm.value.target_words),
    synopsis: infoForm.value.synopsis.trim() || undefined,
    style_prompt: infoForm.value.style_prompt.trim() || undefined,
  }

  if (!payload.title) {
    infoError.value = '小说标题不能为空'
    return
  }

  if (!payload.target_words || payload.target_words <= 0) {
    infoError.value = '目标字数必须大于 0'
    return
  }

  isSavingInfo.value = true

  try {
    await novelStore.updateNovel(props.novelId, payload)
    isEditingInfo.value = false
  } catch (error) {
    infoError.value = getErrorMessage(error, '保存小说信息失败')
  } finally {
    isSavingInfo.value = false
  }
}

const getProgressPercent = (targetNovel: Novel) => {
  if (!targetNovel.target_words || targetNovel.target_words <= 0) return 0
  return Math.min(100, Math.round((targetNovel.current_words / targetNovel.target_words) * 100))
}

const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    planning: '规划中',
    writing: '创作中',
    completed: '已完成',
    paused: '已暂停',
  }

  return statusMap[status] || status || '未知'
}

const formatNumber = (value: number) => new Intl.NumberFormat('zh-CN').format(value || 0)

const formatDate = (value: string) => {
  if (!value) return '未知时间'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未知时间'

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

const getErrorMessage = (error: unknown, fallback: string) => {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response
    return response?.data?.detail || fallback
  }

  if (error instanceof Error) return error.message || fallback
  return fallback
}

const loadStats = async () => {
  if (!props.novelId) return

  loadingStats.value = true

  try {
    const response = await novelApi.stats(props.novelId)
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  } finally {
    loadingStats.value = false
  }
}

const deleteNovel = async () => {
  if (!novel.value) return

  const confirmed = window.confirm(
    `确定要删除小说《${novel.value.title}》吗？\n\n此操作将删除小说及其所有相关数据（大纲、章节、角色等），且不可恢复！`
  )
  if (!confirmed) return

  const doubleConfirmed = window.confirm('再次确认：真的要删除这部小说吗？')
  if (!doubleConfirmed) return

  try {
    await novelApi.delete(props.novelId)
    alert('小说已删除')
    await router.push('/bookshelf')
  } catch (error) {
    infoError.value = getErrorMessage(error, '删除小说失败')
  }
}

const generateSynopsis = async () => {
  if (!novel.value) return
  dialogTitle.value = '生成小说简介'
  dialogPlaceholder.value = '请输入生成要求（可选），例如：突出主角的成长历程、强调悬疑氛围等'
  dialogValue.value = ''
  generatedContent.value = ''
  dialogCallback.value = async (requirements: string) => {
    return fetch('http://127.0.0.1:8000/api/ai/generate-synopsis/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ novel_id: props.novelId, requirements })
    })
  }
  showDialog.value = true
  await nextTick()
  dialogInput.value?.focus()
}

const polishSynopsis = async () => {
  if (!novel.value?.synopsis) return
  dialogTitle.value = '润色小说简介'
  dialogPlaceholder.value = '请输入润色建议（可选），例如：增强文学性、更突出卖点等'
  dialogValue.value = ''
  generatedContent.value = ''
  dialogCallback.value = async (requirements: string) => {
    return fetch('http://127.0.0.1:8000/api/ai/polish-synopsis/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ novel_id: props.novelId, current_synopsis: novel.value!.synopsis })
    })
  }
  showDialog.value = true
  await nextTick()
  dialogInput.value?.focus()
}

const generateStylePrompt = async () => {
  if (!novel.value) return
  dialogTitle.value = '生成系统风格提示词'
  dialogPlaceholder.value = '请输入生成要求（可选），例如：偏向古风雅致、现代简练等'
  dialogValue.value = ''
  generatedContent.value = ''
  dialogCallback.value = async (requirements: string) => {
    return fetch('http://127.0.0.1:8000/api/ai/generate-style-prompt/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ novel_id: props.novelId, requirements })
    })
  }
  showDialog.value = true
  await nextTick()
  dialogInput.value?.focus()
}

const polishStylePrompt = async () => {
  if (!novel.value?.style_prompt) return
  dialogTitle.value = '润色系统风格提示词'
  dialogPlaceholder.value = '请输入润色建议（可选），例如：更具体、更简洁等'
  dialogValue.value = ''
  generatedContent.value = ''
  dialogCallback.value = async (requirements: string) => {
    return fetch('http://127.0.0.1:8000/api/ai/polish-style-prompt/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ novel_id: props.novelId, current_prompt: novel.value!.style_prompt })
    })
  }
  showDialog.value = true
  await nextTick()
  dialogInput.value?.focus()
}

const startGenerate = async () => {
  if (!dialogCallback.value) return
  isGenerating.value = true
  generatedContent.value = ''
  infoError.value = ''

  try {
    const response = await dialogCallback.value(dialogValue.value)
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) throw new Error('无法读取响应流')

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6))
          if (event.type === 'chunk') {
            generatedContent.value += event.content
          } else if (event.type === 'error') {
            throw new Error(event.message)
          }
        }
      }
    }
  } catch (error) {
    infoError.value = getErrorMessage(error, '生成失败')
  } finally {
    isGenerating.value = false
  }
}

const confirmSave = async () => {
  if (!generatedContent.value) return

  try {
    const updateData: any = {}
    if (dialogTitle.value.includes('简介')) {
      updateData.synopsis = generatedContent.value
    } else if (dialogTitle.value.includes('风格')) {
      updateData.style_prompt = generatedContent.value
    }

    await novelStore.updateNovel(props.novelId, updateData)
    await loadNovelInfo()
    showDialog.value = false
  } catch (error) {
    infoError.value = getErrorMessage(error, '保存失败')
  }
}

const closeDialog = () => {
  if (isGenerating.value) return
  showDialog.value = false
  dialogValue.value = ''
  generatedContent.value = ''
  dialogCallback.value = null
}

</script>

<style scoped>
.tab-content {
  background: var(--card-bg);
  border-radius: 8px;
  min-height: 500px;
  padding: 30px;
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.info-actions,
.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.novel-info,
.info-display,
.info-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 20px;
  background: var(--panel-bg-soft);
  border-radius: 8px;
}

.info-summary h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}

.info-summary p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.info-section {
  padding: 20px;
  background: var(--panel-bg-soft);
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header label {
  margin: 0;
  color: var(--text-secondary);
  font-weight: 600;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.section-content {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.status-badge {
  flex-shrink: 0;
  padding: 5px 12px;
  color: white;
  background: var(--info-color);
  border-radius: 999px;
  font-size: 13px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.info-card,
.info-progress {
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.info-card label,
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 600;
}

.info-card span {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 500;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.progress-bar {
  width: 100%;
  height: 10px;
  overflow: hidden;
  background: var(--disabled-bg);
  border-radius: 5px;
}

.progress-fill {
  height: 100%;
  background: var(--success-color);
  transition: width 0.3s;
}

.progress-text {
  display: block;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  box-sizing: border-box;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  padding: 12px 16px;
  color: var(--danger-color);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: 6px;
}

.error-message button {
  color: var(--danger-color);
  background: transparent;
  border: none;
  cursor: pointer;
}

.loading {
  padding: 50px;
  color: var(--text-secondary);
  text-align: center;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.btn-primary {
  color: white;
  background: var(--success-color);
}

.btn-secondary {
  color: var(--text-primary);
  background: var(--disabled-bg);
}

.btn-danger {
  padding: 10px 20px;
  color: white;
  background: var(--danger-color);
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.btn-primary:disabled,
.btn-secondary:disabled,
.btn-danger:disabled {
  background: var(--disabled-bg);
  cursor: not-allowed;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.dialog-box {
  width: 500px;
  max-width: 90vw;
  padding: 24px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog-box h3 {
  margin: 0 0 16px;
  color: var(--text-primary);
  font-size: 18px;
}

.dialog-box textarea {
  width: 100%;
  padding: 10px;
  margin-bottom: 16px;
  color: var(--text-primary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 5px;
  box-sizing: border-box;
  resize: vertical;
}

.btn-full {
  width: 100%;
  margin-bottom: 16px;
}

.generating-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  margin-bottom: 16px;
  color: var(--primary-color);
  background: var(--panel-bg-soft);
  border-radius: 5px;
  font-size: 14px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-section {
  margin-bottom: 16px;
}

.preview-section label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 600;
}

.preview-content {
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  color: var(--text-primary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 5px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
