<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { mealsApiListCamps, mealsApiCreateCamp, type CampSchema } from '../client'

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
      <h2>Your Camps</h2>
      <button class="btn btn-primary" @click="showCreateModal = true">+ Create Camp</button>
    </div>

    <div v-if="camps.length === 0">
      <p class="text-mute">You don't have any camps yet. Start by creating one!</p>
    </div>
    
    <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
      <div v-for="camp in camps" :key="camp.id as string" class="card">
        <h3>{{ camp.name }}</h3>
        <p style="margin-bottom: 1rem; color: var(--color-text-mute)">
          {{ camp.start_date }} to {{ camp.end_date }} • {{ camp.default_people_count }} people
        </p>
        <button class="btn btn-secondary" @click="router.push(`/camps/${camp.id}`)">Open Planner</button>
      </div>
    </div>

    <!-- Modal overlay simple implementation -->
    <div v-if="showCreateModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center;">
      <div class="card" style="width: 100%; max-width: 500px;">
        <h3>Create New Camp</h3>
        <div class="flex-col gap-4" style="margin-top: 1rem;">
          <div>
            <label>Camp Name</label>
            <input class="input" v-model="newCamp.name" placeholder="Summer Camp 2026" />
          </div>
          <div>
            <label>Default People Count</label>
            <input class="input" type="number" v-model="newCamp.default_people_count" />
          </div>
          <div class="flex gap-4">
            <div style="flex: 1">
              <label>Start Date</label>
              <input class="input" type="date" v-model="newCamp.start_date" />
            </div>
            <div style="flex: 1">
              <label>End Date</label>
              <input class="input" type="date" v-model="newCamp.end_date" />
            </div>
          </div>
          <div class="flex gap-2" style="margin-top: 1rem; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
            <button class="btn btn-primary" @click="handleCreateCamp">Create</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
