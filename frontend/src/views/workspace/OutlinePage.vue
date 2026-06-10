<template>
  <div class="tab-content">
    <div class="tab-header">
      <h2>剧情大纲</h2>
      <div class="outline-actions">
        <button class="btn-secondary" :disabled="isLoadingOutlines || isAiBusy" @click="loadOutlines">
          {{ isLoadingOutlines ? '刷新中...' : '刷新大纲' }}
        </button>
        <button v-if="!selectionMode" class="btn-secondary" :disabled="isAiBusy || outlines.length === 0" @click="enableSelectionMode">多选</button>
        <button v-if="selectionMode" class="btn-secondary" @click="cancelSelectionMode">取消多选</button>
        <button v-if="selectionMode" class="btn-danger" :disabled="selectedOutlineIds.length === 0" @click="batchDeleteOutlines">
          删除选中 ({{ selectedOutlineIds.length }})
        </button>
        <button v-if="!selectionMode" class="btn-secondary" :disabled="isAiBusy" @click="openOutlineDialog()">新增大纲项</button>
        <button v-if="!selectionMode" class="btn-primary" :disabled="isAiBusy" @click="showPlanDialog = true">一键规划大纲</button>
      </div>
    </div>

    <div v-if="outlineError" class="error-message">
      <span>{{ outlineError }}</span>
      <button type="button" @click="outlineError = ''">关闭</button>
    </div>

    <div v-if="isGenerating || isGeneratingVolumeChapters" class="generating">
      <div class="generating-content">
        <div class="spinner"></div>
        <h3>{{ generationTitle }}</h3>
        <div class="streaming-text">{{ activeStreamedContent }}<span class="cursor">▌</span></div>
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

        <div v-for="node in outlineTreeNodes" :key="node.volume.id" class="outline-tree-node">
          <div class="outline-item volume-outline" :class="{ 'selection-mode': selectionMode }">
            <label v-if="selectionMode" class="selection-checkbox">
              <input type="checkbox" :checked="selectedOutlineIds.includes(node.volume.id)" @change="toggleSelection(node.volume.id)" />
            </label>
            <div class="outline-item-header">
              <div>
                <div class="outline-meta">
                  <span>{{ getOutlineTypeLabel(node.volume.outline_type) }}</span>
                  <span v-if="node.volume.volume_number">第 {{ node.volume.volume_number }} 卷</span>
                  <span>{{ node.chapters.length }} 个节章</span>
                </div>
                <h3>{{ node.volume.title }}</h3>
              </div>
              <div v-if="!selectionMode" class="outline-item-actions">
                <button class="btn-text" type="button" @click="toggleVolume(node.volume.id)">
                  {{ expandedVolumeIds[node.volume.id] ? '收起节章' : '展开节章' }}
                </button>
                <button class="btn-text" type="button" :disabled="isAiBusy" @click="openGenerateChaptersDialog(node.volume)">
                  {{ node.chapters.length ? '重新生成节章' : '生成节章' }}
                </button>
                <button class="btn-text" type="button" @click="openOutlineDialog(node.volume)">编辑</button>
                <button class="btn-text danger" type="button" @click="deleteOutline(node.volume)">删除</button>
              </div>
            </div>
            <p class="outline-summary">{{ node.volume.plot_summary || '暂无情节梗概' }}</p>
            <div v-if="node.volume.key_events || node.volume.characters_involved" class="outline-detail-grid">
              <div v-if="node.volume.key_events" class="outline-detail">
                <label>关键事件</label>
                <p>{{ node.volume.key_events }}</p>
              </div>
              <div v-if="node.volume.characters_involved" class="outline-detail">
                <label>涉及角色</label>
                <p>{{ node.volume.characters_involved }}</p>
              </div>
            </div>
            <p class="updated-at">更新于 {{ formatDate(node.volume.updated_at) }}</p>
          </div>

          <div v-if="expandedVolumeIds[node.volume.id]" class="chapter-children">
            <div v-if="node.chapters.length === 0" class="empty-child-state">
              当前卷还没有节章，点击“生成节章”后会显示在这里。
            </div>
            <div v-for="chapter in node.chapters" :key="chapter.id" class="outline-item chapter-outline" :class="{ 'selection-mode': selectionMode }">
              <label v-if="selectionMode" class="selection-checkbox">
                <input type="checkbox" :checked="selectedOutlineIds.includes(chapter.id)" @change="toggleSelection(chapter.id)" />
              </label>
              <div class="outline-item-header">
                <div>
                  <div class="outline-meta">
                    <span>{{ getOutlineTypeLabel(chapter.outline_type) }}</span>
                    <span v-if="chapter.volume_number">第 {{ chapter.volume_number }} 卷</span>
                    <span v-if="chapter.chapter_number">第 {{ chapter.chapter_number }} 章</span>
                  </div>
                  <h3>{{ chapter.title }}</h3>
                </div>
                <div v-if="!selectionMode" class="outline-item-actions">
                  <button class="btn-text" type="button" @click="toggleChapter(chapter.id)">
                    {{ expandedChapterIds[chapter.id] ? '收起详情' : '展开详情' }}
                  </button>
                  <button class="btn-text" type="button" @click="openOutlineDialog(chapter)">编辑</button>
                  <button class="btn-text danger" type="button" @click="deleteOutline(chapter)">删除</button>
                </div>
              </div>
              <p class="outline-summary">{{ chapter.plot_summary || '暂无情节梗概' }}</p>
              <div v-if="expandedChapterIds[chapter.id]" class="chapter-detail-panel">
                <div v-if="chapter.key_events || chapter.characters_involved" class="outline-detail-grid">
                  <div v-if="chapter.key_events" class="outline-detail">
                    <label>关键事件</label>
                    <p>{{ chapter.key_events }}</p>
                  </div>
                  <div v-if="chapter.characters_involved" class="outline-detail">
                    <label>涉及角色</label>
                    <p>{{ chapter.characters_involved }}</p>
                  </div>
                </div>
                <p class="updated-at">更新于 {{ formatDate(chapter.updated_at) }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="orphanChapterOutlines.length > 0" class="outline-tree-node">
          <div class="outline-item orphan-outline">
            <div class="outline-item-header">
              <div>
                <div class="outline-meta">
                  <span>未归属节章</span>
                  <span>{{ orphanChapterOutlines.length }} 个节章</span>
                </div>
                <h3>未归属节章</h3>
              </div>
            </div>
            <p class="outline-summary">这些节章没有匹配到对应卷级大纲，仍可编辑或删除。</p>
          </div>
          <div class="chapter-children orphan-children">
            <div v-for="chapter in orphanChapterOutlines" :key="chapter.id" class="outline-item chapter-outline" :class="{ 'selection-mode': selectionMode }">
              <label v-if="selectionMode" class="selection-checkbox">
                <input type="checkbox" :checked="selectedOutlineIds.includes(chapter.id)" @change="toggleSelection(chapter.id)" />
              </label>
              <div class="outline-item-header">
                <div>
                  <div class="outline-meta">
                    <span>{{ getOutlineTypeLabel(chapter.outline_type) }}</span>
                    <span v-if="chapter.volume_number">第 {{ chapter.volume_number }} 卷</span>
                    <span v-if="chapter.chapter_number">第 {{ chapter.chapter_number }} 章</span>
                  </div>
                  <h3>{{ chapter.title }}</h3>
                </div>
                <div v-if="!selectionMode" class="outline-item-actions">
                  <button class="btn-text" type="button" @click="toggleChapter(chapter.id)">
                    {{ expandedChapterIds[chapter.id] ? '收起详情' : '展开详情' }}
                  </button>
                  <button class="btn-text" type="button" @click="openOutlineDialog(chapter)">编辑</button>
                  <button class="btn-text danger" type="button" @click="deleteOutline(chapter)">删除</button>
                </div>
              </div>
              <p class="outline-summary">{{ chapter.plot_summary || '暂无情节梗概' }}</p>
              <div v-if="expandedChapterIds[chapter.id]" class="chapter-detail-panel">
                <div v-if="chapter.key_events || chapter.characters_involved" class="outline-detail-grid">
                  <div v-if="chapter.key_events" class="outline-detail">
                    <label>关键事件</label>
                    <p>{{ chapter.key_events }}</p>
                  </div>
                  <div v-if="chapter.characters_involved" class="outline-detail">
                    <label>涉及角色</label>
                    <p>{{ chapter.characters_involved }}</p>
                  </div>
                </div>
                <p class="updated-at">更新于 {{ formatDate(chapter.updated_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPlanDialog" class="dialog-overlay" @click.self="showPlanDialog = false">
      <div class="dialog">
        <h2>一键规划小说大纲</h2>
        <div v-if="outlines.length > 0" class="warning-message">
          <strong>注意：</strong>本操作将删除当前所有大纲，重新规划卷级大纲。
        </div>
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
            <textarea v-model="planRequest.style_requirements" rows="12" :disabled="isGenerating"></textarea>
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

    <div v-if="showGenerateChaptersDialog && activeVolumeOutline" class="dialog-overlay" @click.self="closeGenerateChaptersDialog">
      <div class="dialog">
        <h2>{{ getVolumeChapters(activeVolumeOutline).length ? '重新生成节章' : '生成节章' }}</h2>
        <form @submit.prevent="handleGenerateVolumeChapters">
          <div v-if="volumeChapterFormError" class="form-error">{{ volumeChapterFormError }}</div>
          <div class="outline-context-card">
            <strong>第 {{ activeVolumeOutline.volume_number }} 卷：{{ activeVolumeOutline.title }}</strong>
            <p>{{ activeVolumeOutline.plot_summary || '暂无情节梗概' }}</p>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>本卷节章数</label>
              <input v-model.number="volumeChapterForm.target_chapters" type="number" min="1" required :disabled="isGeneratingVolumeChapters" />
            </div>
            <div class="form-group">
              <label>起始章节号</label>
              <input v-model.number="volumeChapterForm.start_chapter_number" type="number" min="1" required :disabled="isGeneratingVolumeChapters" />
            </div>
          </div>
          <div class="form-group">
            <label>风格要求（可选）</label>
            <textarea v-model="volumeChapterForm.style_requirements" rows="3" :disabled="isGeneratingVolumeChapters"></textarea>
          </div>
          <label v-if="getVolumeChapters(activeVolumeOutline).length" class="checkbox-field">
            <input v-model="volumeChapterForm.replace_existing" type="checkbox" :disabled="isGeneratingVolumeChapters" />
            <span>覆盖当前卷已有的 {{ getVolumeChapters(activeVolumeOutline).length }} 个节章</span>
          </label>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="isGeneratingVolumeChapters" @click="closeGenerateChaptersDialog">取消</button>
            <button type="submit" class="btn-primary" :disabled="isGeneratingVolumeChapters">
              {{ isGeneratingVolumeChapters ? '生成中...' : '开始生成节章' }}
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
  <ConfirmDialog ref="confirmDialog" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { aiApi, outlineApi } from '../../api'
import type { Outline, OutlineCreate, OutlineUpdate } from '../../types'
import ConfirmDialog from '../../components/ConfirmDialog.vue'

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

type VolumeChapterForm = {
  target_chapters: number | ''
  start_chapter_number: number | ''
  style_requirements: string
  replace_existing: boolean
}

type OutlineTreeNode = {
  volume: Outline
  chapters: Outline[]
}

const showPlanDialog = ref(false)
const showOutlineDialog = ref(false)
const showGenerateChaptersDialog = ref(false)
const isGenerating = ref(false)
const isGeneratingVolumeChapters = ref(false)
const isLoadingOutlines = ref(false)
const isSavingOutline = ref(false)
const selectionMode = ref(false)
const selectedOutlineIds = ref<number[]>([])
const editingOutlineId = ref<number | null>(null)
const generatingVolumeId = ref<number | null>(null)
const activeVolumeOutline = ref<Outline | null>(null)
const outlineError = ref('')
const outlineFormError = ref('')
const volumeChapterFormError = ref('')
const streamedContent = ref('')
const generatedOutlineText = ref('')
const volumeChapterStreamedContent = ref('')
const expandedVolumeIds = ref<Record<number, boolean>>({})
const expandedChapterIds = ref<Record<number, boolean>>({})
const outlines = ref<Outline[]>([])
const confirmDialog = ref<InstanceType<typeof ConfirmDialog>>()
const outlineForm = ref<OutlineForm>(createOutlineForm())
const volumeChapterForm = ref<VolumeChapterForm>(createVolumeChapterForm())
const planRequest = ref({
  target_words: 1000000,
  target_chapters: 200,
  target_volumes: 5,
  style_requirements: '',
})

const isAiBusy = computed(() => isGenerating.value || isGeneratingVolumeChapters.value)
const activeStreamedContent = computed(() => isGeneratingVolumeChapters.value ? volumeChapterStreamedContent.value : streamedContent.value)
const generationTitle = computed(() => {
  if (isGeneratingVolumeChapters.value && activeVolumeOutline.value) {
    return `正在生成第 ${activeVolumeOutline.value.volume_number || '?'} 卷节章`
  }

  return '正在规划卷级大纲'
})

const volumeOutlines = computed(() => outlines.value
  .filter((outline) => outline.outline_type === 'volume')
  .sort(sortOutlines)
)

const chapterOutlines = computed(() => outlines.value
  .filter((outline) => outline.outline_type === 'chapter')
  .sort(sortOutlines)
)

const outlineTreeNodes = computed<OutlineTreeNode[]>(() => volumeOutlines.value.map((volume) => ({
  volume,
  chapters: chapterOutlines.value.filter((chapter) => chapter.volume_number === volume.volume_number),
})))

const orphanChapterOutlines = computed(() => {
  const volumeNumbers = new Set(volumeOutlines.value.map((volume) => volume.volume_number).filter(Boolean))
  return chapterOutlines.value.filter((chapter) => !chapter.volume_number || !volumeNumbers.has(chapter.volume_number))
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

function createVolumeChapterForm(): VolumeChapterForm {
  return {
    target_chapters: 20,
    start_chapter_number: 1,
    style_requirements: '',
    replace_existing: false,
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
  const childCount = outline.outline_type === 'volume' ? getVolumeChapters(outline).length : 0
  const message = childCount > 0
    ? `确定要删除大纲项《${outline.title}》吗？此操作会同时删除下方 ${childCount} 个节章，且不可恢复。`
    : `确定要删除大纲项《${outline.title}》吗？此操作不可恢复。`

  const confirmed = await confirmDialog.value?.show({
    title: '删除大纲',
    message,
    confirmText: '删除',
    type: 'danger'
  })

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
        expandAllVolumes()
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

const openGenerateChaptersDialog = (volume: Outline) => {
  outlineError.value = ''
  volumeChapterFormError.value = ''
  activeVolumeOutline.value = volume
  volumeChapterForm.value = {
    target_chapters: getDefaultTargetChapters(volume),
    start_chapter_number: getDefaultStartChapterNumber(volume),
    style_requirements: '',
    replace_existing: getVolumeChapters(volume).length > 0,
  }
  showGenerateChaptersDialog.value = true
}

const closeGenerateChaptersDialog = () => {
  if (isGeneratingVolumeChapters.value) return
  showGenerateChaptersDialog.value = false
  activeVolumeOutline.value = null
  volumeChapterFormError.value = ''
}

const handleGenerateVolumeChapters = async () => {
  if (!activeVolumeOutline.value) return

  volumeChapterFormError.value = ''
  outlineError.value = ''

  const targetChapters = normalizePositiveNumber(volumeChapterForm.value.target_chapters)
  const startChapterNumber = normalizePositiveNumber(volumeChapterForm.value.start_chapter_number)

  if (!targetChapters) {
    volumeChapterFormError.value = '本卷节章数必须为大于 0 的整数'
    return
  }

  if (!startChapterNumber) {
    volumeChapterFormError.value = '起始章节号必须为大于 0 的整数'
    return
  }

  const existingChapters = getVolumeChapters(activeVolumeOutline.value)
  if (existingChapters.length > 0 && !volumeChapterForm.value.replace_existing) {
    volumeChapterFormError.value = '当前卷已有节章，请勾选覆盖后再重新生成'
    return
  }

  const volume = activeVolumeOutline.value
  showGenerateChaptersDialog.value = false
  isGeneratingVolumeChapters.value = true
  generatingVolumeId.value = volume.id
  volumeChapterStreamedContent.value = ''

  try {
    await aiApi.generateVolumeChaptersStream(
      {
        novel_id: props.novelId,
        outline_id: volume.id,
        target_chapters: targetChapters,
        start_chapter_number: startChapterNumber,
        style_requirements: volumeChapterForm.value.style_requirements.trim() || undefined,
        replace_existing: volumeChapterForm.value.replace_existing,
      },
      (chunk) => {
        volumeChapterStreamedContent.value += chunk
      },
      async () => {
        isGeneratingVolumeChapters.value = false
        generatingVolumeId.value = null
        await loadOutlines()
        setVolumeExpanded(volume.id, true)
        activeVolumeOutline.value = null
      },
      (error) => {
        isGeneratingVolumeChapters.value = false
        generatingVolumeId.value = null
        outlineError.value = `生成节章失败：${error}`
      }
    )
  } catch (error) {
    isGeneratingVolumeChapters.value = false
    generatingVolumeId.value = null
    outlineError.value = getErrorMessage(error, '生成节章失败')
  }
}

const getVolumeChapters = (volume: Outline) => chapterOutlines.value.filter((chapter) => chapter.volume_number === volume.volume_number)

const getDefaultTargetChapters = (volume: Outline) => {
  const existingChapters = getVolumeChapters(volume)
  if (existingChapters.length > 0) return existingChapters.length

  const targetChapters = planRequest.value.target_chapters || 0
  const targetVolumes = planRequest.value.target_volumes || 0
  if (targetChapters > 0 && targetVolumes > 0) {
    return Math.max(1, Math.ceil(targetChapters / targetVolumes))
  }

  return 20
}

const getDefaultStartChapterNumber = (volume: Outline) => {
  const existingChapterNumbers = getVolumeChapters(volume)
    .map((chapter) => chapter.chapter_number)
    .filter((chapterNumber): chapterNumber is number => Boolean(chapterNumber))
  if (existingChapterNumbers.length > 0) return Math.min(...existingChapterNumbers)

  const allChapterNumbers = chapterOutlines.value
    .map((chapter) => chapter.chapter_number)
    .filter((chapterNumber): chapterNumber is number => Boolean(chapterNumber))
  if (allChapterNumbers.length === 0) return 1

  return Math.max(...allChapterNumbers) + 1
}

const toggleVolume = (volumeId: number) => {
  setVolumeExpanded(volumeId, !expandedVolumeIds.value[volumeId])
}

const setVolumeExpanded = (volumeId: number, expanded: boolean) => {
  expandedVolumeIds.value = {
    ...expandedVolumeIds.value,
    [volumeId]: expanded,
  }
}

const toggleChapter = (chapterId: number) => {
  expandedChapterIds.value = {
    ...expandedChapterIds.value,
    [chapterId]: !expandedChapterIds.value[chapterId],
  }
}

const expandAllVolumes = () => {
  expandedVolumeIds.value = Object.fromEntries(volumeOutlines.value.map((volume) => [volume.id, true]))
}

const sortOutlines = (firstOutline: Outline, secondOutline: Outline) => {
  const firstVolume = firstOutline.volume_number || Number.MAX_SAFE_INTEGER
  const secondVolume = secondOutline.volume_number || Number.MAX_SAFE_INTEGER
  if (firstVolume !== secondVolume) return firstVolume - secondVolume

  const firstChapter = firstOutline.chapter_number || Number.MAX_SAFE_INTEGER
  const secondChapter = secondOutline.chapter_number || Number.MAX_SAFE_INTEGER
  if (firstChapter !== secondChapter) return firstChapter - secondChapter

  return firstOutline.id - secondOutline.id
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

const enableSelectionMode = () => {
  selectionMode.value = true
  selectedOutlineIds.value = []
}

const cancelSelectionMode = () => {
  selectionMode.value = false
  selectedOutlineIds.value = []
}

const toggleSelection = (outlineId: number) => {
  const index = selectedOutlineIds.value.indexOf(outlineId)
  if (index > -1) {
    selectedOutlineIds.value.splice(index, 1)
  } else {
    selectedOutlineIds.value.push(outlineId)
  }
}

const batchDeleteOutlines = async () => {
  if (selectedOutlineIds.value.length === 0) return

  const confirmed = await confirmDialog.value?.show({
    title: '批量删除大纲',
    message: `确定要删除选中的 ${selectedOutlineIds.value.length} 个大纲项吗？此操作不可恢复。`,
    confirmText: '删除',
    type: 'danger'
  })

  if (!confirmed) return

  outlineError.value = ''

  try {
    await outlineApi.batchDelete(selectedOutlineIds.value)
    await loadOutlines()
    cancelSelectionMode()
  } catch (error) {
    outlineError.value = getErrorMessage(error, '批量删除失败')
  }
}

</script>

<style scoped>
.tab-content {
  min-height: 500px;
  padding: 30px;
  background: var(--card-bg);
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
  color: var(--text-secondary);
  text-align: center;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.empty-state h3 {
  margin: 0 0 10px;
  color: var(--text-primary);
}

.empty-actions {
  justify-content: center;
  margin-top: 20px;
}

.generated-outline,
.outline-item {
  padding: 18px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.outline-tree-node {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.volume-outline {
  border-left: 4px solid var(--success-color);
}

.chapter-children {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-left: 24px;
  padding-left: 18px;
  border-left: 2px solid var(--success-border);
}

.chapter-outline {
  background: var(--success-bg);
}

.orphan-outline {
  border-left: 4px solid var(--warning-color);
}

.orphan-children {
  border-left-color: var(--warning-border);
}

.empty-child-state {
  padding: 16px;
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  border: 1px dashed var(--border-color);
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
  color: var(--success-color);
  background: var(--success-bg);
  border-radius: 999px;
  font-size: 12px;
}

.outline-item h3,
.generated-outline h3 {
  margin: 0;
  color: var(--text-primary);
}

.outline-summary {
  margin: 12px 0;
  color: var(--text-secondary);
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
  background: var(--panel-bg-soft);
  border-radius: 6px;
}

.outline-detail label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
  font-size: 13px;
}

.outline-detail p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.chapter-detail-panel {
  margin-top: 12px;
}

.updated-at {
  margin: 12px 0 0;
  color: var(--text-muted);
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

.generating-content h3 {
  margin: 0 0 16px;
  color: var(--text-primary);
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 20px;
  border: 3px solid var(--disabled-bg);
  border-top: 3px solid var(--info-color);
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
  color: var(--danger-color);
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: 5px;
}

.warning-message {
  margin-bottom: 16px;
  padding: 10px 12px;
  color: var(--warning-color);
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
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
  color: var(--info-color);
  background: transparent;
  border: none;
  cursor: pointer;
}

.btn-text.danger {
  color: var(--danger-color);
}

.btn-text:disabled {
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-danger {
  padding: 10px 20px;
  color: white;
  background: var(--danger-color);
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.btn-danger:disabled {
  background: var(--disabled-bg);
  cursor: not-allowed;
}

.outline-item.selection-mode {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.selection-checkbox {
  flex-shrink: 0;
  padding-top: 4px;
  cursor: pointer;
}

.selection-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.loading {
  padding: 50px;
  color: var(--text-secondary);
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
  width: 60%;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 30px;
  background: var(--card-bg);
  border-radius: 8px;
}

.dialog h2 {
  margin: 0 0 20px;
}

.outline-context-card {
  margin-bottom: 20px;
  padding: 12px;
  background: var(--panel-bg-soft);
  border-radius: 6px;
}

.outline-context-card p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.checkbox-field {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: var(--text-secondary);
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
  border: 1px solid var(--border-color);
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
  background: var(--success-color);
}

.btn-secondary {
  color: var(--text-primary);
  background: var(--disabled-bg);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  background: var(--disabled-bg);
  cursor: not-allowed;
}
</style>
