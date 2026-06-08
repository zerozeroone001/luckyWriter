import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/bookshelf',
    },
    {
      path: '/bookshelf',
      name: 'Bookshelf',
      component: () => import('../views/Bookshelf.vue'),
    },
    {
      path: '/novel/:id',
      name: 'NovelWorkspace',
      component: () => import('../views/NovelWorkspace.vue'),
    },
    {
      path: '/channels',
      name: 'Channels',
      component: () => import('../views/Channels.vue'),
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
    },
  ],
})

export default router
