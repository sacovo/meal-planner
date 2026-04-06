<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mealsApiCampsListCamps, mealsApiCampsCreateCamp, type CampSchema } from '../client'
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
  const { data } = await mealsApiCampsListCamps()
  if (data) camps.value = data
}

async function handleCreateCamp() {
  if (!newCamp.value.name || !newCamp.value.start_date || !newCamp.value.end_date) return
  const { data } = await mealsApiCampsCreateCamp({ body: newCamp.value })
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
    <div class="page-header mb-8">
      <h2>{{ t('dashboard.title') }}</h2>
      <button class="btn btn-primary" @click="showCreateModal = true">{{ t('dashboard.create_camp') }}</button>
    </div>

    <div v-if="camps.length === 0">
      <p class="text-mute">{{ t('dashboard.no_camps') }}</p>
    </div>

    <div class="grid-cards">
      <div v-for="camp in camps" :key="camp.id as string" class="card">
        <h3>{{ camp.name }}</h3>
        <p class="text-mute mb-4">
          {{ camp.start_date }} {{ t('dashboard.to') }} {{ camp.end_date }} • {{ camp.default_people_count }} {{ t('misc.people') }}
        </p>
        <button class="btn btn-secondary" @click="router.push(`/camps/${camp.id}`)">{{ t('dashboard.open_planner') }}</button>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showCreateModal" class="modal-backdrop">
      <div class="modal">
        <h3>{{ t('camp.create_title') }}</h3>
        <div class="flex-col gap-4 mt-4">
          <div>
            <label>{{ t('camp.name_label') }}</label>
            <input class="input" v-model="newCamp.name" :placeholder="t('camp.name_placeholder')" />
          </div>
          <div>
            <label>{{ t('camp.people_count_label') }}</label>
            <input class="input" type="number" v-model="newCamp.default_people_count" />
          </div>
          <div class="flex gap-4">
            <div class="flex-1">
              <label>{{ t('camp.start_date_label') }}</label>
              <input class="input" type="date" v-model="newCamp.start_date" />
            </div>
            <div class="flex-1">
              <label>{{ t('camp.end_date_label') }}</label>
              <input class="input" type="date" v-model="newCamp.end_date" />
            </div>
          </div>
          <div class="flex gap-2 justify-end mt-4">
            <button class="btn btn-secondary" @click="showCreateModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleCreateCamp">{{ t('btn.create') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
