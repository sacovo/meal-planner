<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mealsApiListCamps, mealsApiCreateCamp, type CampSchema } from '../client'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
const router = useRouter()
const camps = ref<CampSchema[]>([])

const showCreateModal = ref(false)
const newCamp = ref({
  name: '',
  default_people_count: 50,
  start_date: '',
  end_date: ''
})

async function fetchCamps() {
  const { data } = await mealsApiListCamps()
  if (data) camps.value = data
}

async function handleCreateCamp() {
  if (!newCamp.value.name || !newCamp.value.start_date || !newCamp.value.end_date) return
  const { data } = await mealsApiCreateCamp({ body: newCamp.value })
  if (data) {
    camps.value.push(data)
    showCreateModal.value = false
    router.push(`/camps/${data.id}`)
  }
}

onMounted(fetchCamps)
</script>

<template>
  <div>
    <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
      <h2>{{ t('dashboard.title') }}</h2>
      <button class="btn btn-primary" @click="showCreateModal = true">{{ t('dashboard.create_camp') }}</button>
    </div>

    <div v-if="camps.length === 0">
      <p class="text-mute">{{ t('dashboard.no_camps') }}</p>
    </div>
    
    <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
      <div v-for="camp in camps" :key="camp.id as string" class="card">
        <h3>{{ camp.name }}</h3>
        <p style="margin-bottom: 1rem; color: var(--color-text-mute)">
          {{ camp.start_date }} {{ t('dashboard.to') }} {{ camp.end_date }} • {{ camp.default_people_count }} {{ t('misc.people') }}
        </p>
        <button class="btn btn-secondary" @click="router.push(`/camps/${camp.id}`)">{{ t('dashboard.open_planner') }}</button>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showCreateModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center;">
      <div class="card" style="width: 100%; max-width: 500px;">
        <h3>{{ t('camp.create_title') }}</h3>
        <div class="flex-col gap-4" style="margin-top: 1rem;">
          <div>
            <label>{{ t('camp.name_label') }}</label>
            <input class="input" v-model="newCamp.name" :placeholder="t('camp.name_placeholder')" />
          </div>
          <div>
            <label>{{ t('camp.people_count_label') }}</label>
            <input class="input" type="number" v-model="newCamp.default_people_count" />
          </div>
          <div class="flex gap-4">
            <div style="flex: 1">
              <label>{{ t('camp.start_date_label') }}</label>
              <input class="input" type="date" v-model="newCamp.start_date" />
            </div>
            <div style="flex: 1">
              <label>{{ t('camp.end_date_label') }}</label>
              <input class="input" type="date" v-model="newCamp.end_date" />
            </div>
          </div>
          <div class="flex gap-2" style="margin-top: 1rem; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showCreateModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleCreateCamp">{{ t('btn.create') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
