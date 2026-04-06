import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/Dashboard.vue')
    },
    {
      path: '/camps/:id',
      name: 'camp-planner',
      component: () => import('../views/CampPlanner.vue')
    },
    {
      path: '/camps/:id/day/:date',
      name: 'day-detail',
      component: () => import('../views/DayDetail.vue')
    },
    {
      path: '/camps/:id/inventory',
      name: 'inventory',
      component: () => import('../views/Inventory.vue')
    },
    {
      path: '/share/:token',
      name: 'shared-shopping-list',
      component: () => import('../views/SharedShoppingList.vue')
    },
    {
      path: '/camps/:id/shopping-list',
      name: 'shopping-list',
      component: () => import('../views/ShoppingList.vue')
    },
    {
      path: '/recipes',
      name: 'recipes',
      component: () => import('../views/Recipes.vue')
    },
    {
      path: '/recipes/:id',
      name: 'recipe-detail',
      component: () => import('../views/RecipeDetail.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { doNotRedirectToLogin: true }
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/ForgotPassword.vue'),
      meta: { doNotRedirectToLogin: true }
    },
    {
      path: '/reset-password/:uid/:token',
      name: 'reset-password',
      component: () => import('../views/ResetPassword.vue'),
      meta: { doNotRedirectToLogin: true }
    },
    {
      path: '/account',
      name: 'account',
      component: () => import('../views/Account.vue')
    }
  ]
})

export default router
