<template>
  <div class="tab-content">
    <div class="tab-header">
      <h2>剧情大纲</h2>
      <div class="outline-actions">
        <button class="btn-secondary" :disabled="isLoadingOutlines || isGenerating" @click="loadOutlines">
          {{ isLoadingOutlines ? '刷新中...' : '刷新大纲' }}
        </button>
        <button class="btn-secondary" :disabled="isGenerating" @click="openOutlineDialog()">新增大纲项</button>
        <button class="btn-primary" :disabled="isGenerating" @click="showPlanDialog = true">一键规划大纲</button>
      </div>
    </div>

    <div v-if="outlineError" class="error-message">
      <span>{{ outlineError }}</span>
      <button type="button" @click="outlineError = ''">关闭</button>
    </div>

    <div v-if="isGenerating" class="generating">
      <div class="generating-content">
        <div class="spinner"></div>
        <div class="streaming-text">{{ streamedContent }}<span class="cursor">▌</span></div>
      </div>
    </div>

    <div v-else-if="isLoadingOutlines" class="loading">大纲加载中...</div>

    <div v-else class="outline-content">
      <div v-if="outlines.length === 0 && !generatedOutlineText" class="empty-state">
        <h3>暂无剧情大纲</h3>
        <p>可以手动新增大纲项，或使用一键规划生成卷级大纲。</p>
        <div class="empty-actions">
          <button class="btn-secondary" @click="openOutlineDialog()">新增大纲项</button>
          <button class="btn-primary" @click="showPlanDialog = true">一键规划大纲</button>
        </div>
      </div>

      <div v-else class="outline-list">
        <div v-if="outlines.length === 0 && generatedOutlineText" class="generated-outline">
          <h3>生成结果</h3>
          <div class="streaming-text">{{ generatedOutlineText }}</div>
        </div>

        <div v-for="outline in outlines" :key="outline.id" class="outline-item">
          <div class="outline-item-header">
            <div>
              <div class="outline-meta">
                <span>{{ getOutlineTypeLabel(outline.outline_type) }}</span>
                <span v-if="outline.volume_number">第 {{ outline.volume_number }} 卷</span>
                <span v-if="outline.chapter_number">第 {{ outline.chapter_number }} 章</span>
              </div>
              <h3>{{ outline.title }}</h3>
            </div>
            <div class="outline-item-actions">
              <button class="btn-text" type="button" @click="openOutlineDialog(outline)">编辑</button>
              <button class="btn-text danger" type="button" @click="deleteOutline(outline)">删除</button>
            </div>
          </div>
          <p class="outline-summary">{{ outline.plot_summary || '暂无情节梗概' }}</p>
          <div v-if="outline.key_events || outline.characters_involved" class="outline-detail-grid">
            <div v-if="outline.key_events" class="outline-detail">
              <label>关键事件</label>
              <p>{{ outline.key_events }}</p>
            </div>
            <div v-if="outline.characters_involved" class="outline-detail">
              <label>涉及角色</label>
              <p>{{ outline.characters_involved }}</p>
            </div>
          </div>
          <p class="updated-at">更新于 {{ formatDate(outline.updated_at) }}</p>
        </div>
      </div>
    </div>

    <div v-if="showPlanDialog" class="dialog-overlay" @click.self="showPlanDialog = false">
      <div class="dialog">
        <h2>一键规划小说大纲</h2>
        <form @submit.prevent="handlePlanNovel">
          <div class="form-group">
            <label>目标字数</label>
            <input v-model.number="planRequest.target_words" type="number" min="1" required :disabled="isGenerating" />
          </div>
          <div class="form-group">
            <label>目标章节数</label>
            <input v-model.number="planRequest.target_chapters" type="number" min="1" required :disabled="isGenerating" />
          </div>
          <div class="form-group">
            <label>目标卷数</label>
            <input v-model.number="planRequest.target_volumes" type="number" min="1" required :disabled="isGenerating" />
          </div>
          <div class="form-group">
            <label>风格要求（可选）</label>
            <textarea v-model="planRequest.style_requirements" rows="3" :disabled="isGenerating"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="isGenerating" @click="showPlanDialog = false">取消</button>
            <button type="submit" class="btn-primary" :disabled="isGenerating">
              {{ isGenerating ? '生成中...' : '开始生成' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showOutlineDialog" class="dialog-overlay" @click.self="closeOutlineDialog">
      <div class="dialog">
        <h2>{{ editingOutlineId ? '编辑大纲项' : '新增大纲项' }}</h2>
        <form @submit.prevent="saveOutline">
          <div v-if="outlineFormError" class="form-error">{{ outlineFormError }}</div>
          <div class="form-row">
            <div class="form-group">
              <label>标题</label>
              <input v-model="outlineForm.title" type="text" required :disabled="isSavingOutline" />
            </div>
            <div class="form-group">
              <label>类型</label>
              <select v-model="outlineForm.outline_type" :disabled="isSavingOutline">
                <option value="volume">卷</option>
                <option value="chapter">章节</option>
                <option value="scene">场景</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>卷号</label>
              <input v-model.number="outlineForm.volume_number" type="number" min="1" :disabled="isSavingOutline" />
            </div>
            <div class="form-group">
              <label>章节号</label>
              <input v-model.number="outlineForm.chapter_number" type="number" min="1" :disabled="isSavingOutline" />
            </div>
          </div>
          <div class="form-group">
            <label>情节梗概</label>
            <textarea v-model="outlineForm.plot_summary" rows="4" :disabled="isSavingOutline"></textarea>
          </div>
          <div class="form-group">
            <label>关键事件</label>
            <textarea v-model="outlineForm.key_events" rows="3" :disabled="isSavingOutline"></textarea>
          </div>
          <div class="form-group">
            <label>涉及角色</label>
            <textarea v-model="outlineForm.characters_involved" rows="3" :disabled="isSavingOutline"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="isSavingOutline" @click="closeOutlineDialog">取消</button>
            <button type="submit" class="btn-primary" :disabled="isSavingOutline">
              {{ isSavingOutline ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { aiApi, outlineApi } from '../../api'
import type { Outline, OutlineCreate, OutlineUpdate } from '../../types'

const props = defineProps<{
  novelId: number
}>()

type OutlineForm = {
  title: string
  outline_type: string
  volume_number: number | ''
  chapter_number: number | ''
  plot_summary: string
  key_events: string
  characters_involved: string
}

const showPlanDialog = ref(false)
const showOutlineDialog = ref(false)
const isGenerating = ref(false)
const isLoadingOutlines = ref(false)
const isSavingOutline = ref(false)
const editingOutlineId = ref<number | null>(null)
const outlineError = ref('')
const outlineFormError = ref('')
const streamedContent = ref('')
const generatedOutlineText = ref('')
const outlines = ref<Outline[]>([])
const outlineForm = ref<OutlineForm>(createOutlineForm())
const planRequest = ref({
  target_words: 1000000,
  target_chapters: 200,
  target_volumes: 5,
  style_requirements: '',
})

onMounted(() => {
  void loadOutlines()
})

function createOutlineForm(): OutlineForm {
  return {
    title: '',
    outline_type: 'chapter',
    volume_number: '',
    chapter_number: '',
    plot_summary: '',
    key_events: '',
    characters_involved: '',
  }
}

const loadOutlines = async () => {
  outlineError.value = ''
  isLoadingOutlines.value = true

  try {
    const response = await outlineApi.listByNovel(props.novelId)
    outlines.value = response.data
  } catch (error) {
    outlineError.value = getErrorMessage(error, '加载大纲失败')
  } finally {
    isLoadingOutlines.value = false
  }
}

const openOutlineDialog = (outline?: Outline) => {
  outlineFormError.value = ''
  outlineError.value = ''

  if (outline) {
    editingOutlineId.value = outline.id
    outlineForm.value = {
      title: outline.title,
      outline_type: outline.outline_type || 'chapter',
      volume_number: outline.volume_number || '',
      chapter_number: outline.chapter_number || '',
      plot_summary: outline.plot_summary || '',
      key_events: outline.key_events || '',
      characters_involved: outline.characters_involved || '',
    }
  } else {
    editingOutlineId.value = null
    outlineForm.value = createOutlineForm()
  }

  showOutlineDialog.value = true
}

const closeOutlineDialog = () => {
  if (isSavingOutline.value) return
  showOutlineDialog.value = false
  editingOutlineId.value = null
  outlineFormError.value = ''
}

const saveOutline = async () => {
  outlineFormError.value = ''
  outlineError.value = ''

  const title = outlineForm.value.title.trim()
  if (!title) {
    outlineFormError.value = '大纲标题不能为空'
    return
  }

  const volumeNumber = normalizePositiveNumber(outlineForm.value.volume_number)
  const chapterNumber = normalizePositiveNumber(outlineForm.value.chapter_number)

  if (volumeNumber === 0 || chapterNumber === 0) {
    outlineFormError.value = '卷号和章节号必须大于 0 或留空'
    return
  }

  const payload: OutlineUpdate = {
    title,
    outline_type: outlineForm.value.outline_type,
    volume_number: volumeNumber || undefined,
    chapter_number: chapterNumber || undefined,
    plot_summary: outlineForm.value.plot_summary.trim() || undefined,
    key_events: outlineForm.value.key_events.trim() || undefined,
    characters_involved: outlineForm.value.characters_involved.trim() || undefined,
  }

  isSavingOutline.value = true

  try {
    if (editingOutlineId.value) {
      await outlineApi.update(editingOutlineId.value, payload)
    } else {
      await outlineApi.create({
        ...payload,
        novel_id: props.novelId,
        title,
      } as OutlineCreate)
    }

    await loadOutlines()
    closeOutlineDialog()
  } catch (error) {
    outlineFormError.value = getErrorMessage(error, '保存大纲失败')
  } finally {
    isSavingOutline.value = false
  }
}

const deleteOutline = async (outline: Outline) => {
  const confirmed = window.confirm(`确定要删除大纲项《${outline.title}》吗？此操作不可恢复。`)
  if (!confirmed) return

  outlineError.value = ''

  try {
    await outlineApi.delete(outline.id)
    await loadOutlines()
  } catch (error) {
    outlineError.value = getErrorMessage(error, '删除大纲失败')
  }
}

const handlePlanNovel = async () => {
  outlineError.value = ''

  if (!planRequest.value.target_words || planRequest.value.target_words <= 0) {
    outlineError.value = '目标字数必须大于 0'
    return
  }

  if (!planRequest.value.target_chapters || planRequest.value.target_chapters <= 0) {
    outlineError.value = '目标章节数必须大于 0'
    return
  }

  if (!planRequest.value.target_volumes || planRequest.value.target_volumes <= 0) {
    outlineError.value = '目标卷数必须大于 0'
    return
  }

  showPlanDialog.value = false
  isGenerating.value = true
  streamedContent.value = ''
  generatedOutlineText.value = ''

  try {
    await aiApi.planNovelStream(
      {
        novel_id: props.novelId,
        ...planRequest.value,
      },
      (chunk) => {
        streamedContent.value += chunk
        generatedOutlineText.value += chunk
      },
      async () => {
        isGenerating.value = false
        await loadOutlines()
      },
      (error) => {
        isGenerating.value = false
        outlineError.value = `生成失败：${error}`
      }
    )
  } catch (error) {
    isGenerating.value = false
    outlineError.value = getErrorMessage(error, '生成失败')
  }
}

const normalizePositiveNumber = (value: number | '') => {
  if (value === '') return undefined
  const numberValue = Number(value)
  if (!Number.isInteger(numberValue) || numberValue <= 0) return 0
  return numberValue
}

const getOutlineTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    volume: '卷',
    chapter: '章节',
    scene: '场景',
  }

  return typeMap[type] || type || '大纲'
}

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
  min-height: 500px;
  padding: 30px;
  background: white;
  border-radius: 8px;
}

.tab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.outline-actions,
.empty-actions,
.outline-item-actions,
.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.outline-content,
.outline-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.empty-state {
  padding: 60px 20px;
  color: #666;
  text-align: center;
  background: #f8fafc;
  border: 1px solid #eee;
  border-radius: 8px;
}

.empty-state h3 {
  margin: 0 0 10px;
  color: #333;
}

.empty-actions {
  justify-content: center;
  margin-top: 20px;
}

.generated-outline,
.outline-item {
  padding: 18px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
}

.outline-item-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.outline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.outline-meta span {
  padding: 3px 8px;
  color: #2f7d32;
  background: #eef8ef;
  border-radius: 999px;
  font-size: 12px;
}

.outline-item h3,
.generated-outline h3 {
  margin: 0;
  color: #333;
}

.outline-summary {
  margin: 12px 0;
  color: #555;
  line-height: 1.7;
  white-space: pre-wrap;
}

.outline-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.outline-detail {
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.outline-detail label {
  display: block;
  margin-bottom: 6px;
  color: #777;
  font-size: 13px;
}

.outline-detail p {
  margin: 0;
  color: #555;
  line-height: 1.6;
  white-space: pre-wrap;
}

.updated-at {
  margin: 12px 0 0;
  color: #999;
  font-size: 12px;
}

.generating {
  padding: 30px;
  text-align: center;
}

.generating-content {
  max-width: 800px;
  margin: 0 auto;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.streaming-text {
  font-family: monospace;
  line-height: 1.6;
  text-align: left;
  white-space: pre-wrap;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.error-message,
.form-error {
  margin-bottom: 16px;
  padding: 10px 12px;
  color: #b42318;
  background: #fff1f0;
  border: 1px solid #ffccc7;
  border-radius: 5px;
}

.error-message {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.error-message button,
.btn-text {
  color: #3498db;
  background: transparent;
  border: none;
  cursor: pointer;
}

.btn-text.danger {
  color: #d93026;
}

.loading {
  padding: 50px;
  color: #666;
  text-align: center;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
}

.dialog {
  width: 500px;
  max-width: 90%;
  padding: 30px;
  background: white;
  border-radius: 8px;
}

.dialog h2 {
  margin: 0 0 20px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
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
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-sizing: border-box;
}

.form-actions {
  justify-content: flex-end;
  margin-top: 25px;
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
