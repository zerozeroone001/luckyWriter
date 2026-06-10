import api from './axios'
import type {
  Novel,
  NovelCreate,
  NovelStats,
  Outline,
  OutlineCreate,
  OutlineUpdate,
  Chapter,
  ChapterCreate,
  ChapterUpdate,
  Character,
  CharacterCreate,
  CharacterUpdate,
  AIChannel,
  AIChannelCreate,
  AIChannelUpdate,
  AIModel,
  AIModelCreate,
  AIModelUpdate,
  AvailableModel,
  GenerationLogsQuery,
  AIGenerationLog,
  PlanNovelRequest,
  GenerateVolumeChaptersRequest,
  GenerateCharactersRequest,
  ExpandCharacterRequest,
  PolishCharacterRequest,
  PolishOutlineRequest,
  GenerateChapterContentRequest,
  RewriteChapterContentRequest,
  RewriteChapterSelectionRequest,
  PolishChapterContentRequest,
  GenerateCharacterImageRequest,
  SSEEvent,
} from '../types'

// 小说API
export const novelApi = {
  // 创建小说
  create: (data: NovelCreate) => api.post<Novel>('/novels', data),

  // 获取小说列表
  list: () => api.get<Novel[]>('/novels'),

  // 获取小说详情
  get: (id: number) => api.get<Novel>(`/novels/${id}`),

  // 更新小说
  update: (id: number, data: Partial<NovelCreate>) =>
    api.put<Novel>(`/novels/${id}`, data),

  // 删除小说
  delete: (id: number) => api.delete(`/novels/${id}`),

  // 获取小说统计
  stats: (id: number) => api.get<NovelStats>(`/novels/${id}/stats`),
}

// 大纲API
export const outlineApi = {
  // 创建大纲项
  create: (data: OutlineCreate) => api.post<Outline>('/outlines', data),

  // 获取小说的所有大纲项
  listByNovel: (novelId: number) =>
    api.get<Outline[]>(`/outlines/novel/${novelId}`),

  // 更新大纲项
  update: (id: number, data: OutlineUpdate) =>
    api.put<Outline>(`/outlines/${id}`, data),

  // 删除大纲项
  delete: (id: number) => api.delete(`/outlines/${id}`),

  // 批量删除大纲项
  batchDelete: (outlineIds: number[]) =>
    api.post('/outlines/batch-delete', { outline_ids: outlineIds }),
}

// 章节API
export const chapterApi = {
  // 创建章节
  create: (data: ChapterCreate) => api.post<Chapter>('/chapters', data),

  // 获取小说的所有章节
  listByNovel: (novelId: number) =>
    api.get<Chapter[]>(`/chapters/novel/${novelId}`),

  // 获取章节详情
  get: (id: number) => api.get<Chapter>(`/chapters/${id}`),

  // 更新章节
  update: (id: number, data: ChapterUpdate) =>
    api.put<Chapter>(`/chapters/${id}`, data),

  // 删除章节
  delete: (id: number) => api.delete(`/chapters/${id}`),
}

// 角色API
export const characterApi = {
  // 创建角色
  create: (data: CharacterCreate) => api.post<Character>('/characters', data),

  // 获取小说的所有角色
  listByNovel: (novelId: number) =>
    api.get<Character[]>(`/characters/novel/${novelId}`),

  // 获取角色详情
  get: (id: number) => api.get<Character>(`/characters/${id}`),

  // 更新角色
  update: (id: number, data: CharacterUpdate) =>
    api.put<Character>(`/characters/${id}`, data),

  // 删除角色
  delete: (id: number) => api.delete(`/characters/${id}`),
}

// AI渠道API
export const channelApi = {
  // 创建AI渠道
  create: (data: AIChannelCreate) => api.post<AIChannel>('/channels', data),

  // 获取所有AI渠道
  list: () => api.get<AIChannel[]>('/channels'),

  // 获取AI渠道详情
  get: (id: number) => api.get<AIChannel>(`/channels/${id}`),

  // 更新AI渠道
  update: (id: number, data: AIChannelUpdate) =>
    api.put<AIChannel>(`/channels/${id}`, data),

  // 删除AI渠道
  delete: (id: number) => api.delete(`/channels/${id}`),

  // 获取渠道支持的模型列表
  getAvailableModels: (channelId: number) =>
    api.get<AvailableModel[]>(`/channels/${channelId}/available-models`),
}

// AI模型API
export const modelApi = {
  // 添加模型
  create: (data: AIModelCreate) => api.post<AIModel>('/channels/models', data),

  // 获取渠道的所有模型
  list: (channelId: number) => api.get<AIModel[]>(`/channels/${channelId}/models`),

  // 更新模型配置
  update: (modelId: number, data: AIModelUpdate) =>
    api.put<AIModel>(`/channels/models/${modelId}`, data),

  // 删除模型
  delete: (modelId: number) => api.delete(`/channels/models/${modelId}`),

  // 测试模型响应速度
  testSpeed: (modelId: number) =>
    api.post<{ model_id: number; response_time_ms: number; status: string }>(
      `/channels/models/${modelId}/test-speed`
    ),
}

export const logsApi = {
  // 查询 AI 生成调用日志
  list: (params?: GenerationLogsQuery) =>
    api.get<AIGenerationLog[]>('/logs/generation-logs', { params }),
}

const streamPost = async <TData>(
  path: string,
  data: TData,
  onChunk: (content: string) => void,
  onDone: (result: any) => void,
  onError: (error: string) => void
) => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('无法读取响应流')
    }

    let buffer = ''
    let completed = false

    const handleLine = (line: string) => {
      const trimmedLine = line.trim()
      if (!trimmedLine.startsWith('data: ')) return false

      const event: SSEEvent = JSON.parse(trimmedLine.slice(6))

      if (event.type === 'chunk') {
        onChunk(event.content)
        return false
      }

      if (event.type === 'done') {
        completed = true
        onDone(event.result)
        return true
      }

      if (event.type === 'error') {
        completed = true
        onError(event.message)
        return true
      }

      return false
    }

    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (handleLine(line)) return
      }
    }

    buffer += decoder.decode()
    if (buffer && handleLine(buffer)) return

    if (!completed) {
      onError('接口未返回完成事件')
    }
  } catch (error: any) {
    onError(error.message || '请求失败')
  }
}

// AI生成API（流式）
export const aiApi = {
  // 一键规划小说大纲（流式）
  planNovelStream: (
    data: PlanNovelRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/plan-novel/stream', data, onChunk, onDone, onError),

  // 根据卷级大纲生成节章大纲（流式）
  generateVolumeChaptersStream: (
    data: GenerateVolumeChaptersRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/generate-volume-chapters/stream', data, onChunk, onDone, onError),

  // 批量生成角色卡（流式）
  generateCharactersStream: async (
    data: GenerateCharactersRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ai/generate-characters/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const text = decoder.decode(value, { stream: true })
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            try {
              const event: SSEEvent = JSON.parse(jsonStr)

              if (event.type === 'chunk') {
                onChunk(event.content)
              } else if (event.type === 'done') {
                onDone(event.result)
              } else if (event.type === 'error') {
                onError(event.message)
              }
            } catch (e) {
              console.error('解析SSE事件失败:', e)
            }
          }
        }
      }
    } catch (error: any) {
      onError(error.message || '请求失败')
    }
  },

  // 扩展角色卡详情（流式）
  expandCharacterStream: async (
    data: ExpandCharacterRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ai/expand-character/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const text = decoder.decode(value, { stream: true })
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            try {
              const event: SSEEvent = JSON.parse(jsonStr)

              if (event.type === 'chunk') {
                onChunk(event.content)
              } else if (event.type === 'done') {
                onDone(event.result)
              } else if (event.type === 'error') {
                onError(event.message)
              }
            } catch (e) {
              console.error('解析SSE事件失败:', e)
            }
          }
        }
      }
    } catch (error: any) {
      onError(error.message || '请求失败')
    }
  },

  // 润色单个角色卡（流式）
  polishCharacterStream: async (
    data: PolishCharacterRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/ai/polish-character/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('无法读取响应流')
      }

      let buffer = ''
      let completed = false

      const handleLine = (line: string) => {
        const trimmedLine = line.trim()
        if (!trimmedLine.startsWith('data: ')) return false

        const jsonStr = trimmedLine.slice(6)
        const event: SSEEvent = JSON.parse(jsonStr)

        if (event.type === 'chunk') {
          onChunk(event.content)
          return false
        }

        if (event.type === 'done') {
          completed = true
          onDone(event.result)
          return true
        }

        if (event.type === 'error') {
          completed = true
          onError(event.message)
          return true
        }

        return false
      }

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (handleLine(line)) return
        }
      }

      buffer += decoder.decode()
      if (buffer && handleLine(buffer)) return

      if (!completed) {
        onError('润色接口未返回完成事件')
      }
    } catch (error: any) {
      onError(error.message || '请求失败')
    }
  },

  // 润色章节剧情大纲（流式）
  polishOutlineStream: (
    data: PolishOutlineRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/polish-outline/stream', data, onChunk, onDone, onError),

  // 根据大纲写作章节正文（流式）
  generateChapterContentStream: (
    data: GenerateChapterContentRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/generate-chapter-content/stream', data, onChunk, onDone, onError),

  // 重写章节正文（流式）
  rewriteChapterContentStream: (
    data: RewriteChapterContentRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/rewrite-chapter-content/stream', data, onChunk, onDone, onError),

  // 局部改写章节选区（流式）
  rewriteChapterSelectionStream: (
    data: RewriteChapterSelectionRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/rewrite-chapter-selection/stream', data, onChunk, onDone, onError),

  // 润色章节正文（流式）
  polishChapterContentStream: (
    data: PolishChapterContentRequest,
    onChunk: (content: string) => void,
    onDone: (result: any) => void,
    onError: (error: string) => void
  ) => streamPost('/ai/polish-chapter-content/stream', data, onChunk, onDone, onError),

  // 生成角色形象图片
  generateCharacterImage: (data: GenerateCharacterImageRequest) =>
    api.post('/ai/generate-character-image', data),
}
