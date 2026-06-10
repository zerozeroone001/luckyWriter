<template>
  <div class="bookshelf">
    <div class="header">
      <div>
        <h1>小说书架</h1>
        <p class="subtitle">管理你的小说项目，快速进入创作工作区</p>
      </div>
      <button class="btn-primary" @click="openCreateDialog">+ 新建小说</button>
    </div>

    <div class="toolbar">
      <input
        v-model.trim="searchKeyword"
        class="search-input"
        type="text"
        placeholder="搜索标题、作者、类型或简介"
      />
      <select v-model="statusFilter" class="toolbar-select">
        <option value="all">全部状态</option>
        <option value="planning">规划中</option>
        <option value="writing">创作中</option>
        <option value="completed">已完成</option>
        <option value="paused">已暂停</option>
      </select>
      <select v-model="genreFilter" class="toolbar-select">
        <option value="all">全部类型</option>
        <option v-for="genre in availableGenres" :key="genre" :value="genre">
          {{ genre }}
        </option>
      </select>
      <select v-model="sortBy" class="toolbar-select">
        <option value="updated_desc">最近更新</option>
        <option value="created_desc">最新创建</option>
        <option value="title_asc">标题排序</option>
        <option value="progress_desc">进度优先</option>
      </select>
      <button class="btn-secondary" :disabled="loading" @click="loadBookshelf">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="errorMessage" class="error-message">
      <span>{{ errorMessage }}</span>
      <button type="button" @click="errorMessage = ''">关闭</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="novels.length === 0" class="empty-state">
      <h2>书架还是空的</h2>
      <p>创建第一本小说后，就可以开始规划大纲、角色和章节。</p>
      <button class="btn-primary" @click="openCreateDialog">创建第一本小说</button>
    </div>

    <div v-else-if="filteredNovels.length === 0" class="empty-state">
      <h2>没有匹配的小说</h2>
      <p>试试调整搜索关键词、类型或状态筛选。</p>
      <button class="btn-secondary" @click="resetFilters">清空筛选</button>
    </div>

    <div v-else class="novel-grid">
      <div
        v-for="novel in filteredNovels"
        :key="novel.id"
        class="novel-card"
        @click="openNovel(novel.id)"
      >
        <div class="cover">
          <img v-if="novel.cover_image" :src="novel.cover_image" alt="封面" />
          <div v-else class="cover-placeholder">{{ getTitleInitial(novel.title) }}</div>
          <span class="status-badge">{{ getStatusLabel(novel.status) }}</span>
        </div>
        <div class="info">
          <div class="card-title-row">
            <h3>{{ novel.title }}</h3>
            <button class="btn-delete" type="button" @click.stop="deleteNovel(novel.id)">
              删除
            </button>
          </div>
          <p class="author">作者：{{ novel.author || '默认作者' }}</p>
          <p class="genre">{{ novel.genre || '未分类' }}</p>
          <p class="synopsis">{{ novel.synopsis || '暂无简介' }}</p>
          <div class="progress">
            <div class="progress-header">
              <span>写作进度</span>
              <span>{{ getProgressPercent(novel) }}%</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${getProgressPercent(novel)}%` }"
              ></div>
            </div>
            <span class="progress-text">
              {{ formatNumber(novel.current_words) }} / {{ formatNumber(novel.target_words) }} 字
            </span>
          </div>
          <p class="updated-at">更新于 {{ formatDate(novel.updated_at) }}</p>
        </div>
      </div>
    </div>

    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="closeCreateDialog">
      <div class="dialog">
        <h2>新建小说</h2>
        <form @submit.prevent="handleCreate">
          <div v-if="formError" class="form-error">{{ formError }}</div>
          <div class="form-group">
            <label>小说标题</label>
            <input v-model="newNovel.title" type="text" required :disabled="submitting" />
          </div>
          <div class="form-group">
            <label>作者</label>
            <input v-model="newNovel.author" type="text" :disabled="submitting" />
          </div>
          <div class="form-group">
            <label>类型</label>
            <select v-model="newNovel.genre" :disabled="submitting">
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
            <label>目标字数</label>
            <input
              v-model.number="newNovel.target_words"
              type="number"
              min="1"
              required
              :disabled="submitting"
            />
          </div>
          <div class="form-group">
            <label>简介</label>
            <textarea v-model="newNovel.synopsis" rows="4" :disabled="submitting"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="submitting" @click="closeCreateDialog">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="submitting">
              {{ submitting ? '创建中...' : '创建' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useNovelStore } from '../stores/novel'
import type { Novel, NovelCreate } from '../types'

type SortBy = 'updated_desc' | 'created_desc' | 'title_asc' | 'progress_desc'

const router = useRouter()
const novelStore = useNovelStore()
const { novels, loading } = storeToRefs(novelStore)

const showCreateDialog = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const formError = ref('')
const searchKeyword = ref('')
const statusFilter = ref('all')
const genreFilter = ref('all')
const sortBy = ref<SortBy>('updated_desc')
const newNovel = ref<NovelCreate>(createDefaultNovel())

const availableGenres = computed(() => {
  const genres = novels.value
    .map((novel) => novel.genre?.trim())
    .filter((genre): genre is string => Boolean(genre))

  return [...new Set(genres)].sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const filteredNovels = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()

  return [...novels.value]
    .filter((novel) => {
      const searchableText = [novel.title, novel.author, novel.genre, novel.synopsis]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      const matchesKeyword = !keyword || searchableText.includes(keyword)
      const matchesStatus = statusFilter.value === 'all' || novel.status === statusFilter.value
      const matchesGenre = genreFilter.value === 'all' || novel.genre === genreFilter.value

      return matchesKeyword && matchesStatus && matchesGenre
    })
    .sort((a, b) => {
      if (sortBy.value === 'created_desc') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      }

      if (sortBy.value === 'title_asc') {
        return a.title.localeCompare(b.title, 'zh-CN')
      }

      if (sortBy.value === 'progress_desc') {
        return getProgressPercent(b) - getProgressPercent(a)
      }

      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
})

onMounted(() => {
  loadBookshelf()
})

function createDefaultNovel(): NovelCreate {
  return {
    title: '',
    author: '默认作者',
    genre: '',
    target_words: 1000000,
    synopsis: '',
  }
}

const loadBookshelf = async () => {
  errorMessage.value = ''

  try {
    await novelStore.loadNovels()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加载小说列表失败')
  }
}

const openCreateDialog = () => {
  formError.value = ''
  showCreateDialog.value = true
}

const closeCreateDialog = () => {
  if (submitting.value) return
  showCreateDialog.value = false
}

const openNovel = (id: number) => {
  router.push(`/novel/${id}`)
}

const resetFilters = () => {
  searchKeyword.value = ''
  statusFilter.value = 'all'
  genreFilter.value = 'all'
  sortBy.value = 'updated_desc'
}

const handleCreate = async () => {
  errorMessage.value = ''
  formError.value = ''

  const payload: NovelCreate = {
    title: newNovel.value.title.trim(),
    author: newNovel.value.author?.trim() || '默认作者',
    genre: newNovel.value.genre?.trim() || undefined,
    target_words: Number(newNovel.value.target_words),
    synopsis: newNovel.value.synopsis?.trim() || undefined,
  }

  if (!payload.title) {
    formError.value = '小说标题不能为空'
    return
  }

  if (!payload.target_words || payload.target_words <= 0) {
    formError.value = '目标字数必须大于 0'
    return
  }

  submitting.value = true

  try {
    await novelStore.createNovel(payload)
    showCreateDialog.value = false
    newNovel.value = createDefaultNovel()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '创建失败')
  } finally {
    submitting.value = false
  }
}

const deleteNovel = async (id: number) => {
  const novel = novels.value.find((item) => item.id === id)
  const confirmed = window.confirm(`确定要删除《${novel?.title || '这本小说'}》吗？此操作不可恢复。`)

  if (!confirmed) return

  errorMessage.value = ''

  try {
    await novelStore.deleteNovel(id)
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '删除失败')
  }
}

const getProgressPercent = (novel: Novel) => {
  if (!novel.target_words || novel.target_words <= 0) return 0
  return Math.min(100, Math.round((novel.current_words / novel.target_words) * 100))
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

const getTitleInitial = (title: string) => title.trim().charAt(0) || '书'

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
.bookshelf {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.header h1 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
}

.subtitle {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) repeat(3, minmax(130px, 160px)) auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}

.search-input,
.toolbar-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 14px;
  background: var(--card-bg);
}

.btn-primary {
  background: var(--success-color);
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.btn-primary:hover:not(:disabled) {
  background: color-mix(in srgb, var(--success-color) 84%, var(--text-primary));
}

.btn-secondary {
  background: var(--disabled-bg);
  color: var(--text-primary);
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
}

.btn-secondary:hover:not(:disabled) {
  background: var(--hover-bg);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.error-message {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.loading,
.empty-state {
  text-align: center;
  padding: 70px 20px;
  color: var(--text-secondary);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
}

.empty-state h2 {
  margin: 0 0 10px;
  color: var(--text-primary);
}

.empty-state p {
  margin: 0 0 22px;
}

.novel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.novel-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.novel-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-soft);
}

.cover {
  position: relative;
  width: 100%;
  height: 180px;
  background: linear-gradient(135deg, var(--panel-bg-soft), var(--success-bg));
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  font-size: 48px;
  color: var(--text-muted);
  font-weight: bold;
}

.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 10px;
  color: white;
  background: color-mix(in srgb, var(--info-color) 90%, transparent);
  border-radius: 999px;
  font-size: 12px;
}

.info {
  padding: 16px;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.info h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--text-primary);
  line-height: 1.4;
}

.btn-delete {
  flex-shrink: 0;
  padding: 4px 8px;
  color: var(--danger-color);
  background: var(--card-bg);
  border: 1px solid var(--danger-border);
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-delete:hover {
  background: var(--danger-bg);
}

.author {
  margin: 5px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.genre {
  display: inline-block;
  margin: 6px 0;
  padding: 3px 8px;
  color: var(--success-color);
  background: var(--success-bg);
  border-radius: 999px;
  font-size: 13px;
}

.synopsis {
  min-height: 40px;
  margin: 8px 0 12px;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.progress {
  margin-top: 12px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--disabled-bg);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--success-color);
  transition: width 0.3s;
}

.progress-text {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: var(--text-secondary);
}

.updated-at {
  margin: 12px 0 0;
  color: var(--text-muted);
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
  width: 500px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog h2 {
  margin: 0 0 20px;
  font-size: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-error {
  margin-bottom: 16px;
  padding: 10px 12px;
  color: var(--danger-color);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: 5px;
  font-size: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
}

@media (max-width: 900px) {
  .header {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
