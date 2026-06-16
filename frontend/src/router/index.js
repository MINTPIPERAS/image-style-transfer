import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'
import AboutPage from '../views/AboutPage.vue'
import ToolPage from '../views/ToolPage.vue'
import LoginPage from '../views/LoginPage.vue'
import ProfilePage from '../views/ProfilePage.vue'
import HistoryPage from '../views/HistoryPage.vue'

const routes = [
  { path: '/', name: 'Home', component: HomePage },
  { path: '/about', name: 'About', component: AboutPage },
  { path: '/tool', name: 'Tool', component: ToolPage },
  { path: '/login', name: 'Login', component: LoginPage },
  { path: '/profile', name: 'Profile', component: ProfilePage },
  { path: '/history', name: 'History', component: HistoryPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
