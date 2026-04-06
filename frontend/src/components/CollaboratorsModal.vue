<script setup lang="ts">
import CampCollaborators from './CampCollaborators.vue'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

defineProps<{
  show: boolean
  collaborators: string[]
  ownerUsername: string
  currentUserUsername: string
}>()

defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'invite', username: string): void
  (e: 'remove', username: string): void
}>()
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click="$emit('update:show', false)">
    <div class="modal" @click.stop>
      <div class="flex justify-between items-center mb-4">
        <h3 class="modal-title m-0">{{ t('collab.title') }}</h3>
        <button class="btn-close" @click="$emit('update:show', false)">×</button>
      </div>
      
      <div class="modal-body p-0">
        <CampCollaborators 
          :collaborators="collaborators" 
          :owner-username="ownerUsername"
          :current-user-username="currentUserUsername"
          @invite="$emit('invite', $event)"
          @remove="$emit('remove', $event)"
          class="in-modal"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-title {
  margin: 0;
}

.modal-body {
  margin-top: 0.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--color-text-mute);
  line-height: 1;
  padding: 0;
}

.btn-close:hover {
  color: var(--color-text-main);
}

:deep(.in-modal) {
  padding: 0;
  background: transparent;
  border: none;
}

:deep(.in-modal .section-title) {
  display: none;
}
</style>
