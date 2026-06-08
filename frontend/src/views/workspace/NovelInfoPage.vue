<template>
  <div class="tab-content">
    <div class="tab-header">
      <h2>小说信息</h2>
      <div class="info-actions">
        <button class="btn-secondary" :disabled="loading || isSavingInfo" @click="loadNovelInfo">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
        <button
          v-if="!isEditingInfo"
          class="btn-primary"
          :disabled="!novel || loading"
          @click="startEditInfo"
        >
          编辑
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
          <div>
            <h3>{{ novel.title }}</h3>
            <p>{{ novel.synopsis || '暂无简介' }}</p>
          </div>
          <span class="status-badge">{{ getStatusLabel(novel.status) }}</span>
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
            <label>当前字数</label>
            <span>{{ formatNumber(novel.current_words) }} 字</span>
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
            <span>{{ getProgressPercent(novel) }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${getProgressPercent(novel)}%` }"></div>
          </div>
          <span class="progress-text">
            {{ formatNumber(novel.current_words) }} / {{ formatNumber(novel.target_words) }} 字
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
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useNovelStore } from '../../stores/novel'
import type { Novel } from '../../types'

const props = defineProps<{
  novelId: number
}>()

const novelStore = useNovelStore()
const { currentNovel: novel, loading } = storeToRefs(novelStore)

type NovelInfoForm = {
  title: string
  author: string
  genre: string
  status: string
  target_words: number
  synopsis: string
}

const isEditingInfo = ref(false)
const isSavingInfo = ref(false)
const infoError = ref('')
const infoForm = ref<NovelInfoForm>(createInfoForm())

onMounted(() => {
  void loadNovelInfo()
})

function createInfoForm(): NovelInfoForm {
  return {
    title: '',
    author: '默认作者',
    genre: '',
    status: 'planning',
    target_words: 1000000,
    synopsis: '',
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
</script>

<style scoped>
.tab-content {
  background: white;
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
}

.info-summary h3 {
  margin: 0 0 10px;
  color: #333;
  font-size: 24px;
}

.info-summary p {
  margin: 0;
  color: #666;
  line-height: 1.7;
  white-space: pre-wrap;
}

.status-badge {
  flex-shrink: 0;
  padding: 5px 12px;
  color: white;
  background: #3498db;
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
  border: 1px solid #eee;
  border-radius: 8px;
}

.info-card label,
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 600;
}

.info-card span {
  color: #333;
  font-size: 16px;
  font-weight: 500;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #555;
  font-size: 14px;
}

.progress-bar {
  width: 100%;
  height: 10px;
  overflow: hidden;
  background: #f0f0f0;
  border-radius: 5px;
}

.progress-fill {
  height: 100%;
  background: #4CAF50;
  transition: width 0.3s;
}

.progress-text {
  display: block;
  margin-top: 8px;
  color: #666;
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
  border: 1px solid #ddd;
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
  color: #b42318;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
}

.error-message button {
  color: #b42318;
  background: transparent;
  border: none;
  cursor: pointer;
}

.loading {
  padding: 50px;
  color: #666;
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
  background: #4CAF50;
}

.btn-secondary {
  color: #333;
  background: #ccc;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
