<template>
  <header class="top-nav">
    <div class="nav-inner container">
      <RouterLink class="brand" to="/">
        <span class="brand-dot"></span>
        DevFlow AI
      </RouterLink>
      <nav class="nav-links">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/workflow">流水线引擎</RouterLink>
      </nav>
      <div class="nav-actions">
        <RouterLink class="btn btn-primary" to="/workflow">立即体验</RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
