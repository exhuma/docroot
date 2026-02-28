import { createRouter, createWebHistory } from 'vue-router'
import DocsPage from '@/pages/DocsPage.vue'
import NamespaceList from '@/pages/NamespaceList.vue'
import ProjectList from '@/pages/ProjectList.vue'
import VersionList from '@/pages/VersionList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: NamespaceList,
    },
    {
      path: '/:namespace',
      component: ProjectList,
    },
    {
      path: '/:namespace/:project',
      component: VersionList,
    },
    {
      path: '/:namespace/:project/docs/:version/:locale',
      component: DocsPage,
    },
  ],
})

export default router
