<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
const route = useRoute()

const uid = route.params.uid as string
const token = route.params.token as string

const new_password = ref('')
const confirm_password = ref('')
const msg = ref({ type: '', text: '' })
const success = ref(false)

async function handleSubmit() {
  msg.value = { type: '', text: '' }
  if (new_password.value !== confirm_password.value) {
    msg.value = { type: 'danger', text: t('misc.error') }
    return
  }

  const formData = new FormData()
  formData.append('uid', uid)
  formData.append('token', token)
  formData.append('new_password', new_password.value)

  try {
    const res = await fetch('/api/auth/password-reset-confirm', {
      method: 'POST',
      body: formData
    })
    if (res.ok) {
      msg.value = { type: 'success', text: t('reset.success') }
      success.value = true
    } else {
      const err = await res.json()
      msg.value = { type: 'danger', text: err.detail || t('reset.error') }
    }
  } catch (err) {
    msg.value = { type: 'danger', text: String(err) }
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="card auth-card">
      <h2>{{ t('reset.title') }}</h2>

      <div v-if="!success">
        <form @submit.prevent="handleSubmit" class="flex-col gap-4">
          <div>
            <label>{{ t('reset.new_password') }}</label>
            <input class="input" v-model="new_password" type="password" required />
          </div>
          <div>
            <label>{{ t('reset.confirm_password') }}</label>
            <input class="input" v-model="confirm_password" type="password" required />
          </div>
          <div v-if="msg.text" :style="{ color: `var(--color-${msg.type})` }" class="text-center">
            {{ msg.text }}
          </div>
          <button class="btn btn-primary btn-block mt-4" type="submit">{{ t('reset.submit') }}</button>
        </form>
      </div>

      <div v-else class="flex-col gap-4 items-center">
        <div class="emoji-lg">✅</div>
        <p class="text-center text-mute">
          {{ msg.text }}
        </p>
        <RouterLink to="/login" class="btn btn-primary btn-block mt-4">{{ t('login.title') }}</RouterLink>
      </div>
    </div>
  </div>
</template>
