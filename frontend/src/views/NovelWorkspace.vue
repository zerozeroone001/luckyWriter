<template>
  <div class="workspace">
    <aside class="sidebar">
      <nav class="nav-menu">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="nav-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </nav>
      <button class="btn-back" type="button" @click="goBack">返回书架</button>
    </aside>

    <main class="content">
      <component :is="activePageComponent" :novel-id="novelId" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NovelInfoPage from './workspace/NovelInfoPage.vue'
import OutlinePage from './workspace/OutlinePage.vue'
import CharactersPage from './workspace/CharactersPage.vue'
import ChaptersPage from './workspace/ChaptersPage.vue'

type WorkspaceTabKey = 'info' | 'outline' | 'characters' | 'chapters'

const route = useRoute()
const router = useRouter()
const novelId = computed(() => Number(route.params.id))
const activeTab = ref<WorkspaceTabKey>('info')

const tabs: Array<{ key: WorkspaceTabKey; label: string }> = [
  { key: 'info', label: '小说信息' },
  { key: 'outline', label: '剧情大纲' },
  { key: 'characters', label: '角色卡' },
  { key: 'chapters', label: '章节目录' },
]

const pageComponents = {
  info: NovelInfoPage,
  outline: OutlinePage,
  characters: CharactersPage,
  chapters: ChaptersPage,
}

const activePageComponent = computed(() => pageComponents[activeTab.value])

const goBack = () => {
  router.push('/bookshelf')
}
</script>

<style scoped>
.workspace {
  display: flex;
  height: 100vh;
}

.sidebar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 200px;
  color: var(--text-primary);
  background: var(--panel-bg);
  border-right: 1px solid var(--border-color);
  box-shadow: 1px 0 18px rgba(31, 41, 55, 0.05);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.nav-item {
  margin: 4px 12px;
  padding: 14px 16px;
  color: var(--text-secondary);
  text-align: left;
  background: transparent;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.nav-item:hover {
  color: var(--theme-color);
  background: var(--theme-color-soft);
}

.nav-item.active {
  color: var(--theme-color);
  background: var(--theme-color-soft);
  font-weight: 700;
}

.btn-back {
  margin: 20px;
  padding: 10px;
  color: var(--text-secondary);
  background: var(--panel-bg-soft);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
}

.btn-back:hover {
  color: var(--theme-color);
  border-color: var(--theme-color-border);
}

.content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: var(--app-bg);
}
</style>
