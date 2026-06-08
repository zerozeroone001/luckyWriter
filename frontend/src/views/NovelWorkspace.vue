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
  color: white;
  background: #2c3e50;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.nav-item {
  padding: 15px 20px;
  color: inherit;
  text-align: left;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.nav-item:hover {
  background: #34495e;
}

.nav-item.active {
  background: #3498db;
}

.btn-back {
  margin: 20px;
  padding: 10px;
  color: white;
  background: #95a5a6;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: #f5f5f5;
}
</style>
