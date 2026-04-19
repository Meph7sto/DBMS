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
import TestCasesView from './views/TestCasesView.vue'
import MilestonesView from './views/MilestonesView.vue'
import BranchesView from './views/BranchesView.vue'
import CommentsView from './views/CommentsView.vue'
import AuditLogsView from './views/AuditLogsView.vue'
import PerformanceLab from './views/PerformanceLab.vue'
import ComplexQueriesView from './views/ComplexQueriesView.vue'
import TestValidationView from './views/TestValidationView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/query', name: 'query', component: QueryEditor },
  { path: '/table/:schema/:name', name: 'table', component: TableView, props: true },
  { path: '/products', name: 'products', component: ProductsView },
  { path: '/projects', name: 'projects', component: ProjectsView },
  { path: '/requirements', name: 'requirements', component: RequirementsView },
  { path: '/defects', name: 'defects', component: DefectsView },
  { path: '/test-cases', name: 'test-cases', component: TestCasesView },
  { path: '/milestones', name: 'milestones', component: MilestonesView },
  { path: '/branches', name: 'branches', component: BranchesView },
  { path: '/comments', name: 'comments', component: CommentsView },
  { path: '/audit-logs', name: 'audit-logs', component: AuditLogsView },
  { path: '/complex-queries', name: 'complex-queries', component: ComplexQueriesView },
  { path: '/performance-lab', name: 'performance-lab', component: PerformanceLab },
  { path: '/test-validation', name: 'test-validation', component: TestValidationView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
