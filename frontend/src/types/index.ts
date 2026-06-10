// 小说相关类型
export interface Novel {
  id: number
  title: string
  author: string
  genre?: string
  target_words: number
  current_words: number
  cover_image?: string
  synopsis?: string
  style_prompt?: string
  status: string
  created_at: string
  updated_at: string
}

export interface NovelCreate {
  title: string
  author?: string
  genre?: string
  target_words?: number
  synopsis?: string
}

export interface NovelStats {
  novel_id: number
  chapter_count: number
  total_words: number
  target_words: number
  progress: number
}

// 大纲相关类型
export interface Outline {
  id: number
  novel_id: number
  volume_number?: number
  chapter_number?: number
  title: string
  plot_summary?: string
  key_events?: string
  characters_involved?: string
  outline_type: string
  created_at: string
  updated_at: string
}

export interface OutlineCreate {
  novel_id: number
  volume_number?: number
  chapter_number?: number
  title: string
  plot_summary?: string
  key_events?: string
  characters_involved?: string
  outline_type?: string
}

export interface OutlineUpdate {
  volume_number?: number
  chapter_number?: number
  title?: string
  plot_summary?: string
  key_events?: string
  characters_involved?: string
  outline_type?: string
}

// 章节相关类型
export interface Chapter {
  id: number
  novel_id: number
  volume_number: number
  chapter_number: number
  title: string
  content?: string
  word_count: number
  status: string
  created_at: string
  updated_at: string
}

export interface ChapterCreate {
  novel_id: number
  volume_number?: number
  chapter_number: number
  title: string
  content?: string
}

export interface ChapterUpdate {
  title?: string
  content?: string
  status?: string
}

// 角色相关类型
export interface Character {
  id: number
  novel_id: number
  name: string
  gender?: string
  age?: string
  appearance?: string
  identity_info?: string
  personality?: string
  background?: string
  relationships?: string
  abilities?: string
  character_arc?: string
  quotes?: string
  avatar_url?: string
  importance: string
  is_detailed: boolean
  created_at: string
  updated_at: string
}

export interface CharacterCreate {
  novel_id: number
  name: string
  gender?: string
  age?: string
  appearance?: string
  identity_info?: string
  personality?: string
  background?: string
  relationships?: string
  abilities?: string
  character_arc?: string
  quotes?: string
  avatar_url?: string
  importance?: string
}

export interface CharacterUpdate {
  name?: string
  gender?: string
  age?: string
  appearance?: string
  identity_info?: string
  personality?: string
  background?: string
  relationships?: string
  abilities?: string
  character_arc?: string
  quotes?: string
  avatar_url?: string
  importance?: string
}

// AI渠道相关类型
export interface AIChannel {
  id: number
  name: string
  provider: string
  base_url?: string
  is_enabled: boolean
  created_at: string
  updated_at: string
  model_count: number
}

export interface AIChannelCreate {
  name: string
  provider: string
  api_key?: string
  base_url?: string
}

export interface AIChannelUpdate {
  name?: string
  api_key?: string
  base_url?: string
  is_enabled?: boolean
}

// AI模型相关类型
export interface AIModel {
  id: number
  channel_id: number
  model_name: string
  model_id: string
  is_enabled: boolean
  temperature: number
  cost_per_1k_input_tokens: number
  cost_per_1k_output_tokens: number
  response_time_ms?: number
  last_test_at?: string
  created_at: string
  updated_at: string
}

export interface AIModelCreate {
  channel_id: number
  model_name: string
  model_id: string
  temperature?: number
  cost_per_1k_input_tokens?: number
  cost_per_1k_output_tokens?: number
}

export interface AIModelUpdate {
  is_enabled?: boolean
  temperature?: number
  cost_per_1k_input_tokens?: number
  cost_per_1k_output_tokens?: number
}

export interface AvailableModel {
  id: string
  name: string
  description?: string
}

export interface GenerationLogsQuery {
  limit?: number
  offset?: number
  generation_type?: string
  status?: string
}

export interface AIGenerationLog {
  id: number
  novel_id?: number
  generation_type: string
  api_endpoint?: string
  channel_name?: string
  channel_provider?: string
  model_name?: string
  model_identifier?: string
  request_params?: string
  input_tokens?: number
  output_tokens?: number
  cost?: number
  duration_seconds?: number
  status?: string
  error_message?: string
  created_at: string
}

// AI生成相关类型
export interface PlanNovelRequest {
  novel_id: number
  target_words?: number
  target_chapters?: number
  target_volumes?: number
  genre?: string
  style_requirements?: string
}

export interface GenerateVolumeChaptersRequest {
  novel_id: number
  outline_id: number
  target_chapters?: number
  start_chapter_number?: number
  style_requirements?: string
  replace_existing?: boolean
}

export interface GenerateCharactersRequest {
  novel_id: number
  outline_text: string
  character_count?: number
}

export interface ExpandCharacterRequest {
  character_id: number
  novel_id: number
}

export interface PolishCharacterRequest {
  character_id: number
  novel_id: number
}

export interface PolishOutlineRequest {
  novel_id: number
  outline_id: number
  polish_requirements?: string
  save?: boolean
}

export interface GenerateChapterContentRequest {
  novel_id: number
  outline_id: number
  chapter_id?: number
  target_words?: number
  writing_requirements?: string
  save?: boolean
}

export interface RewriteChapterContentRequest {
  novel_id: number
  chapter_id: number
  rewrite_requirements?: string
  save?: boolean
}

export interface RewriteChapterSelectionRequest {
  novel_id: number
  chapter_id: number
  selected_text: string
  rewrite_requirements?: string
  context_before?: string
  context_after?: string
}

export interface PolishChapterContentRequest {
  novel_id: number
  chapter_id: number
  style_requirements?: string
  save?: boolean
}

export interface InspirationChatRequest {
  messages: Array<{ role: string; content: string }>
}

export interface GenerateTitleFromConversationRequest {
  conversation: string
  genre: string
}

export interface GenerateSynopsisFromConversationRequest {
  title: string
  genre: string
  conversation: string
}

export interface GenerateStylePromptFromConversationRequest {
  title: string
  genre: string
  synopsis: string
  conversation: string
}

export interface GenerateOutlineFromConversationRequest {
  novel_id: number
  conversation: string
}

export interface GenerateCharacterImageRequest {
  character_id: number
  style?: string
}

// SSE流式响应类型
export interface SSEChunkEvent {
  type: 'chunk'
  content: string
}

export interface SSEDoneEvent {
  type: 'done'
  result: any
}

export interface SSEErrorEvent {
  type: 'error'
  message: string
}

export type SSEEvent = SSEChunkEvent | SSEDoneEvent | SSEErrorEvent
