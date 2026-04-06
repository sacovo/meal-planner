<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

const email = ref('')
const msg = ref({ type: '', text: '' })
const submitted = ref(false)

async function handleSubmit() {
  msg.value = { type: '', text: '' }
  const formData = new FormData()
  formData.append('email', email.value)

  try {
    const res = await fetch('/api/auth/password-reset-request', {
      method: 'POST',
      body: formData
    })
    if (res.ok) {
      msg.value = { type: 'success', text: t('forgot.success') }
      submitted.value = true
    } else {
      msg.value = { type: 'danger', text: t('misc.error') }
    }
  } catch (err) {
    msg.value = { type: 'danger', text: String(err) }
  }
}
</script>

<template>
  <div class="flex items-center justify-center" style="min-height: 50vh;">
    <div class="card" style="width: 100%; max-width: 400px;">
      <h2 style="text-align: center; margin-bottom: 2rem;">{{ t('forgot.title') }}</h2>
      
      <div v-if="!submitted">
        <form @submit.prevent="handleSubmit" class="flex-col gap-4">
          <div>
            <label>{{ t('forgot.email') }}</label>
            <input class="input" v-model="email" type="email" required />
          </div>
          <div v-if="msg.text" :style="{ color: `var(--color-${msg.type})` }" style="text-align: center;">
            {{ msg.text }}
          </div>
          <button class="btn btn-primary" type="submit" style="width: 100%; margin-top: 1rem;">{{ t('forgot.submit') }}</button>
        </form>
      </div>
      
      <div v-else class="flex-col gap-4 items-center">
        <div style="font-size: 3rem;">✉️</div>
        <p style="text-align: center; color: var(--color-text-mute);">
          {{ msg.text }}
        </p>
        <RouterLink to="/login" class="btn btn-secondary" style="width: 100%; margin-top: 1rem;">{{ t('forgot.back_to_login') }}</RouterLink>
      </div>
    </div>
  </div>
</template>
