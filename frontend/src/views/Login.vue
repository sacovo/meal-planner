<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const errorMsg = ref('')

async function handleLogin() {
  errorMsg.value = ''
  try {
    // The user's new Ninja API endpoint for login handles form data
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
      errorMsg.value = 'Invalid credentials'
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
      <h2 style="text-align: center; margin-bottom: 2rem;">Log In</h2>
      <form @submit.prevent="handleLogin" class="flex-col gap-4">
        <div>
          <label>Username</label>
          <input class="input" v-model="username" type="text" required />
        </div>
        <div>
          <label>Password</label>
          <input class="input" v-model="password" type="password" required />
        </div>
        <div v-if="errorMsg" style="color: var(--color-danger); text-align: center;">
          {{ errorMsg }}
        </div>
        <button class="btn btn-primary" type="submit" style="width: 100%; margin-top: 1rem;">Log In</button>
      </form>
    </div>
  </div>
</template>
