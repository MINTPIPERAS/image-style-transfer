import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'
import AboutPage from '../views/AboutPage.vue'
import ToolPage from '../views/ToolPage.vue'

const routes = [
  { path: '/', name: 'Home', component: HomePage },
  { path: '/about', name: 'About', component: AboutPage },
  { path: '/tool', name: 'Tool', component: ToolPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
