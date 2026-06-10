<template>
  <div class="tab-content">
    <div class="tab-header">
      <h2>角色卡</h2>
      <div class="character-actions-top">
        <button class="btn-secondary" type="button" :disabled="isGenerating || isCharacterBusy" @click="openCharacterDialog()">
          新增角色
        </button>
        <button class="btn-primary" type="button" :disabled="isGenerating || isCharacterBusy" @click="generateCharacters">
          批量生成角色
        </button>
      </div>
    </div>

    <div v-if="characters.length > 0" class="batch-toolbar">
      <span>已选择 {{ selectedCharacterCount }} 个角色</span>
      <button class="btn-secondary" type="button" :disabled="isCharacterBusy" @click="toggleAllCharactersSelection">
        {{ isAllCharactersSelected ? '取消全选' : '全选' }}
      </button>
      <button class="btn-secondary" type="button" :disabled="!hasSelectedCharacters || isCharacterBusy" @click="batchDeleteSelectedCharacters">
        {{ isBatchDeletingCharacters ? '删除中...' : '批量删除' }}
      </button>
      <button class="btn-primary" type="button" :disabled="!hasSelectedCharacters || isGenerating || isCharacterBusy" @click="batchPolishSelectedCharacters">
        {{ isBatchPolishingCharacters ? '润色中...' : '批量润色' }}
      </button>
      <button class="btn-text" type="button" :disabled="!hasSelectedCharacters || isCharacterBusy" @click="clearCharacterSelection">
        清空选择
      </button>
    </div>

    <div v-if="isBatchPolishingCharacters" class="batch-progress">
      <strong>{{ batchPolishProgressText }}</strong>
      <div class="streaming-text">{{ streamedContent }}<span class="cursor">▌</span></div>
    </div>

    <div v-if="characterError" class="error-message">
      <span>{{ characterError }}</span>
      <button type="button" @click="characterError = ''">关闭</button>
    </div>

    <div v-if="isGenerating" class="generating">
      <div class="generating-content">
        <div class="spinner"></div>
        <div class="streaming-text">{{ streamedContent }}<span class="cursor">▌</span></div>
      </div>
    </div>
    <div v-else-if="isLoadingCharacters" class="loading">角色加载中...</div>
    <div v-else-if="characters.length === 0" class="empty-state">
      <h3>暂无角色卡</h3>
      <p>可以手动新增角色，或根据大纲批量生成角色卡。</p>
      <div class="empty-actions">
        <button class="btn-secondary" type="button" @click="openCharacterDialog()">新增角色</button>
        <button class="btn-primary" type="button" @click="generateCharacters">批量生成角色</button>
      </div>
    </div>
    <div v-else class="characters-grid">
      <div
        v-for="char in characters"
        :key="char.id"
        class="character-card"
        :class="{ selected: isCharacterSelected(char.id), polishing: polishingCharacterId === char.id }"
        @click="selectCharacter(char)"
      >
        <label class="character-select" @click.stop>
          <input
            type="checkbox"
            :checked="isCharacterSelected(char.id)"
            :disabled="isCharacterBusy"
            @change="toggleCharacterSelection(char.id)"
          />
          <span>选择</span>
        </label>
        <div class="avatar">
          <img v-if="char.avatar_url" :src="char.avatar_url" alt="头像" />
          <div v-else class="avatar-placeholder">{{ getCharacterInitial(char) }}</div>
        </div>
        <div class="char-info">
          <div class="char-title-row">
            <h3>{{ char.name }}</h3>
            <span class="importance-badge">{{ getImportanceLabel(char.importance) }}</span>
          </div>
          <p class="char-meta">{{ formatCharacterMeta(char) }}</p>
          <p class="char-intro">{{ char.identity_info || '暂无身份简介' }}</p>
          <span v-if="char.is_detailed" class="badge-detailed">已详细</span>
        </div>
      </div>
    </div>

    <div v-if="showCharacterDetail && selectedCharacter" class="dialog-overlay" @click.self="closeCharacterDetail">
      <div class="dialog character-detail-dialog">
        <div class="dialog-title-row">
          <h2>{{ selectedCharacter.name }}</h2>
          <span class="importance-badge">{{ getImportanceLabel(selectedCharacter.importance) }}</span>
        </div>

        <div class="character-detail-header">
          <div class="avatar detail-avatar">
            <img v-if="selectedCharacter.avatar_url" :src="selectedCharacter.avatar_url" alt="头像" />
            <div v-else class="avatar-placeholder">{{ getCharacterInitial(selectedCharacter) }}</div>
          </div>
          <div>
            <p class="char-meta">{{ formatCharacterMeta(selectedCharacter) }}</p>
            <p class="char-intro">{{ selectedCharacter.identity_info || '暂无身份简介' }}</p>
            <span v-if="selectedCharacter.is_detailed" class="badge-detailed">已详细</span>
          </div>
        </div>

        <div v-if="isExpandingCharacter" class="generating compact-generating">
          <div class="spinner"></div>
          <div class="streaming-text">{{ streamedContent }}<span class="cursor">▌</span></div>
        </div>

        <div class="character-detail-sections">
          <div v-for="section in characterDetailSections" :key="section.label" class="character-detail-section">
            <label>{{ section.label }}</label>
            <p>{{ section.value || '暂无' }}</p>
          </div>
        </div>

        <p class="updated-at">更新于 {{ formatDate(selectedCharacter.updated_at) }}</p>

        <div class="form-actions character-actions">
          <button type="button" class="btn-secondary" :disabled="isCharacterBusy" @click="openCharacterDialog(selectedCharacter)">编辑</button>
          <button type="button" class="btn-secondary" :disabled="isCharacterBusy" @click="expandSelectedCharacter">
            {{ isExpandingCharacter ? '扩展中...' : 'AI 扩展详情' }}
          </button>
          <button type="button" class="btn-secondary" :disabled="isCharacterBusy" @click="generateSelectedCharacterAvatar">
            {{ isGeneratingAvatar ? '生成中...' : '生成头像' }}
          </button>
          <button type="button" class="btn-text danger" :disabled="isCharacterBusy" @click="deleteCharacter(selectedCharacter)">删除</button>
          <button type="button" class="btn-primary" :disabled="isCharacterBusy" @click="closeCharacterDetail">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showCharacterDialog" class="dialog-overlay" @click.self="closeCharacterDialog">
      <div class="dialog character-form-dialog">
        <h2>{{ editingCharacterId ? '编辑角色' : '新增角色' }}</h2>
        <form @submit.prevent="saveCharacter">
          <div v-if="characterFormError" class="form-error">{{ characterFormError }}</div>
          <div class="form-row">
            <div class="form-group">
              <label>姓名</label>
              <input v-model="characterForm.name" type="text" required :disabled="isSavingCharacter" />
            </div>
            <div class="form-group">
              <label>重要性</label>
              <select v-model="characterForm.importance" :disabled="isSavingCharacter">
                <option value="main">主角</option>
                <option value="major">主要角色</option>
                <option value="minor">次要角色</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>性别</label>
              <input v-model="characterForm.gender" type="text" :disabled="isSavingCharacter" />
            </div>
            <div class="form-group">
              <label>年龄</label>
              <input v-model="characterForm.age" type="text" :disabled="isSavingCharacter" />
            </div>
          </div>
          <div class="form-group">
            <label>身份简介</label>
            <textarea v-model="characterForm.identity_info" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>头像 URL</label>
            <input v-model="characterForm.avatar_url" type="url" :disabled="isSavingCharacter" />
          </div>
          <div class="form-group">
            <label>外貌身材</label>
            <textarea v-model="characterForm.appearance" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>性格特点</label>
            <textarea v-model="characterForm.personality" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>背景故事</label>
            <textarea v-model="characterForm.background" rows="4" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>人物关系</label>
            <textarea v-model="characterForm.relationships" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>能力特长</label>
            <textarea v-model="characterForm.abilities" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>角色成长线</label>
            <textarea v-model="characterForm.character_arc" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-group">
            <label>经典语录</label>
            <textarea v-model="characterForm.quotes" rows="3" :disabled="isSavingCharacter"></textarea>
          </div>
          <div class="form-actions">
            <button type="button" class="btn-secondary" :disabled="isSavingCharacter" @click="closeCharacterDialog">取消</button>
            <button type="submit" class="btn-primary" :disabled="isSavingCharacter">
              {{ isSavingCharacter ? '保存中...' : '保存' }}
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
import { aiApi, outlineApi } from '../../api'
import { useCharacterStore } from '../../stores/character'
import type { Character, CharacterCreate, CharacterUpdate, Outline } from '../../types'

const props = defineProps<{
  novelId: number
}>()

const characterStore = useCharacterStore()
const { characters, loading: isLoadingCharacters } = storeToRefs(characterStore)

type CharacterForm = {
  name: string
  gender: string
  age: string
  appearance: string
  identity_info: string
  personality: string
  background: string
  relationships: string
  abilities: string
  character_arc: string
  quotes: string
  avatar_url: string
  importance: string
}

const showCharacterDialog = ref(false)
const showCharacterDetail = ref(false)
const isGenerating = ref(false)
const isSavingCharacter = ref(false)
const isExpandingCharacter = ref(false)
const isGeneratingAvatar = ref(false)
const isBatchDeletingCharacters = ref(false)
const isBatchPolishingCharacters = ref(false)
const polishingCharacterId = ref<number | null>(null)
const batchPolishCurrent = ref(0)
const batchPolishTotal = ref(0)
const editingCharacterId = ref<number | null>(null)
const selectedCharacter = ref<Character | null>(null)
const selectedCharacterIds = ref<Set<number>>(new Set())
const characterError = ref('')
const characterFormError = ref('')
const streamedContent = ref('')
const outlines = ref<Outline[]>([])
const characterForm = ref<CharacterForm>(createCharacterForm())

const isCharacterBusy = computed(
  () => isSavingCharacter.value
    || isExpandingCharacter.value
    || isGeneratingAvatar.value
    || isBatchDeletingCharacters.value
    || isBatchPolishingCharacters.value
)
const selectedCharacterCount = computed(() => selectedCharacterIds.value.size)
const hasSelectedCharacters = computed(() => selectedCharacterCount.value > 0)
const isAllCharactersSelected = computed(
  () => characters.value.length > 0 && selectedCharacterCount.value === characters.value.length
)
const currentPolishingCharacter = computed(
  () => characters.value.find((character) => character.id === polishingCharacterId.value) || null
)
const batchPolishProgressText = computed(() => {
  if (!isBatchPolishingCharacters.value) return ''
  const characterName = currentPolishingCharacter.value?.name || '角色'
  return `正在润色 ${batchPolishCurrent.value}/${batchPolishTotal.value}：${characterName}`
})
const characterDetailSections = computed(() => {
  if (!selectedCharacter.value) return []

  return [
    { label: '外貌身材', value: selectedCharacter.value.appearance },
    { label: '性格特点', value: selectedCharacter.value.personality },
    { label: '背景故事', value: selectedCharacter.value.background },
    { label: '人物关系', value: selectedCharacter.value.relationships },
    { label: '能力特长', value: selectedCharacter.value.abilities },
    { label: '角色成长线', value: selectedCharacter.value.character_arc },
    { label: '经典语录', value: selectedCharacter.value.quotes },
  ]
})

onMounted(async () => {
  await loadOutlines()
  await loadCharacters()
})

function createCharacterForm(): CharacterForm {
  return {
    name: '',
    gender: '',
    age: '',
    appearance: '',
    identity_info: '',
    personality: '',
    background: '',
    relationships: '',
    abilities: '',
    character_arc: '',
    quotes: '',
    avatar_url: '',
    importance: 'minor',
  }
}

const loadOutlines = async () => {
  try {
    const response = await outlineApi.listByNovel(props.novelId)
    outlines.value = response.data
  } catch (error) {
    characterError.value = getErrorMessage(error, '加载大纲失败')
  }
}

const loadCharacters = async () => {
  characterError.value = ''

  try {
    await characterStore.loadCharacters(props.novelId)
    syncSelectedCharacter()
    syncSelectedCharacterIds()
  } catch (error) {
    characterError.value = getErrorMessage(error, '加载角色失败')
  }
}

const syncSelectedCharacter = () => {
  if (!selectedCharacter.value) return

  selectedCharacter.value = characters.value.find((character) => character.id === selectedCharacter.value?.id) || null
  if (!selectedCharacter.value) showCharacterDetail.value = false
}

const syncSelectedCharacterIds = () => {
  const existingIds = new Set(characters.value.map((character) => character.id))
  selectedCharacterIds.value = new Set(
    [...selectedCharacterIds.value].filter((characterId) => existingIds.has(characterId))
  )
}

const isCharacterSelected = (characterId: number) => selectedCharacterIds.value.has(characterId)

const toggleCharacterSelection = (characterId: number) => {
  const nextSelectedIds = new Set(selectedCharacterIds.value)
  if (nextSelectedIds.has(characterId)) {
    nextSelectedIds.delete(characterId)
  } else {
    nextSelectedIds.add(characterId)
  }
  selectedCharacterIds.value = nextSelectedIds
}

const toggleAllCharactersSelection = () => {
  selectedCharacterIds.value = isAllCharactersSelected.value
    ? new Set()
    : new Set(characters.value.map((character) => character.id))
}

const clearCharacterSelection = () => {
  selectedCharacterIds.value = new Set()
}

const openCharacterDialog = (character?: Character) => {
  characterFormError.value = ''
  characterError.value = ''

  if (character) {
    editingCharacterId.value = character.id
    characterForm.value = {
      name: character.name,
      gender: character.gender || '',
      age: character.age || '',
      appearance: character.appearance || '',
      identity_info: character.identity_info || '',
      personality: character.personality || '',
      background: character.background || '',
      relationships: character.relationships || '',
      abilities: character.abilities || '',
      character_arc: character.character_arc || '',
      quotes: character.quotes || '',
      avatar_url: character.avatar_url || '',
      importance: character.importance || 'minor',
    }
  } else {
    editingCharacterId.value = null
    characterForm.value = createCharacterForm()
  }

  showCharacterDialog.value = true
}

const closeCharacterDialog = () => {
  if (isSavingCharacter.value) return
  showCharacterDialog.value = false
  editingCharacterId.value = null
  characterFormError.value = ''
}

const buildCharacterPayload = (): CharacterUpdate => ({
  name: characterForm.value.name.trim(),
  gender: characterForm.value.gender.trim() || undefined,
  age: characterForm.value.age.trim() || undefined,
  appearance: characterForm.value.appearance.trim() || undefined,
  identity_info: characterForm.value.identity_info.trim() || undefined,
  personality: characterForm.value.personality.trim() || undefined,
  background: characterForm.value.background.trim() || undefined,
  relationships: characterForm.value.relationships.trim() || undefined,
  abilities: characterForm.value.abilities.trim() || undefined,
  character_arc: characterForm.value.character_arc.trim() || undefined,
  quotes: characterForm.value.quotes.trim() || undefined,
  avatar_url: characterForm.value.avatar_url.trim() || undefined,
  importance: characterForm.value.importance,
})

const saveCharacter = async () => {
  characterFormError.value = ''
  characterError.value = ''

  const payload = buildCharacterPayload()
  if (!payload.name) {
    characterFormError.value = '角色姓名不能为空'
    return
  }

  isSavingCharacter.value = true

  try {
    const savedCharacter = editingCharacterId.value
      ? await characterStore.updateCharacter(editingCharacterId.value, payload)
      : await characterStore.createCharacter({
          ...payload,
          novel_id: props.novelId,
          name: payload.name,
        } as CharacterCreate)

    selectedCharacter.value = savedCharacter
    showCharacterDetail.value = true
    showCharacterDialog.value = false
    editingCharacterId.value = null
  } catch (error) {
    characterFormError.value = getErrorMessage(error, '保存角色失败')
  } finally {
    isSavingCharacter.value = false
  }
}

const deleteCharacter = async (character: Character) => {
  const confirmed = window.confirm(`确定要删除角色《${character.name}》吗？此操作不可恢复。`)
  if (!confirmed) return

  characterError.value = ''

  try {
    await characterStore.deleteCharacter(character.id)
    selectedCharacterIds.value.delete(character.id)
    selectedCharacterIds.value = new Set(selectedCharacterIds.value)
    if (selectedCharacter.value?.id === character.id) {
      selectedCharacter.value = null
      showCharacterDetail.value = false
    }
  } catch (error) {
    characterError.value = getErrorMessage(error, '删除角色失败')
  }
}

const batchDeleteSelectedCharacters = async () => {
  if (!hasSelectedCharacters.value || isCharacterBusy.value) return

  const selectedIds = [...selectedCharacterIds.value]
  const confirmed = window.confirm(`确定要删除选中的 ${selectedIds.length} 个角色吗？此操作不可恢复。`)
  if (!confirmed) return

  characterError.value = ''
  isBatchDeletingCharacters.value = true

  try {
    for (const characterId of selectedIds) {
      await characterStore.deleteCharacter(characterId)
    }

    if (selectedCharacter.value && selectedIds.includes(selectedCharacter.value.id)) {
      selectedCharacter.value = null
      showCharacterDetail.value = false
    }
    clearCharacterSelection()
  } catch (error) {
    characterError.value = getErrorMessage(error, '批量删除角色失败')
  } finally {
    isBatchDeletingCharacters.value = false
    syncSelectedCharacterIds()
  }
}

const polishSingleCharacter = (character: Character, currentIndex: number, totalCount: number) => new Promise<void>((resolve, reject) => {
  batchPolishCurrent.value = currentIndex
  batchPolishTotal.value = totalCount
  polishingCharacterId.value = character.id
  streamedContent.value = ''

  aiApi.polishCharacterStream(
    {
      character_id: character.id,
      novel_id: props.novelId,
    },
    (chunk) => {
      streamedContent.value += chunk
    },
    async () => {
      await loadCharacters()
      resolve()
    },
    (error) => {
      reject(new Error(error))
    }
  ).catch(reject)
})

const batchPolishSelectedCharacters = async () => {
  if (!hasSelectedCharacters.value || isGenerating.value || isCharacterBusy.value) return

  const selectedIds = [...selectedCharacterIds.value]
  const selectedCharacters = selectedIds
    .map((characterId) => characters.value.find((character) => character.id === characterId))
    .filter((character): character is Character => Boolean(character))

  if (!selectedCharacters.length) return

  characterError.value = ''
  isBatchPolishingCharacters.value = true

  try {
    for (const [index, character] of selectedCharacters.entries()) {
      await polishSingleCharacter(character, index + 1, selectedCharacters.length)
    }

    characterError.value = `已完成 ${selectedCharacters.length} 个角色润色`
    clearCharacterSelection()
  } catch (error) {
    characterError.value = getErrorMessage(error, '批量润色角色失败')
  } finally {
    isBatchPolishingCharacters.value = false
    polishingCharacterId.value = null
    batchPolishCurrent.value = 0
    batchPolishTotal.value = 0
    streamedContent.value = ''
    await loadCharacters()
  }
}

const expandSelectedCharacter = async () => {
  if (!selectedCharacter.value || isCharacterBusy.value) return

  characterError.value = ''
  streamedContent.value = ''
  isExpandingCharacter.value = true

  try {
    await aiApi.expandCharacterStream(
      {
        character_id: selectedCharacter.value.id,
        novel_id: props.novelId,
      },
      (chunk) => {
        streamedContent.value += chunk
      },
      async () => {
        isExpandingCharacter.value = false
        await loadCharacters()
        streamedContent.value = ''
      },
      (error) => {
        isExpandingCharacter.value = false
        characterError.value = `扩展角色失败：${error}`
      }
    )
  } catch (error) {
    isExpandingCharacter.value = false
    characterError.value = getErrorMessage(error, '扩展角色失败')
  }
}

const generateSelectedCharacterAvatar = async () => {
  if (!selectedCharacter.value || isCharacterBusy.value) return

  characterError.value = ''
  isGeneratingAvatar.value = true

  try {
    await aiApi.generateCharacterImage({ character_id: selectedCharacter.value.id })
    await loadCharacters()
  } catch (error) {
    characterError.value = getErrorMessage(error, '生成头像失败')
  } finally {
    isGeneratingAvatar.value = false
  }
}

const generateCharacters = async () => {
  const outlineText = formatOutlinesForPrompt()
  characterError.value = ''

  if (!outlineText) {
    characterError.value = '请先生成或新增大纲'
    return
  }

  isGenerating.value = true
  streamedContent.value = ''

  try {
    await aiApi.generateCharactersStream(
      {
        novel_id: props.novelId,
        outline_text: outlineText,
        character_count: 12,
      },
      (chunk) => {
        streamedContent.value += chunk
      },
      async (result) => {
        isGenerating.value = false
        await loadCharacters()
        characterError.value = `成功生成 ${result.characters_count} 个角色`
        streamedContent.value = ''
      },
      (error) => {
        isGenerating.value = false
        characterError.value = `生成角色失败：${error}`
      }
    )
  } catch (error) {
    isGenerating.value = false
    characterError.value = getErrorMessage(error, '生成角色失败')
  }
}

const selectCharacter = (char: Character) => {
  selectedCharacter.value = char
  characterError.value = ''
  showCharacterDetail.value = true
}

const closeCharacterDetail = () => {
  if (isCharacterBusy.value) return
  showCharacterDetail.value = false
  selectedCharacter.value = null
  streamedContent.value = ''
}

const formatOutlinesForPrompt = () => outlines.value
  .map((outline) => {
    const position = [
      outline.volume_number ? `第${outline.volume_number}卷` : '',
      outline.chapter_number ? `第${outline.chapter_number}章` : '',
    ].filter(Boolean).join(' ')

    return [
      `## ${position ? `${position}：` : ''}${outline.title}`,
      outline.plot_summary ? `情节梗概：${outline.plot_summary}` : '',
      outline.key_events ? `关键事件：${outline.key_events}` : '',
      outline.characters_involved ? `涉及角色：${outline.characters_involved}` : '',
    ].filter(Boolean).join('\n')
  })
  .join('\n\n')

const getImportanceLabel = (importance: string) => {
  const importanceMap: Record<string, string> = {
    main: '主角',
    major: '主要角色',
    minor: '次要角色',
  }

  return importanceMap[importance] || importance || '角色'
}

const getCharacterInitial = (character: Character) => character.name.trim().charAt(0) || '角'

const formatCharacterMeta = (character: Character) => {
  const meta = [character.gender, character.age].filter(Boolean)
  return meta.length ? meta.join(' · ') : '未填写性别年龄'
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
  background: var(--card-bg);
  border-radius: 8px;
}

.tab-header,
.dialog-title-row,
.char-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tab-header {
  margin-bottom: 20px;
}

.character-actions-top,
.empty-actions,
.form-actions,
.character-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
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

.batch-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.batch-toolbar span {
  color: var(--text-secondary);
  font-weight: 500;
}

.batch-progress {
  margin-bottom: 16px;
  padding: 16px;
  background: var(--warning-bg);
  border: 1px solid var(--warning-border);
  border-radius: 8px;
}

.batch-progress strong {
  display: block;
  margin-bottom: 10px;
  color: var(--warning-color);
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.character-card {
  position: relative;
  padding: 44px 15px 15px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}

.character-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-soft);
}

.character-card.selected {
  border-color: var(--success-color);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--success-color) 16%, transparent);
}

.character-card.polishing {
  background: var(--warning-bg);
  border-color: var(--warning-color);
}

.character-select {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
}

.character-select input {
  width: 16px;
  height: 16px;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  margin-bottom: 10px;
  overflow: hidden;
  background: var(--disabled-bg);
  border-radius: 50%;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: var(--text-muted);
  font-size: 32px;
}

.char-title-row h3 {
  margin: 0;
}

.char-meta,
.char-intro {
  color: var(--text-secondary);
  font-size: 14px;
}

.char-meta {
  margin: 6px 0;
}

.char-intro {
  margin: 10px 0;
}

.importance-badge,
.badge-detailed {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 12px;
}

.importance-badge {
  color: var(--info-color);
  background: var(--info-bg);
  white-space: nowrap;
}

.badge-detailed {
  color: white;
  background: var(--success-color);
  border-radius: 3px;
}

.generating {
  padding: 30px;
  text-align: center;
}

.compact-generating {
  margin: 16px 0;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.generating-content {
  max-width: 800px;
  margin: 0 auto;
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
  background: var(--card-bg);
  border-radius: 8px;
}

.character-detail-dialog,
.character-form-dialog {
  width: 760px;
  max-height: 90vh;
  overflow-y: auto;
}

.dialog h2 {
  margin: 0 0 20px;
}

.character-detail-header {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--panel-bg-soft);
  border-radius: 8px;
}

.detail-avatar {
  flex: 0 0 auto;
  margin-bottom: 0;
}

.character-detail-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.character-detail-section {
  padding: 14px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.character-detail-section label,
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 600;
}

.character-detail-section p {
  margin: 0;
  color: var(--text-primary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.updated-at {
  margin: 12px 0 0;
  color: var(--text-muted);
  font-size: 12px;
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
  border: 1px solid var(--border-color);
  border-radius: 5px;
  box-sizing: border-box;
}

.form-actions {
  justify-content: flex-end;
  margin-top: 25px;
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
  color: var(--disabled-text);
  cursor: not-allowed;
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

.btn-primary:disabled,
.btn-secondary:disabled {
  background: var(--disabled-bg);
  cursor: not-allowed;
}
</style>
