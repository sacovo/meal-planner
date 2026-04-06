<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

const props = defineProps<{
  collaborators: string[]
  ownerUsername: string
  currentUserUsername: string
}>()

const emit = defineEmits<{
  (e: 'invite', username: string): void
  (e: 'remove', username: string): void
}>()

const newUsername = ref('')

function handleInvite() {
  if (newUsername.value.trim()) {
    emit('invite', newUsername.value.trim())
    newUsername.value = ''
  }
}

const isOwner = computed(() => props.ownerUsername === props.currentUserUsername)
</script>

<template>
  <div class="collaborators-section flex-col gap-4">
    <h3 class="section-title">Camp Collaborators</h3>
    
    <div class="members-list flex-col gap-2">
      <div class="member-item flex justify-between items-center p-2 border rounded">
        <div class="flex items-center gap-2">
          <span class="user-icon">👑</span>
          <span class="username">{{ ownerUsername }}</span>
          <span class="badge owner-badge">{{ t('collab.owner') }}</span>
        </div>
        <span class="text-mute italic text-sm">—</span>
      </div>
      
      <div v-for="username in collaborators" :key="username" class="member-item flex justify-between items-center p-2 border rounded">
        <div class="flex items-center gap-2">
          <span class="user-icon">👤</span>
          <span class="username">{{ username }}</span>
        </div>
        
        <button 
          v-if="isOwner || username === currentUserUsername" 
          class="btn btn-sm btn-danger-outline" 
          @click="$emit('remove', username)"
        >
          {{ username === currentUserUsername ? t('collab.remove') : t('btn.remove') }}
        </button>
      </div>
    </div>
    
    <div v-if="isOwner" class="invite-form flex-col gap-2 mt-4">
      <label class="text-sm font-semibold">{{ t('collab.invite') }}</label>
      <div class="flex gap-2">
        <input 
          type="text" 
          class="input flex-1" 
          v-model="newUsername" 
          :placeholder="t('collab.username_placeholder')"
          @keyup.enter="handleInvite"
        />
        <button class="btn btn-primary" @click="handleInvite" :disabled="!newUsername.trim()">{{ t('collab.invite_btn') }}</button>
      </div>
      <p class="text-xs text-mute">Collaborators have full access to edit meals and shopping lists.</p>
    </div>
  </div>
</template>

<style scoped>
.collaborators-section {
  padding: 1rem;
  background: var(--color-bg-mute);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.section-title {
  margin-top: 0;
  font-size: 1.1rem;
}

.member-item {
  background: var(--color-bg-base);
  border-color: var(--color-border);
}

.user-icon {
  font-size: 1.1rem;
}

.username {
  font-weight: 500;
}

.badge {
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  text-transform: uppercase;
  font-weight: bold;
}

.owner-badge {
  background: #fef3c7;
  color: #92400e;
}

.btn-sm {
  padding: 0.2rem 0.5rem;
  font-size: 0.8rem;
}

.btn-danger-outline {
  background: transparent;
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.btn-danger-outline:hover {
  background: var(--color-danger);
  color: white;
}

.text-sm {
  font-size: 0.85rem;
}

.text-xs {
  font-size: 0.75rem;
}
</style>
