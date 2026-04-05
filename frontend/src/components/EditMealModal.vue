<script setup lang="ts">
import { ref, watch } from 'vue'
import type { CampMealSchema, DietaryPreferenceSchema } from '../client'

const props = defineProps<{
  show: boolean
  meal: CampMealSchema | null
  preferences: DietaryPreferenceSchema[]
  recipeName: string
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'save', data: { overridePeopleCount: number | null, preferenceId: number | null }): void
}>()

const localPeopleCount = ref<number | null>(null)
const localPreferenceId = ref<number | null>(null)

watch(() => props.meal, (newMeal) => {
  if (newMeal) {
    localPeopleCount.value = newMeal.override_people_count || null
    localPreferenceId.value = newMeal.serves_preference?.id || null
  }
}, { immediate: true })
</script>

<template>
  <div v-if="show && meal" class="modal-backdrop" @click="$emit('update:show', false)">
    <div class="modal" @click.stop>
      <h3 class="modal-title">Edit Assigned Meal</h3>
      <p class="text-mute subtitle">Specify participant overrides or subgroups for {{ recipeName }}</p>
      
      <div class="flex-col gap-4 modal-body">
        <div class="form-group">
          <label class="label">Override People Count (Optional)</label>
          <input type="number" class="input" v-model="localPeopleCount" placeholder="Default from camp settings" />
        </div>
        <div class="form-group">
          <label class="label">Meal Target Subgroup (Optional)</label>
          <select class="input" v-model="localPreferenceId">
            <option :value="null">-- For Main Group --</option>
            <option v-for="pref in preferences" :key="pref.id" :value="pref.id">{{ pref.name }}</option>
          </select>
        </div>
        <div class="flex justify-end gap-2 footer">
          <button class="btn btn-secondary" @click="$emit('update:show', false)">Cancel</button>
          <button class="btn btn-primary" @click="$emit('save', { overridePeopleCount: localPeopleCount, preferenceId: localPreferenceId })">Save Variables</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-title {
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.modal-body {
  margin-top: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.footer {
  margin-top: 1rem;
}
</style>
