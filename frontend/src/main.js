import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import Dashboard from './views/Dashboard.vue'
import QueryEditor from './views/QueryEditor.vue'
import TableView from './views/TableView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/query', name: 'query', component: QueryEditor },
  { path: '/table/:schema/:name', name: 'table', component: TableView, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
