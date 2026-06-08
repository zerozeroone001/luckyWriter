import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Novel } from '../types'
import { novelApi } from '../api'

export const useNovelStore = defineStore('novel', () => {
  const novels = ref<Novel[]>([])
  const currentNovel = ref<Novel | null>(null)
  const loading = ref(false)

  // 加载小说列表
  const loadNovels = async () => {
    loading.value = true
    try {
      const response = await novelApi.list()
      novels.value = response.data
    } catch (error) {
      console.error('加载小说列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 加载单个小说
  const loadNovel = async (id: number) => {
    loading.value = true
    try {
      const response = await novelApi.get(id)
      currentNovel.value = response.data
      return response.data
    } catch (error) {
      console.error('加载小说失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建小说
  const createNovel = async (data: any) => {
    loading.value = true
    try {
      const response = await novelApi.create(data)
      novels.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('创建小说失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新小说
  const updateNovel = async (id: number, data: any) => {
    loading.value = true
    try {
      const response = await novelApi.update(id, data)
      const index = novels.value.findIndex((n) => n.id === id)
      if (index !== -1) {
        novels.value[index] = response.data
      }
      if (currentNovel.value?.id === id) {
        currentNovel.value = response.data
      }
      return response.data
    } catch (error) {
      console.error('更新小说失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除小说
  const deleteNovel = async (id: number) => {
    loading.value = true
    try {
      await novelApi.delete(id)
      novels.value = novels.value.filter((n) => n.id !== id)
      if (currentNovel.value?.id === id) {
        currentNovel.value = null
      }
    } catch (error) {
      console.error('删除小说失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    novels,
    currentNovel,
    loading,
    loadNovels,
    loadNovel,
    createNovel,
    updateNovel,
    deleteNovel,
  }
})
