import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import Dashboard from './views/Dashboard.vue'
import QueryEditor from './views/QueryEditor.vue'
import TableView from './views/TableView.vue'
import ProductsView from './views/ProductsView.vue'
import ProjectsView from './views/ProjectsView.vue'
import RequirementsView from './views/RequirementsView.vue'
import DefectsView from './views/DefectsView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/query', name: 'query', component: QueryEditor },
  { path: '/table/:schema/:name', name: 'table', component: TableView, props: true },
  { path: '/products', name: 'products', component: ProductsView },
  { path: '/projects', name: 'projects', component: ProjectsView },
  { path: '/requirements', name: 'requirements', component: RequirementsView },
  { path: '/defects', name: 'defects', component: DefectsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
