<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div>
    <nav class="navbar">
      <div class="container navbar-content">
        <h1 style="margin: 0; font-size: 1.25rem; color: var(--color-primary); display: flex; align-items: center; gap: 0.5rem">
          ⛺ Meal Planner
        </h1>
        <div class="flex gap-4">
          <RouterLink to="/" class="nav-link">Camps</RouterLink>
          <RouterLink to="/recipes" class="nav-link">Recipes</RouterLink>
        </div>
      </div>
    </nav>
    <main class="container page-container">
      <RouterView />
    </main>
  </div>
</template>
