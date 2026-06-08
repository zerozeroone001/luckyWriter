<template>
  <div class="tab-content">
    <div class="tab-header">
      <div>
        <p class="page-eyebrow">Novel Chapters</p>
        <h2>章节目录</h2>
      </div>
      <div class="chapter-actions">
        <button class="btn-secondary" :disabled="isLoadingChapters || isRunningChapterAi" @click="refreshChapterWorkspace">
          {{ isLoadingChapters ? '刷新中...' : '刷新目录' }}
        </button>
        <button class="btn-primary" :disabled="isSavingChapter || isRunningChapterAi" @click="openChapterDialog()">新建章节</button>
      </div>
    </div>

    <div v-if="chapterError" class="error-message">
      <span>{{ chapterError }}</span>
      <button @click="chapterError = ''">关闭</button>
    </div>

    <div v-if="isLoadingChapters || isLoadingOutlines" class="loading">章节目录加载中...</div>
    <div v-else-if="chapterOutlineRows.length > 0" class="chapter-outline-list">
      <div v-for="row in chapterOutlineRows" :key="row.key" class="chapter-outline-card">
        <div class="chapter-outline-index">
          <span>卷 {{ row.outline.volume_number || 1 }}</span>
          <strong>{{ row.outline.chapter_number }}</strong>
        </div>
        <div class="chapter-outline-main">
          <div class="chapter-title-row">
            <span class="chapter-number">{{ formatOutlinePosition(row.outline) }}</span>
            <span class="chapter-status" :class="{ empty: !row.chapter?.content }">{{ getChapterRowStatus(row) }}</span>
          </div>
          <h3>{{ row.outline.title }}</h3>
          <div class="outline-detail-grid compact">
            <div class="outline-detail primary-detail">
              <label>情节梗概</label>
              <p>{{ row.outline.plot_summary || '暂无' }}</p>
            </div>
            <div class="outline-detail">
              <label>关键事件</label>
              <p>{{ row.outline.key_events || '暂无' }}</p>
            </div>
            <div class="outline-detail">
              <label>涉及角色</label>
              <p>{{ row.outline.characters_involved || '暂无' }}</p>
            </div>
          </div>
          <div class="chapter-meta">
            <span>{{ row.chapter ? `${formatNumber(row.chapter.word_count)} 字` : '未添加正文' }}</span>
            <span v-if="row.chapter">更新于 {{ formatDate(row.chapter.updated_at) }}</span>
          </div>
        </div>
        <div class="chapter-ai-actions">
          <button class="ai-action-btn secondary" :disabled="isChapterAiDisabled(row)" @click="openChapterAiDialog(row, 'polish-outline')">剧情润色</button>
          <button class="ai-action-btn primary" :disabled="isChapterAiDisabled(row)" @click="openChapterAiDialog(row, 'generate-content')">AI 写作正文</button>
          <button class="ai-action-btn overwrite" :disabled="isChapterAiDisabled(row) || !row.chapter?.content" @click="openChapterAiDialog(row, 'rewrite-content')">AI 重写正文</button>
          <button class="ai-action-btn secondary" :disabled="isChapterAiDisabled(row) || !row.chapter?.content" @click="openChapterAiDialog(row, 'polish-content')">AI 润色正文</button>
          <div class="chapter-manual-actions">
            <button class="btn-text" :disabled="isRunningChapterAi" @click="row.chapter ? openChapterDialog(row.chapter) : openChapterDialogFromOutline(row.outline)">
              {{ row.chapter ? '编辑章节' : '添加章节' }}
            </button>
            <button class="btn-text" :disabled="!row.chapter || isRunningChapterAi" @click="row.chapter && selectChapter(row.chapter)">阅读正文</button>
            <button v-if="row.chapter" class="btn-text danger" :disabled="isRunningChapterAi" @click="deleteChapter(row.chapter)">删除正文</button>
          </div>
        </div>
      </div>
    </div>
    <div v-else-if="chapters.length > 0" class="chapters-list">
      <div class="empty-state compact-empty">
        <h3>暂无章节级大纲</h3>
        <p>当前显示已存在正文。建议先在剧情大纲中生成或新增章节大纲，再进行 AI 写作。</p>
      </div>
      <section v-for="group in chapterGroups" :key="group.volumeNumber" class="chapter-volume">
        <div class="chapter-volume-header">
          <h3>{{ group.title }}</h3>
          <span>{{ group.chapters.length }} 章</span>
        </div>
        <div v-for="chapter in group.chapters" :key="chapter.id" class="chapter-item" @click="selectChapter(chapter)">
          <div class="chapter-main">
            <div class="chapter-title-row">
              <span class="chapter-number">{{ formatChapterPosition(chapter) }}</span>
              <span class="chapter-status">{{ getChapterStatusLabel(chapter.status) }}</span>
            </div>
            <h3>{{ chapter.title }}</h3>
            <p class="chapter-preview">{{ getChapterPreview(chapter) }}</p>
            <div class="chapter-meta">
              <span>{{ formatNumber(chapter.word_count) }} 字</span>
              <span>更新于 {{ formatDate(chapter.updated_at) }}</span>
            </div>
          </div>
          <div class="chapter-item-actions" @click.stop>
            <button class="btn-text" @click="selectChapter(chapter)">阅读正文</button>
            <button class="btn-text" @click="openChapterDialog(chapter)">编辑</button>
            <button class="btn-text danger" @click="deleteChapter(chapter)">删除</button>
          </div>
        </div>
      </section>
    </div>
    <div v-else class="empty-state">
      <h3>暂无章节目录</h3>
      <p>请先生成或新增章节大纲，也可以手动创建章节。</p>
      <div class="empty-actions">
        <button class="btn-primary" @click="openChapterDialog()">新建章节</button>
      </div>
    </div>

    <div v-if="showChapterDialog" class="dialog-overlay" @click.self="closeChapterDialog">
      <div class="dialog chapter-form-dialog">
        <h2>{{ editingChapterId ? '编辑章节' : '新建章节' }}</h2>
        <form @submit.prevent="saveChapter">
          <div v-if="chapterFormError" class="form-error">{{ chapterFormError }}</div>
          <div class="form-row">
            <div class="form-group">
              <label>卷号</label>
              <input v-model.number="chapterForm.volume_number" type="number" min="1" :disabled="isSavingChapter || Boolean(editingChapterId)" />
            </div>
            <div class="form-group">
              <label>章节号</label>
              <input v-model.number="chapterForm.chapter_number" type="number" min="1" required :disabled="isSavingChapter || Boolean(editingChapterId)" />
            </div>
          </div>
          <div class="form-group">
            <label>章节标题</label>
            <input v-model="chapterForm.title" type="text" required :disabled="isSavingChapter" />
          </div>
          <div v-if="editingChapterId" class="form-group">
            <label>状态</label>
            <select v-model="chapterForm.status" :disabled="isSavingChapter">
              <option value="draft">草稿</option>
              <option value="published">已发布</option>
            </select>
          </div>
          <div class="form-group">
            <label>正文内容</label>
            <textarea v-model="chapterForm.content" rows="12" :disabled="isSavingChapter"></textarea>
          </div>
          <p v-if="editingChapterId" class="form-hint">卷号和章节号当前由创建接口确定，编辑时仅修改标题、正文和状态。</p>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="isSavingChapter" @click="closeChapterDialog">取消</button>
            <button type="submit" class="btn-primary" :disabled="isSavingChapter">
              {{ isSavingChapter ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showChapterDetail && selectedChapter" class="dialog-overlay" @click.self="closeChapterDetail">
      <div class="dialog chapter-detail-dialog">
        <div class="dialog-title-row">
          <h2>{{ selectedChapter.title }}</h2>
          <span class="chapter-status">{{ getChapterStatusLabel(selectedChapter.status) }}</span>
        </div>
        <div class="chapter-detail-meta">
          <span>{{ formatChapterPosition(selectedChapter) }}</span>
          <span>{{ formatNumber(selectedChapter.word_count) }} 字</span>
          <span>创建于 {{ formatDate(selectedChapter.created_at) }}</span>
          <span>更新于 {{ formatDate(selectedChapter.updated_at) }}</span>
        </div>
        <div
          ref="chapterContentRef"
          class="chapter-content-full"
          tabindex="0"
          v-text="selectedChapter.content || '暂无正文'"
          @mouseup="handleChapterTextSelection"
          @keyup="handleChapterTextSelection"
        ></div>
        <button
          v-if="selectionSnapshot && !showSelectionRewriteDialog"
          type="button"
          class="selection-edit-button"
          :style="{ left: `${selectionSnapshot.buttonX}px`, top: `${selectionSnapshot.buttonY}px` }"
          @mousedown.prevent
          @click="openSelectionRewriteDialog"
        >
          编辑
        </button>
        <div class="form-actions">
          <button type="button" class="btn-secondary" @click="openChapterDialog(selectedChapter)">编辑</button>
          <button type="button" class="btn-text danger" @click="deleteChapter(selectedChapter)">删除</button>
          <button type="button" class="btn-primary" @click="closeChapterDetail">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showChapterAiDialog && activeChapterAiRow && runningChapterAiAction" class="dialog-overlay" @click.self="closeChapterAiDialog">
      <div class="dialog chapter-ai-dialog">
        <div class="dialog-title-row">
          <div>
            <p class="page-eyebrow">AI Preview</p>
            <h2>{{ chapterAiActionLabels[runningChapterAiAction] }}</h2>
          </div>
          <span class="chapter-status">{{ formatOutlinePosition(activeChapterAiRow.outline) }}</span>
        </div>

        <div class="ai-context-card">
          <h3>{{ activeChapterAiRow.outline.title }}</h3>
          <p>{{ activeChapterAiRow.outline.plot_summary || '暂无情节梗概' }}</p>
        </div>

        <div v-if="chapterAiError" class="form-error">{{ chapterAiError }}</div>

        <div class="form-group">
          <label>修改建议</label>
          <textarea
            v-model="chapterAiRequirements"
            rows="4"
            :placeholder="getChapterAiRequirementPlaceholder(runningChapterAiAction)"
            :disabled="isRunningChapterAi || isSavingChapterAiResult"
          ></textarea>
        </div>

        <div class="ai-preview-panel" :class="{ empty: !streamedContent }">
          <div class="ai-preview-header">
            <strong>生成内容预览</strong>
            <span v-if="isRunningChapterAi">生成中...</span>
            <span v-else-if="streamedContent">等待确认保存</span>
            <span v-else>尚未生成</span>
          </div>
          <div class="streaming-text preview-text">
            {{ streamedContent || '输入修改建议后点击“开始生成”，内容会在这里实时回显。' }}<span v-if="isRunningChapterAi" class="cursor">▌</span>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-secondary" :disabled="isRunningChapterAi || isSavingChapterAiResult" @click="closeChapterAiDialog">取消</button>
          <button type="button" class="btn-secondary" :disabled="isRunningChapterAi || isSavingChapterAiResult" @click="generateChapterAiPreview">
            {{ streamedContent ? '重新生成' : '开始生成' }}
          </button>
          <button type="button" class="btn-primary" :disabled="!canSaveChapterAiResult || isSavingChapterAiResult" @click="saveChapterAiResult">
            {{ isSavingChapterAiResult ? '保存中...' : '确认保存' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSelectionRewriteDialog && selectionRewriteSnapshot" class="dialog-overlay" @click.self="closeSelectionRewriteDialog">
      <div class="dialog selection-rewrite-dialog">
        <div class="dialog-title-row">
          <div>
            <p class="page-eyebrow">Selection Rewrite</p>
            <h2>局部改写正文</h2>
          </div>
          <span class="chapter-status">{{ selectedChapter ? formatChapterPosition(selectedChapter) : '当前选区' }}</span>
        </div>

        <div v-if="selectionRewriteError" class="form-error">{{ selectionRewriteError }}</div>

        <div class="form-group">
          <label>原选中文本</label>
          <div class="selected-text-preview">{{ selectionRewriteSnapshot.selectedText }}</div>
        </div>

        <div class="form-group">
          <label>修改意见</label>
          <textarea
            v-model="selectionRewriteRequirements"
            rows="4"
            placeholder="例如：增强人物情绪，减少说明性文字，让动作更有画面感。"
            :disabled="isGeneratingSelectionRewrite || isSavingSelectionRewrite"
          ></textarea>
        </div>

        <div class="ai-preview-panel selection-preview-panel" :class="{ empty: !selectionRewriteContent }">
          <div class="ai-preview-header">
            <strong>替换内容预览</strong>
            <span v-if="isGeneratingSelectionRewrite">生成中...</span>
            <span v-else-if="selectionRewriteContent">等待确认替换</span>
            <span v-else>尚未生成</span>
          </div>
          <div class="streaming-text preview-text">
            {{ selectionRewriteContent || '点击“开始生成”后，AI 生成的替换片段会在这里实时回显。' }}<span v-if="isGeneratingSelectionRewrite" class="cursor">▌</span>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-secondary" :disabled="isGeneratingSelectionRewrite || isSavingSelectionRewrite" @click="closeSelectionRewriteDialog">取消</button>
          <button type="button" class="btn-secondary" :disabled="isGeneratingSelectionRewrite || isSavingSelectionRewrite" @click="generateSelectionRewritePreview">
            {{ selectionRewriteContent ? '重新生成' : '开始生成' }}
          </button>
          <button type="button" class="btn-primary" :disabled="!canConfirmSelectionRewrite || isSavingSelectionRewrite" @click="confirmSelectionRewrite">
            {{ isSavingSelectionRewrite ? '替换中...' : '确认替换' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { aiApi, chapterApi, outlineApi } from '../../api'
import type { Chapter, ChapterCreate, ChapterUpdate, Outline, OutlineUpdate } from '../../types'

const props = defineProps<{
  novelId: number
}>()

type ChapterForm = {
  title: string
  volume_number: number | ''
  chapter_number: number | ''
  status: string
  content: string
}

type ChapterGroup = {
  volumeNumber: number
  title: string
  chapters: Chapter[]
}

type ChapterOutlineRow = {
  key: string
  outline: Outline
  chapter?: Chapter
}

type ChapterAiAction = 'polish-outline' | 'generate-content' | 'rewrite-content' | 'polish-content'

type SelectionRewriteSnapshot = {
  chapterId: number
  baseContent: string
  selectedText: string
  start: number
  end: number
  contextBefore: string
  contextAfter: string
  buttonX: number
  buttonY: number
}

const SELECTION_CONTEXT_LENGTH = 500

const showChapterDialog = ref(false)
const showChapterDetail = ref(false)
const showChapterAiDialog = ref(false)
const showSelectionRewriteDialog = ref(false)
const isLoadingOutlines = ref(false)
const isLoadingChapters = ref(false)
const isSavingChapter = ref(false)
const isRunningChapterAi = ref(false)
const isSavingChapterAiResult = ref(false)
const isGeneratingSelectionRewrite = ref(false)
const isSavingSelectionRewrite = ref(false)
const runningChapterAiKey = ref('')
const runningChapterAiAction = ref<ChapterAiAction | null>(null)
const editingChapterId = ref<number | null>(null)
const selectedChapter = ref<Chapter | null>(null)
const activeChapterAiRow = ref<ChapterOutlineRow | null>(null)
const chapterContentRef = ref<HTMLElement | null>(null)
const selectionSnapshot = ref<SelectionRewriteSnapshot | null>(null)
const selectionRewriteSnapshot = ref<SelectionRewriteSnapshot | null>(null)
const chapterError = ref('')
const chapterFormError = ref('')
const chapterAiError = ref('')
const selectionRewriteError = ref('')
const chapterAiRequirements = ref('')
const selectionRewriteRequirements = ref('')
const streamedContent = ref('')
const selectionRewriteContent = ref('')
const outlines = ref<Outline[]>([])
const chapters = ref<Chapter[]>([])
const chapterForm = ref<ChapterForm>(createChapterForm())

const chapterAiActionLabels: Record<ChapterAiAction, string> = {
  'polish-outline': '剧情润色',
  'generate-content': 'AI 写作正文',
  'rewrite-content': 'AI 重写正文',
  'polish-content': 'AI 润色正文',
}

const chapterGroups = computed<ChapterGroup[]>(() => {
  const grouped = new Map<number, Chapter[]>()

  for (const chapter of chapters.value) {
    const volumeNumber = chapter.volume_number || 1
    grouped.set(volumeNumber, [...(grouped.get(volumeNumber) || []), chapter])
  }

  return [...grouped.entries()]
    .sort(([firstVolume], [secondVolume]) => firstVolume - secondVolume)
    .map(([volumeNumber, groupChapters]) => ({
      volumeNumber,
      title: `第 ${volumeNumber} 卷`,
      chapters: [...groupChapters].sort((firstChapter, secondChapter) => firstChapter.chapter_number - secondChapter.chapter_number),
    }))
})

const chapterOutlineRows = computed<ChapterOutlineRow[]>(() => outlines.value
  .filter((outline) => outline.outline_type === 'chapter' && Boolean(outline.chapter_number))
  .map((outline) => ({
    key: getOutlineKey(outline),
    outline,
    chapter: findChapterByOutline(outline),
  }))
  .sort((firstRow, secondRow) => {
    const firstVolume = firstRow.outline.volume_number || 1
    const secondVolume = secondRow.outline.volume_number || 1
    if (firstVolume !== secondVolume) return firstVolume - secondVolume
    return (firstRow.outline.chapter_number || 0) - (secondRow.outline.chapter_number || 0)
  }))

const canSaveChapterAiResult = computed(() => Boolean(streamedContent.value.trim()) && !isRunningChapterAi.value)
const canConfirmSelectionRewrite = computed(() => Boolean(selectionRewriteContent.value.trim()) && !isGeneratingSelectionRewrite.value)

onMounted(() => {
  void refreshChapterWorkspace()
})

function createChapterForm(): ChapterForm {
  const nextChapterNumber = chapters.value.length
    ? Math.max(...chapters.value.map((chapter) => chapter.chapter_number)) + 1
    : 1

  return {
    title: '',
    volume_number: 1,
    chapter_number: nextChapterNumber,
    status: 'draft',
    content: '',
  }
}

const loadOutlines = async () => {
  chapterError.value = ''
  isLoadingOutlines.value = true

  try {
    const response = await outlineApi.listByNovel(props.novelId)
    outlines.value = response.data
  } catch (error) {
    chapterError.value = getErrorMessage(error, '加载大纲失败')
  } finally {
    isLoadingOutlines.value = false
  }
}

const loadChapters = async () => {
  chapterError.value = ''
  isLoadingChapters.value = true

  try {
    const response = await chapterApi.listByNovel(props.novelId)
    chapters.value = response.data
    syncSelectedChapter()
  } catch (error) {
    chapterError.value = getErrorMessage(error, '加载章节失败')
  } finally {
    isLoadingChapters.value = false
  }
}

const refreshChapterWorkspace = async () => {
  await loadOutlines()
  await loadChapters()
}

const getOutlineKey = (outline: Outline) => `${outline.volume_number || 1}-${outline.chapter_number || outline.id}`

const findChapterByOutline = (outline: Outline) => chapters.value.find((chapter) => (
  (chapter.volume_number || 1) === (outline.volume_number || 1)
  && chapter.chapter_number === outline.chapter_number
))

const syncSelectedChapter = () => {
  if (!selectedChapter.value) return

  selectedChapter.value = chapters.value.find((chapter) => chapter.id === selectedChapter.value?.id) || null
  if (!selectedChapter.value) showChapterDetail.value = false
}

const openChapterDialog = (chapter?: Chapter) => {
  chapterFormError.value = ''
  chapterError.value = ''

  if (chapter) {
    editingChapterId.value = chapter.id
    chapterForm.value = {
      title: chapter.title,
      volume_number: chapter.volume_number || 1,
      chapter_number: chapter.chapter_number,
      status: chapter.status || 'draft',
      content: chapter.content || '',
    }
  } else {
    editingChapterId.value = null
    chapterForm.value = createChapterForm()
  }

  showChapterDialog.value = true
}

const openChapterDialogFromOutline = (outline: Outline) => {
  chapterFormError.value = ''
  chapterError.value = ''
  editingChapterId.value = null
  chapterForm.value = {
    title: outline.title,
    volume_number: outline.volume_number || 1,
    chapter_number: outline.chapter_number || 1,
    status: 'draft',
    content: '',
  }
  showChapterDialog.value = true
}

const closeChapterDialog = () => {
  if (isSavingChapter.value) return
  showChapterDialog.value = false
  editingChapterId.value = null
  chapterFormError.value = ''
}

const saveChapter = async () => {
  chapterFormError.value = ''
  chapterError.value = ''

  const title = chapterForm.value.title.trim()
  if (!title) {
    chapterFormError.value = '章节标题不能为空'
    return
  }

  const volumeNumber = normalizePositiveNumber(chapterForm.value.volume_number)
  const chapterNumber = normalizePositiveNumber(chapterForm.value.chapter_number)

  if (volumeNumber === 0) {
    chapterFormError.value = '卷号必须大于 0 或留空'
    return
  }

  if (!chapterNumber) {
    chapterFormError.value = '章节号必须为大于 0 的整数'
    return
  }

  isSavingChapter.value = true

  try {
    if (editingChapterId.value) {
      const payload: ChapterUpdate = {
        title,
        content: chapterForm.value.content.trim() || undefined,
        status: chapterForm.value.status,
      }
      const response = await chapterApi.update(editingChapterId.value, payload)
      selectedChapter.value = response.data
    } else {
      const payload: ChapterCreate = {
        novel_id: props.novelId,
        volume_number: volumeNumber || undefined,
        chapter_number: chapterNumber,
        title,
        content: chapterForm.value.content.trim() || undefined,
      }
      const response = await chapterApi.create(payload)
      selectedChapter.value = response.data
    }

    await loadChapters()
    showChapterDetail.value = Boolean(selectedChapter.value)
    closeChapterDialog()
  } catch (error) {
    chapterFormError.value = getErrorMessage(error, '保存章节失败')
  } finally {
    isSavingChapter.value = false
  }
}

const selectChapter = (chapter: Chapter) => {
  selectedChapter.value = chapter
  chapterError.value = ''
  clearSelectionSnapshot()
  resetSelectionRewriteDialog()
  showChapterDetail.value = true
}

const closeChapterDetail = () => {
  if (isGeneratingSelectionRewrite.value || isSavingSelectionRewrite.value) return
  showChapterDetail.value = false
  selectedChapter.value = null
  clearSelectionSnapshot()
  resetSelectionRewriteDialog()
}

const deleteChapter = async (chapter: Chapter) => {
  const confirmed = window.confirm(`确定要删除章节《${chapter.title}》吗？此操作不可恢复。`)
  if (!confirmed) return

  chapterError.value = ''

  try {
    await chapterApi.delete(chapter.id)
    if (selectedChapter.value?.id === chapter.id) {
      selectedChapter.value = null
      showChapterDetail.value = false
    }
    await loadChapters()
  } catch (error) {
    chapterError.value = getErrorMessage(error, '删除章节失败')
  }
}

const openChapterAiDialog = (row: ChapterOutlineRow, action: ChapterAiAction) => {
  if (isChapterAiDisabled(row)) return
  if ((action === 'rewrite-content' || action === 'polish-content') && !row.chapter?.content) return

  activeChapterAiRow.value = row
  runningChapterAiAction.value = action
  runningChapterAiKey.value = row.key
  chapterAiRequirements.value = ''
  chapterAiError.value = ''
  streamedContent.value = ''
  showChapterAiDialog.value = true
}

const closeChapterAiDialog = () => {
  if (isRunningChapterAi.value || isSavingChapterAiResult.value) return
  resetChapterAiDialog()
}

const resetChapterAiDialog = () => {
  showChapterAiDialog.value = false
  activeChapterAiRow.value = null
  runningChapterAiKey.value = ''
  runningChapterAiAction.value = null
  chapterAiRequirements.value = ''
  chapterAiError.value = ''
  streamedContent.value = ''
}

const startChapterAi = () => {
  chapterError.value = ''
  chapterAiError.value = ''
  streamedContent.value = ''
  isRunningChapterAi.value = true
}

const finishChapterAi = () => {
  isRunningChapterAi.value = false
}

const handleChapterAiError = (fallback: string, error: string) => {
  chapterAiError.value = `${fallback}：${error}`
  finishChapterAi()
}

const generateChapterAiPreview = async () => {
  const row = activeChapterAiRow.value
  const action = runningChapterAiAction.value
  if (!row || !action || isRunningChapterAi.value) return

  startChapterAi()
  const requirements = chapterAiRequirements.value.trim() || undefined

  if (action === 'polish-outline') {
    await aiApi.polishOutlineStream(
      {
        novel_id: props.novelId,
        outline_id: row.outline.id,
        polish_requirements: requirements,
        save: false,
      },
      appendChapterAiChunk,
      handleChapterAiDone,
      (error) => handleChapterAiError('剧情润色失败', error)
    )
    return
  }

  if (action === 'generate-content') {
    await aiApi.generateChapterContentStream(
      {
        novel_id: props.novelId,
        outline_id: row.outline.id,
        chapter_id: row.chapter?.id,
        target_words: 3000,
        writing_requirements: requirements,
        save: false,
      },
      appendChapterAiChunk,
      handleChapterAiDone,
      (error) => handleChapterAiError('AI 写作正文失败', error)
    )
    return
  }

  if (action === 'rewrite-content' && row.chapter) {
    await aiApi.rewriteChapterContentStream(
      {
        novel_id: props.novelId,
        chapter_id: row.chapter.id,
        rewrite_requirements: requirements,
        save: false,
      },
      appendChapterAiChunk,
      handleChapterAiDone,
      (error) => handleChapterAiError('AI 重写正文失败', error)
    )
    return
  }

  if (action === 'polish-content' && row.chapter) {
    await aiApi.polishChapterContentStream(
      {
        novel_id: props.novelId,
        chapter_id: row.chapter.id,
        style_requirements: requirements,
        save: false,
      },
      appendChapterAiChunk,
      handleChapterAiDone,
      (error) => handleChapterAiError('AI 润色正文失败', error)
    )
  }
}

const appendChapterAiChunk = (chunk: string) => {
  streamedContent.value += chunk
}

const handleChapterAiDone = (result: any) => {
  if (typeof result?.content === 'string' && result.content.trim()) {
    streamedContent.value = result.content
  }
  finishChapterAi()
}

const saveChapterAiResult = async () => {
  const row = activeChapterAiRow.value
  const action = runningChapterAiAction.value
  const content = streamedContent.value.trim()
  if (!row || !action || !content || isRunningChapterAi.value) return

  chapterAiError.value = ''
  isSavingChapterAiResult.value = true

  try {
    if (action === 'polish-outline') {
      await savePolishedOutline(row.outline, content)
    } else if (action === 'generate-content') {
      await saveGeneratedChapterContent(row, content)
    } else if ((action === 'rewrite-content' || action === 'polish-content') && row.chapter) {
      await saveUpdatedChapterContent(row.chapter, content)
    }

    resetChapterAiDialog()
  } catch (error) {
    chapterAiError.value = getErrorMessage(error, '保存 AI 生成结果失败')
  } finally {
    isSavingChapterAiResult.value = false
  }
}

const savePolishedOutline = async (outline: Outline, content: string) => {
  const payload: OutlineUpdate = {
    plot_summary: extractMarkdownSection(content, ['情节梗概']) || outline.plot_summary || undefined,
    key_events: extractMarkdownSection(content, ['关键事件']) || outline.key_events || undefined,
    characters_involved: extractMarkdownSection(content, ['涉及角色']) || outline.characters_involved || undefined,
  }

  if (!payload.plot_summary && !payload.key_events && !payload.characters_involved) {
    throw new Error('未解析到可保存的大纲内容')
  }

  await outlineApi.update(outline.id, payload)
  await loadOutlines()
}

const saveGeneratedChapterContent = async (row: ChapterOutlineRow, content: string) => {
  if (row.chapter) {
    const response = await chapterApi.update(row.chapter.id, { content })
    selectedChapter.value = response.data
  } else {
    const response = await chapterApi.create({
      novel_id: props.novelId,
      volume_number: row.outline.volume_number || 1,
      chapter_number: row.outline.chapter_number || 1,
      title: row.outline.title,
      content,
    })
    selectedChapter.value = response.data
  }

  await loadChapters()
  if (selectedChapter.value) showChapterDetail.value = true
}

const saveUpdatedChapterContent = async (chapter: Chapter, content: string) => {
  const response = await chapterApi.update(chapter.id, { content })
  selectedChapter.value = response.data
  await loadChapters()
  showChapterDetail.value = true
}

const extractMarkdownSection = (content: string, headings: string[]) => {
  const escapedHeadings = headings.map((heading) => heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  const pattern = new RegExp(`^##+\\s*(?:${escapedHeadings})\\s*$\\n([\\s\\S]*?)(?=^##+\\s+|$)`, 'm')
  const match = content.match(pattern)
  return match?.[1]?.trim()
}

const handleChapterTextSelection = () => {
  if (!selectedChapter.value?.content || showSelectionRewriteDialog.value) {
    clearSelectionSnapshot()
    return
  }

  const container = chapterContentRef.value
  const selection = window.getSelection()
  if (!container || !selection || selection.rangeCount === 0) {
    clearSelectionSnapshot()
    return
  }

  const range = selection.getRangeAt(0)
  if (!container.contains(range.commonAncestorContainer)) {
    clearSelectionSnapshot()
    return
  }

  const rawSelectedText = range.toString()
  const selectedText = rawSelectedText.trim()
  if (!selectedText) {
    clearSelectionSnapshot()
    return
  }

  const baseContent = selectedChapter.value.content
  const rawStart = getTextOffset(container, range.startContainer, range.startOffset)
  const rawEnd = getTextOffset(container, range.endContainer, range.endOffset)
  const leadingWhitespaceLength = rawSelectedText.length - rawSelectedText.trimStart().length
  const trailingWhitespaceLength = rawSelectedText.length - rawSelectedText.trimEnd().length
  const start = rawStart + leadingWhitespaceLength
  const end = rawEnd - trailingWhitespaceLength

  if (start < 0 || end <= start || baseContent.slice(start, end) !== selectedText) {
    clearSelectionSnapshot()
    return
  }

  const rect = range.getBoundingClientRect()
  selectionSnapshot.value = {
    chapterId: selectedChapter.value.id,
    baseContent,
    selectedText,
    start,
    end,
    contextBefore: baseContent.slice(Math.max(0, start - SELECTION_CONTEXT_LENGTH), start),
    contextAfter: baseContent.slice(end, Math.min(baseContent.length, end + SELECTION_CONTEXT_LENGTH)),
    buttonX: Math.min(window.innerWidth - 72, rect.right + 10),
    buttonY: Math.min(window.innerHeight - 42, rect.bottom + 10),
  }
}

const getTextOffset = (container: HTMLElement, targetNode: Node, targetOffset: number) => {
  const range = document.createRange()
  range.selectNodeContents(container)
  range.setEnd(targetNode, targetOffset)
  return range.toString().length
}

const clearSelectionSnapshot = () => {
  selectionSnapshot.value = null
}

const openSelectionRewriteDialog = () => {
  if (!selectionSnapshot.value) return
  selectionRewriteSnapshot.value = { ...selectionSnapshot.value }
  selectionRewriteRequirements.value = ''
  selectionRewriteContent.value = ''
  selectionRewriteError.value = ''
  showSelectionRewriteDialog.value = true
}

const closeSelectionRewriteDialog = () => {
  if (isGeneratingSelectionRewrite.value || isSavingSelectionRewrite.value) return
  resetSelectionRewriteDialog()
}

const resetSelectionRewriteDialog = () => {
  showSelectionRewriteDialog.value = false
  selectionRewriteSnapshot.value = null
  selectionRewriteRequirements.value = ''
  selectionRewriteContent.value = ''
  selectionRewriteError.value = ''
}

const generateSelectionRewritePreview = async () => {
  const snapshot = selectionRewriteSnapshot.value
  if (!snapshot || isGeneratingSelectionRewrite.value) return

  selectionRewriteError.value = ''
  selectionRewriteContent.value = ''
  isGeneratingSelectionRewrite.value = true

  await aiApi.rewriteChapterSelectionStream(
    {
      novel_id: props.novelId,
      chapter_id: snapshot.chapterId,
      selected_text: snapshot.selectedText,
      rewrite_requirements: selectionRewriteRequirements.value.trim() || undefined,
      context_before: snapshot.contextBefore || undefined,
      context_after: snapshot.contextAfter || undefined,
    },
    (chunk) => {
      selectionRewriteContent.value += chunk
    },
    (result) => {
      if (typeof result?.content === 'string' && result.content.trim()) {
        selectionRewriteContent.value = result.content
      }
      isGeneratingSelectionRewrite.value = false
    },
    (error) => {
      selectionRewriteError.value = `局部改写失败：${error}`
      isGeneratingSelectionRewrite.value = false
    }
  )
}

const confirmSelectionRewrite = async () => {
  const snapshot = selectionRewriteSnapshot.value
  const replacement = selectionRewriteContent.value.trim()
  if (!snapshot || !replacement || isGeneratingSelectionRewrite.value) return

  if (!selectedChapter.value || selectedChapter.value.id !== snapshot.chapterId) {
    selectionRewriteError.value = '当前章节已变化，请重新选择正文片段'
    return
  }

  if ((selectedChapter.value.content || '') !== snapshot.baseContent) {
    selectionRewriteError.value = '正文已变化，请重新选择正文片段'
    return
  }

  if (snapshot.baseContent.slice(snapshot.start, snapshot.end) !== snapshot.selectedText) {
    selectionRewriteError.value = '选中文本已变化，请重新选择正文片段'
    return
  }

  isSavingSelectionRewrite.value = true
  selectionRewriteError.value = ''

  try {
    const content = `${snapshot.baseContent.slice(0, snapshot.start)}${replacement}${snapshot.baseContent.slice(snapshot.end)}`
    const response = await chapterApi.update(snapshot.chapterId, { content })
    selectedChapter.value = response.data
    await loadChapters()
    clearSelectionSnapshot()
    resetSelectionRewriteDialog()
  } catch (error) {
    selectionRewriteError.value = getErrorMessage(error, '保存局部改写失败')
  } finally {
    isSavingSelectionRewrite.value = false
  }
}

const normalizePositiveNumber = (value: number | '') => {
  if (value === '') return undefined
  const numberValue = Number(value)
  if (!Number.isInteger(numberValue) || numberValue <= 0) return 0
  return numberValue
}

const getChapterStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
  }

  return statusMap[status] || status || '未知'
}

const getChapterRowStatus = (row: ChapterOutlineRow) => {
  if (!row.chapter) return '未添加正文'
  if (!row.chapter.content) return '未生成正文'
  return getChapterStatusLabel(row.chapter.status)
}

const formatOutlinePosition = (outline: Outline) => `第 ${outline.volume_number || 1} 卷 · 第 ${outline.chapter_number} 章`

const formatChapterPosition = (chapter: Chapter) => `第 ${chapter.volume_number || 1} 卷 · 第 ${chapter.chapter_number} 章`

const isChapterAiDisabled = (row: ChapterOutlineRow) => isRunningChapterAi.value || !row.outline.id

const getChapterAiRequirementPlaceholder = (action: ChapterAiAction) => {
  const placeholderMap: Record<ChapterAiAction, string> = {
    'polish-outline': '例如：增强反转，突出主角动机，结尾留一个悬念。',
    'generate-content': '例如：加强对话和动作描写，节奏更紧凑，结尾卡在危机处。',
    'rewrite-content': '例如：减少说明性文字，增强冲突，保持原剧情不变。',
    'polish-content': '例如：语言更细腻，提升画面感和情绪张力，不改变剧情。',
  }

  return placeholderMap[action]
}

const getChapterPreview = (chapter: Chapter) => {
  const content = chapter.content?.trim()
  if (!content) return '暂无正文'
  return content.length > 120 ? `${content.slice(0, 120)}...` : content
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
  min-height: 500px;
  padding: 30px;
  background: linear-gradient(180deg, #f8fbff 0%, #fff 220px);
  border-radius: 8px;
}

.tab-header,
.chapter-actions,
.empty-actions,
.form-actions,
.chapter-title-row,
.chapter-volume-header,
.dialog-title-row,
.chapter-detail-meta,
.chapter-meta,
.chapter-item-actions,
.chapter-manual-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tab-header,
.chapter-volume-header,
.dialog-title-row {
  align-items: center;
  justify-content: space-between;
}

.tab-header {
  margin-bottom: 24px;
}

.tab-header h2,
.dialog h2 {
  margin: 0;
  color: #1f2937;
}

.page-eyebrow {
  margin: 0 0 6px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.chapter-outline-list,
.chapters-list,
.chapter-volume {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.chapter-outline-card {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) 310px;
  gap: 18px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #dbeafe;
  border-radius: 16px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
}

.chapter-outline-card:hover {
  border-color: #93c5fd;
  box-shadow: 0 16px 34px rgba(37, 99, 235, 0.12);
  transform: translateY(-2px);
}

.chapter-outline-index {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 72px;
  color: #1d4ed8;
  background: linear-gradient(180deg, #eff6ff, #dbeafe);
  border-radius: 14px;
}

.chapter-outline-index span {
  font-size: 12px;
  font-weight: 600;
}

.chapter-outline-index strong {
  font-size: 28px;
  line-height: 1;
}

.chapter-outline-main,
.chapter-main {
  flex: 1;
  min-width: 0;
}

.chapter-outline-main h3,
.chapter-item h3,
.chapter-volume-header h3 {
  margin: 0 0 12px;
  color: #111827;
}

.outline-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.outline-detail-grid.compact {
  grid-template-columns: 1.2fr 1fr 1fr;
  margin-top: 0;
}

.outline-detail,
.chapter-outline-summary,
.ai-context-card {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #edf2f7;
  border-radius: 10px;
}

.outline-detail.primary-detail {
  background: #f0f9ff;
  border-color: #bae6fd;
}

.outline-detail label,
.chapter-outline-summary label,
.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #64748b;
  font-weight: 700;
  font-size: 13px;
}

.outline-detail p,
.chapter-outline-summary p,
.ai-context-card p {
  margin: 0;
  color: #475569;
  line-height: 1.6;
  white-space: pre-wrap;
}

.ai-context-card {
  margin: 18px 0;
}

.ai-context-card h3 {
  margin: 0 0 8px;
  color: #1f2937;
}

.chapter-ai-actions {
  display: flex;
  align-content: flex-start;
  align-items: stretch;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
}

.chapter-manual-actions {
  justify-content: flex-end;
  width: 100%;
  padding-top: 8px;
  border-top: 1px dashed #e5e7eb;
}

.ai-action-btn {
  min-width: 132px;
  padding: 9px 12px;
  color: #1f2937;
  font-weight: 700;
  background: #f8fafc;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s, background 0.2s;
}

.ai-action-btn:hover:not(:disabled) {
  border-color: #60a5fa;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.16);
  transform: translateY(-1px);
}

.ai-action-btn.primary {
  color: white;
  background: linear-gradient(135deg, #16a34a, #22c55e);
  border-color: transparent;
}

.ai-action-btn.secondary {
  color: #1d4ed8;
  background: #eff6ff;
  border-color: #bfdbfe;
}

.ai-action-btn.overwrite {
  color: #b45309;
  background: #fffbeb;
  border-color: #fde68a;
}

.ai-action-btn:disabled {
  color: #9ca3af;
  background: #f3f4f6;
  border-color: #e5e7eb;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

.chapter-number {
  color: #1f6fb2;
  font-size: 13px;
  font-weight: 600;
}

.chapter-status {
  display: inline-block;
  padding: 3px 8px;
  color: #2f7d32;
  background: #eef8ef;
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}

.chapter-status.empty {
  color: #8a5a00;
  background: #fff8e6;
}

.chapter-meta,
.chapter-detail-meta {
  color: #777;
  font-size: 13px;
}

.chapter-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
}

.chapter-item:hover {
  border-color: #9ac7ed;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.chapter-preview {
  margin: 0 0 10px;
  color: #666;
  line-height: 1.6;
  white-space: pre-wrap;
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

.compact-empty {
  padding: 28px 20px;
}

.empty-actions {
  justify-content: center;
  margin-top: 20px;
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

.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.58);
}

.dialog {
  width: 500px;
  max-width: 90%;
  padding: 30px;
  background: white;
  border-radius: 14px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.25);
}

.chapter-form-dialog,
.chapter-detail-dialog {
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.chapter-ai-dialog,
.selection-rewrite-dialog {
  width: min(1080px, 96vw);
  max-height: 92vh;
  overflow-y: auto;
}

.selection-rewrite-dialog {
  width: min(920px, 96vw);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.form-group {
  margin-bottom: 20px;
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

.form-hint {
  margin: -8px 0 16px;
  color: #777;
  font-size: 13px;
}

.ai-preview-panel {
  overflow: hidden;
  border: 1px solid #bfdbfe;
  border-radius: 12px;
  background: #fff;
}

.ai-preview-panel.empty {
  border-color: #e5e7eb;
}

.ai-preview-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  color: #1e3a8a;
  background: #eff6ff;
  border-bottom: 1px solid #bfdbfe;
}

.ai-preview-header span {
  color: #64748b;
  font-size: 13px;
}

.preview-text {
  max-height: 44vh;
  min-height: 220px;
  padding: 16px;
  overflow-y: auto;
  color: #1f2937;
  font-family: ui-serif, Georgia, 'Times New Roman', serif;
  line-height: 1.9;
}

.chapter-content-full {
  min-height: 180px;
  padding: 16px;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f8fafc;
  border: 1px solid #eee;
  border-radius: 8px;
  outline: none;
}

.chapter-content-full::selection {
  color: #0f172a;
  background: #bfdbfe;
}

.selection-edit-button {
  position: fixed;
  z-index: 1100;
  padding: 8px 14px;
  color: white;
  font-weight: 700;
  background: linear-gradient(135deg, #2563eb, #60a5fa);
  border: none;
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
  cursor: pointer;
}

.selected-text-preview {
  max-height: 180px;
  padding: 14px;
  overflow-y: auto;
  color: #334155;
  line-height: 1.8;
  white-space: pre-wrap;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.selection-preview-panel {
  margin-top: 8px;
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

.btn-text:disabled {
  color: #aaa;
  cursor: not-allowed;
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

@media (max-width: 1180px) {
  .chapter-outline-card {
    grid-template-columns: 64px minmax(0, 1fr);
  }

  .chapter-ai-actions {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .chapter-manual-actions {
    justify-content: flex-start;
  }

  .outline-detail-grid.compact {
    grid-template-columns: 1fr;
  }
}
</style>
