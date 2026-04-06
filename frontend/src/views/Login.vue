<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)

    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]') as HTMLInputElement)?.value || ''
      },
      body: formData
    })
    
    if (!res.ok) {
      errorMsg.value = t('login.error')
    } else {
      const next = route.query.next as string
      router.push(next || '/')
    }
  } catch (err) {
    errorMsg.value = String(err)
  }
}
</script>

<template>
  <div class="flex items-center" style="justify-content: center; min-height: 50vh;">
    <div class="card" style="width: 100%; max-width: 400px;">
      <h2 style="text-align: center; margin-bottom: 2rem;">{{ t('login.title') }}</h2>
      <form @submit.prevent="handleLogin" class="flex-col gap-4">
        <div>
          <label>{{ t('login.username') }}</label>
          <input class="input" v-model="username" type="text" required />
        </div>
        <div>
          <label>{{ t('login.password') }}</label>
          <input class="input" v-model="password" type="password" required />
        </div>
        <div v-if="errorMsg" style="color: var(--color-danger); text-align: center;">
          {{ errorMsg }}
        </div>
        <button class="btn btn-primary" type="submit" style="width: 100%; margin-top: 1rem;">{{ t('login.submit') }}</button>
        <div style="text-align: center; margin-top: 1rem;">
          <RouterLink to="/forgot-password" style="font-size: 0.875rem; color: var(--color-text-mute);">{{ t('login.forgot_password') }}</RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>
