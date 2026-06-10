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
      <div class="inspiration-card" @click="openInspirationMode">
        <div class="inspiration-icon">✨</div>
        <h3>灵感模式</h3>
        <p>AI 对话引导创作</p>
      </div>
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

    <div v-if="showInspirationDialog" class="dialog-overlay" @click.self="closeInspirationDialog">
      <div class="inspiration-dialog">
        <div class="dialog-title-bar">
          <h2>✨ 灵感模式</h2>
          <button class="btn-close" @click="closeInspirationDialog">×</button>
        </div>
        <div class="dialog-header">
          <input
            v-model="conversationTitle"
            type="text"
            class="conversation-title-input"
            placeholder="对话标题"
          />
          <div class="header-buttons">
            <button class="btn-secondary" @click="openConversationList">
              对话历史
            </button>
            <button class="btn-create-novel" :disabled="isGenerating" @click="generateFromConversation">
              创建小说
            </button>
          </div>
        </div>
        <div ref="chatContainer" class="chat-container">
          <div v-for="(msg, index) in inspirationMessages" :key="index" class="chat-message" :class="msg.role">
            <div class="message-content">
              <div v-if="isGenerating && index === inspirationMessages.length - 1 && msg.content === ''" class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <div v-else v-html="formatMessageContent(msg.content)"></div>
            </div>
            <div class="message-footer">
              <span class="message-time">{{ formatMessageTime(msg.timestamp || new Date()) }}</span>
              <div class="message-actions">
                <button class="action-btn" @click="copyMessage(msg.content)" title="复制">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </button>
                <template v-if="msg.role === 'user'">
                  <button class="action-btn" @click="editMessage(index)" title="编辑">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                  <button class="action-btn" @click="resendMessage(index)" title="重新发送">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"></path>
                    </svg>
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
        <div class="chat-input-area">
          <textarea
            v-model="userInput"
            placeholder="输入你的想法..."
            :disabled="isGenerating"
            rows="3"
            @keydown.enter.exact.prevent="sendMessage"
          ></textarea>
          <button :disabled="isGenerating || !userInput.trim()" @click="sendMessage">
            {{ isGenerating ? '生成中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showConversationListDialog" class="dialog-overlay" @click.self="showConversationListDialog = false">
      <div class="dialog conversation-list-dialog">
        <h2>对话历史</h2>
        <div v-if="conversationList.length === 0" class="empty-state">
          <p>暂无对话历史</p>
        </div>
        <div v-else class="conversation-list">
          <div
            v-for="conv in conversationList"
            :key="conv.id"
            class="conversation-item"
            @click="loadConversation(conv.id)"
          >
            <div class="conversation-info">
              <h3>{{ conv.title }}</h3>
              <p>{{ formatDate(conv.updated_at) }}</p>
            </div>
            <button class="btn-delete" @click.stop="deleteConversation(conv.id)">
              删除
            </button>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-secondary" @click="showConversationListDialog = false">
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
  <ConfirmDialog ref="confirmDialog" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useNovelStore } from '../stores/novel'
import type { Novel, NovelCreate } from '../types'
import ConfirmDialog from '../components/ConfirmDialog.vue'

type SortBy = 'updated_desc' | 'created_desc' | 'title_asc' | 'progress_desc'

const router = useRouter()
const novelStore = useNovelStore()
const { novels, loading } = storeToRefs(novelStore)
const confirmDialog = ref<InstanceType<typeof ConfirmDialog>>()

const showCreateDialog = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const formError = ref('')
const searchKeyword = ref('')
const statusFilter = ref('all')
const genreFilter = ref('all')
const sortBy = ref<SortBy>('updated_desc')
const newNovel = ref<NovelCreate>(createDefaultNovel())

const showInspirationDialog = ref(false)
const showConversationListDialog = ref(false)
const inspirationStep = ref(0)
const inspirationMessages = ref<Array<{ role: 'ai' | 'user'; content: string; timestamp?: Date | string }>>([])
const userInput = ref('')
const isGenerating = ref(false)
const chatContainer = ref<HTMLDivElement | null>(null)
const conversationTitle = ref('')
const currentConversationId = ref<number | null>(null)
const conversationList = ref<Array<{ id: number; title: string; updated_at: string }>>([])
const inspirationData = ref({
  title: '',
  synopsis: '',
  style_prompt: '',
  genre: '',
})

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
  const confirmed = await confirmDialog.value?.show({
    title: '删除小说',
    message: `确定要删除《${novel?.title || '这本小说'}》吗？此操作不可恢复。`,
    confirmText: '删除',
    type: 'danger'
  })

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

const openInspirationMode = () => {
  showInspirationDialog.value = true
  inspirationStep.value = 0
  conversationTitle.value = '新对话'
  currentConversationId.value = null
  inspirationMessages.value = [
    {
      role: 'ai',
      content: '你好！我是你的小说创作助手。\n\n我可以帮你：梳理故事创意、生成剧情大纲、设计角色人物、创作章节内容、提供写作建议等。\n\n告诉我你的想法，我们一起创作吧！',
      timestamp: new Date()
    }
  ]
  userInput.value = ''
  inspirationData.value = { title: '', synopsis: '', style_prompt: '', genre: '' }
}

const formatMessageTime = (timestamp: Date | string) => {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${month}/${day} ${hours}:${minutes}:${seconds}`
}

const formatMessageContent = (content: string) => {
  return content.replace(/\n/g, '<br>')
}

const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content).then(() => {
    console.log('已复制到剪贴板')
  })
}

const editMessage = (index: number) => {
  const msg = inspirationMessages.value[index]
  if (msg.role === 'user') {
    userInput.value = msg.content
    inspirationMessages.value = inspirationMessages.value.slice(0, index)
  }
}

const resendMessage = async (index: number) => {
  const msg = inspirationMessages.value[index]
  if (msg.role === 'user') {
    inspirationMessages.value = inspirationMessages.value.slice(0, index)
    userInput.value = msg.content
    await sendMessage()
  }
}

const openConversationList = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/conversations')
    conversationList.value = await response.json()
    showConversationListDialog.value = true
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加载对话列表失败')
  }
}

const loadConversation = async (conversationId: number) => {
  try {
    const response = await fetch(`http://localhost:8000/api/conversations/${conversationId}`)
    const data = await response.json()

    conversationTitle.value = data.title
    currentConversationId.value = data.id
    inspirationMessages.value = data.messages
    showConversationListDialog.value = false
    showInspirationDialog.value = true
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加载对话失败')
  }
}

const deleteConversation = async (conversationId: number) => {
  const confirmed = await confirmDialog.value?.show({
    title: '删除对话',
    message: '确定要删除这个对话吗？',
    confirmText: '删除',
    type: 'danger'
  })

  if (!confirmed) return

  try {
    await fetch(`http://localhost:8000/api/conversations/${conversationId}`, {
      method: 'DELETE'
    })
    conversationList.value = conversationList.value.filter(c => c.id !== conversationId)
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '删除对话失败')
  }
}

const saveConversation = async () => {
  try {
    if (currentConversationId.value) {
      await fetch(`http://localhost:8000/api/conversations/${currentConversationId.value}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: conversationTitle.value,
          messages: inspirationMessages.value
        })
      })
    } else {
      const response = await fetch('http://localhost:8000/api/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: conversationTitle.value,
          messages: inspirationMessages.value
        })
      })
      const data = await response.json()
      currentConversationId.value = data.id
    }
  } catch (error) {
    console.error('保存对话失败:', error)
  }
}

const closeInspirationDialog = () => {
  if (isGenerating.value) return
  showInspirationDialog.value = false
}

const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || isGenerating.value) return

  inspirationMessages.value.push({ role: 'user', content: message, timestamp: new Date() })
  userInput.value = ''
  isGenerating.value = true

  setTimeout(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }, 50)

  try {
    const messagesForApi = inspirationMessages.value.map(m => ({
      role: m.role === 'ai' ? 'assistant' : 'user',
      content: m.content
    }))

    const response = await fetch('http://localhost:8000/api/ai/inspiration-chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: messagesForApi })
    })

    let aiReply = ''
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    inspirationMessages.value.push({ role: 'ai', content: '', timestamp: new Date() })
    const aiMsgIndex = inspirationMessages.value.length - 1

    if (reader) {
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
              aiReply += event.content
              inspirationMessages.value[aiMsgIndex].content = aiReply
              setTimeout(() => {
                if (chatContainer.value) {
                  chatContainer.value.scrollTop = chatContainer.value.scrollHeight
                }
              }, 10)
            }
          }
        }
      }
    }

    await saveConversation()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '对话失败')
    inspirationMessages.value.push({ role: 'ai', content: `对话失败：${errorMessage.value}`, timestamp: new Date() })
  } finally {
    isGenerating.value = false
  }

  setTimeout(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }, 50)
}

const generateFromConversation = async () => {
  isGenerating.value = true

  const conversationText = inspirationMessages.value
    .map(m => `${m.role === 'user' ? '用户' : 'AI'}：${m.content}`)
    .join('\n\n')

  const genreMatch = conversationText.match(/(玄幻|都市|科幻|言情|历史|武侠|仙侠|奇幻|军事|游戏|悬疑|推理)/i)
  const genre = genreMatch ? genreMatch[1] : '未分类'
  inspirationData.value.genre = genre

  try {
    const decoder = new TextDecoder()

    inspirationMessages.value.push({ role: 'ai', content: '正在生成小说标题...', timestamp: new Date() })
    const titleResponse = await fetch('http://localhost:8000/api/ai/generate-title-from-conversation/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation: conversationText, genre })
    })

    let title = ''
    const titleReader = titleResponse.body?.getReader()
    if (titleReader) {
      let buffer = ''
      while (true) {
        const { done, value } = await titleReader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'chunk') {
              title += event.content
              inspirationMessages.value[inspirationMessages.value.length - 1].content = `正在生成小说标题...\n\n${title}`
            }
          }
        }
      }
    }
    inspirationData.value.title = title.trim()
    inspirationMessages.value[inspirationMessages.value.length - 1].content = `✓ 标题：${title.trim()}`

    inspirationMessages.value.push({ role: 'ai', content: '正在生成小说简介...', timestamp: new Date() })
    const synopsisResponse = await fetch('http://localhost:8000/api/ai/generate-synopsis-from-conversation/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: inspirationData.value.title, genre, conversation: conversationText })
    })

    let synopsis = ''
    const synopsisReader = synopsisResponse.body?.getReader()
    if (synopsisReader) {
      let buffer = ''
      while (true) {
        const { done, value } = await synopsisReader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'chunk') {
              synopsis += event.content
              inspirationMessages.value[inspirationMessages.value.length - 1].content = `正在生成小说简介...\n\n${synopsis}`
            }
          }
        }
      }
    }
    inspirationData.value.synopsis = synopsis.trim()
    inspirationMessages.value[inspirationMessages.value.length - 1].content = `✓ 简介：\n${synopsis.trim()}`

    inspirationMessages.value.push({ role: 'ai', content: '正在生成风格提示词...', timestamp: new Date() })
    const styleResponse = await fetch('http://localhost:8000/api/ai/generate-style-prompt-from-conversation/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: inspirationData.value.title, genre, synopsis: inspirationData.value.synopsis, conversation: conversationText })
    })

    let stylePrompt = ''
    const styleReader = styleResponse.body?.getReader()
    if (styleReader) {
      let buffer = ''
      while (true) {
        const { done, value } = await styleReader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6))
            if (event.type === 'chunk') {
              stylePrompt += event.content
              inspirationMessages.value[inspirationMessages.value.length - 1].content = `正在生成风格提示词...\n\n${stylePrompt}`
            }
          }
        }
      }
    }
    inspirationData.value.style_prompt = stylePrompt.trim()
    inspirationMessages.value[inspirationMessages.value.length - 1].content = `✓ 风格提示词：\n${stylePrompt.trim()}`

    await createNovelFromInspiration()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '生成失败')
    inspirationMessages.value.push({ role: 'ai', content: `生成失败：${errorMessage.value}`, timestamp: new Date() })
  } finally {
    isGenerating.value = false
  }
}

const createNovelFromInspiration = async () => {
  try {
    const payload = {
      title: inspirationData.value.title,
      genre: inspirationData.value.genre,
      synopsis: inspirationData.value.synopsis,
      style_prompt: inspirationData.value.style_prompt,
      author: '默认作者',
      target_words: 1000000
    }

    await novelStore.createNovel(payload)
    const newNovel = novels.value[0]

    if (newNovel) {
      const conversationText = inspirationMessages.value
        .map(m => `${m.role === 'user' ? '用户' : 'AI'}：${m.content}`)
        .join('\n\n')

      inspirationMessages.value.push({ role: 'ai', content: '正在生成剧情大纲...', timestamp: new Date() })

      const outlineResponse = await fetch('http://localhost:8000/api/ai/generate-outline-from-conversation/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ novel_id: newNovel.id, conversation: conversationText })
      })

      let outline = ''
      const decoder = new TextDecoder()
      const outlineReader = outlineResponse.body?.getReader()
      if (outlineReader) {
        let buffer = ''
        while (true) {
          const { done, value } = await outlineReader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'chunk') {
                outline += event.content
                inspirationMessages.value[inspirationMessages.value.length - 1].content = `正在生成剧情大纲...\n\n${outline}`
              }
            }
          }
        }
      }

      inspirationMessages.value[inspirationMessages.value.length - 1].content = '✓ 剧情大纲已生成'
      inspirationMessages.value.push({ role: 'ai', content: '🎉 小说创建成功！正在跳转到工作区...', timestamp: new Date() })

      setTimeout(() => {
        router.push(`/novel/${newNovel.id}`)
        showInspirationDialog.value = false
      }, 1500)
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '创建小说失败')
    inspirationMessages.value.push({ role: 'ai', content: `创建失败：${errorMessage.value}`, timestamp: new Date() })
  }
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

.inspiration-card {
  background: linear-gradient(135deg, var(--success-bg), var(--info-bg));
  border: 2px dashed var(--success-color);
  border-radius: 10px;
  padding: 40px 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.inspiration-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-soft);
}

.inspiration-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.inspiration-card h3 {
  margin: 0 0 8px;
  font-size: 20px;
  color: var(--text-primary);
}

.inspiration-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
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

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 25px;
}

.inspiration-dialog {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 0;
  width: 60%;
  max-width: 90%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.dialog-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
}

.dialog-title-bar h2 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.btn-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 28px;
  color: var(--text-secondary);
  line-height: 1;
  padding: 0;
}

.btn-close:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}

.dialog-header h2 {
  margin: 0;
  font-size: 24px;
}

.conversation-title-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  background: var(--card-bg);
  color: var(--text-primary);
}

.header-buttons {
  display: flex;
  gap: 8px;
}

.btn-create-novel {
  padding: 8px 20px;
  background: var(--success-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-create-novel:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-create-novel:hover:not(:disabled) {
  background: color-mix(in srgb, var(--success-color) 84%, var(--text-primary));
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  background: var(--panel-bg-soft);
  min-height: 600px;
}

.chat-message {
  margin-bottom: 20px;
  padding: 12px 16px;
  border-radius: 12px;
  max-width: 75%;
  white-space: pre-wrap;
  word-wrap: break-word;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.chat-message.ai {
  background: var(--info-bg);
  border: 1px solid var(--info-border);
  margin-right: auto;
}

.chat-message.user {
  background: var(--success-bg);
  border: 1px solid var(--success-border);
  margin-left: auto;
}

.message-content {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--text-secondary);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-muted);
}

.chat-message.user .message-footer {
  flex-direction: row-reverse;
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-message:hover .message-actions {
  opacity: 1;
}

.action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.action-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.action-btn svg {
  display: block;
}

.chat-input-area {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--card-bg);
}

.chat-input-area textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--card-bg);
  resize: vertical;
  min-height: 60px;
  max-height: 150px;
  font-family: inherit;
}

.chat-input-area input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background: var(--card-bg);
}

.chat-input-area button {
  padding: 10px 24px;
  background: var(--success-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.chat-input-area button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input-area button:hover:not(:disabled) {
  background: color-mix(in srgb, var(--success-color) 84%, var(--text-primary));
}

.conversation-list-dialog {
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.conversation-list {
  margin-bottom: 20px;
}

.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: var(--hover-bg);
}

.conversation-info {
  flex: 1;
}

.conversation-info h3 {
  margin: 0 0 4px;
  font-size: 16px;
  color: var(--text-primary);
}

.conversation-info p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
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
