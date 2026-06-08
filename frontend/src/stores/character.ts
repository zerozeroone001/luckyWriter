import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Character } from '../types'
import { characterApi } from '../api'

export const useCharacterStore = defineStore('character', () => {
  const characters = ref<Character[]>([])
  const loading = ref(false)

  // 加载小说的所有角色
  const loadCharacters = async (novelId: number) => {
    loading.value = true
    try {
      const response = await characterApi.listByNovel(novelId)
      characters.value = response.data
    } catch (error) {
      console.error('加载角色列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 创建角色
  const createCharacter = async (data: any) => {
    loading.value = true
    try {
      const response = await characterApi.create(data)
      characters.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('创建角色失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新角色
  const updateCharacter = async (id: number, data: any) => {
    loading.value = true
    try {
      const response = await characterApi.update(id, data)
      const index = characters.value.findIndex((c) => c.id === id)
      if (index !== -1) {
        characters.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('更新角色失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 删除角色
  const deleteCharacter = async (id: number) => {
    loading.value = true
    try {
      await characterApi.delete(id)
      characters.value = characters.value.filter((c) => c.id !== id)
    } catch (error) {
      console.error('删除角色失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  return {
    characters,
    loading,
    loadCharacters,
    createCharacter,
    updateCharacter,
    deleteCharacter,
  }
})
