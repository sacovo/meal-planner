<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  mealsApiInventoryGetInventoryStatus,
  mealsApiCampsGetCamp,
  mealsApiShoppingAddManualShoppingItem,
  mealsApiInventoryExportInventoryExcel,
  type InventoryStatusSchema,
  type CampSchema
} from '../client'
import { useI18n } from '../composables/useI18n'
import { useFileDownload } from '../composables/useFileDownload'

const route = useRoute()
const { t } = useI18n()
const { downloadBlob } = useFileDownload()

const campId = route.params.id as string
const inventory = ref<InventoryStatusSchema[]>([])
const camp = ref<CampSchema | null>(null)
const loading = ref(true)

const showAddModal = ref(false)
const selectedItem = ref<InventoryStatusSchema | null>(null)
const addAmount = ref(0)
const adding = ref(false)
const successMessage = ref('')

async function fetchData() {
  loading.value = true
  try {
    const [invRes, campRes] = await Promise.all([
      mealsApiInventoryGetInventoryStatus({ path: { camp_id: campId } }),
      mealsApiCampsGetCamp({ path: { camp_id: campId } })
    ])
    if (invRes.data) inventory.value = invRes.data
    if (campRes.data) camp.value = campRes.data
  } finally {
    loading.value = false
  }
}

function openAddModal(item: InventoryStatusSchema) {
  selectedItem.value = item
  addAmount.value = item.balance < 0 ? Math.abs(item.balance) : 1
  showAddModal.value = true
}

async function confirmAdd() {
  if (!selectedItem.value || addAmount.value <= 0) return
  adding.value = true
  try {
    await mealsApiShoppingAddManualShoppingItem({
      path: { camp_id: campId },
      body: {
        ingredient_id: selectedItem.value.ingredient_id as string,
        amount: addAmount.value,
        unit: selectedItem.value.unit
      }
    })
    successMessage.value = `Added ${addAmount.value} ${selectedItem.value.unit} ${selectedItem.value.ingredient_name} to the latest shopping list.`
    showAddModal.value = false
    setTimeout(() => { successMessage.value = '' }, 5000)
  } finally {
    adding.value = false
  }
}

async function exportExcel() {
  const res = await mealsApiInventoryExportInventoryExcel({
    path: { camp_id: campId },
    parseAs: 'blob'
  })
  if (res.data) {
    downloadBlob(res.data as unknown as Blob, `inventory_${camp.value?.name || 'camp'}.xlsx`)
  }
}

const categories = computed(() => {
  const cats = new Set(inventory.value.map(i => i.category))
  return Array.from(cats).sort()
})

function getItemsForCategory(cat: string) {
  return inventory.value.filter(i => i.category === cat)
}

function getBalanceColor(balance: number) {
  if (balance < 0) return 'var(--color-danger)'
  if (balance === 0) return 'var(--color-text-mute)'
  return 'var(--color-success)'
}

onMounted(fetchData)
</script>

<template>
  <div v-if="camp" class="flex-col gap-4">
    <div class="page-header card">
      <div>
        <RouterLink :to="`/camps/${campId}`" class="badge mb-2">{{ t('btn.back') }}</RouterLink>
        <h2 class="page-title">{{ t('inventory.title') }}: {{ camp.name }}</h2>
        <p class="text-mute">{{ t('inventory.description') }}</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="exportExcel">📥 {{ t('btn.export') || 'Export' }}</button>
        <button class="btn btn-secondary" @click="fetchData">🔄 {{ t('btn.refresh') }}</button>
      </div>
    </div>

    <div v-if="successMessage" class="alert alert-success mb-4">
      {{ successMessage }}
    </div>

    <div v-if="loading" class="card text-center py-8 text-mute">
      {{ t('btn.loading') }}
    </div>

    <div v-else-if="inventory.length === 0" class="card text-center py-8 text-mute">
      {{ t('inventory.no_items') }}
    </div>

    <div v-else class="card card-flush">
      <div class="overflow-x-auto">
        <table class="table inventory-table">
          <thead>
            <tr>
              <th>{{ t('inventory.ingredient') }}</th>
              <th class="col-number">{{ t('inventory.in_stock') }}</th>
              <th class="col-unit"></th>
              <th class="col-number">{{ t('inventory.still_needed') }}</th>
              <th class="col-unit"></th>
              <th class="col-number">{{ t('inventory.balance') }}</th>
              <th class="col-unit"></th>
              <th class="col-action">{{ t('inventory.add_to_list') }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="cat in categories" :key="cat">
              <tr class="category-row">
                <td colspan="8">
                  <h3 class="category-header">{{ cat }}</h3>
                </td>
              </tr>

              <tr v-for="item in getItemsForCategory(cat)" :key="item.ingredient_id as string">
                <td><strong>{{ item.ingredient_name }}</strong></td>
                <td class="col-number">{{ parseFloat(item.quantity_bought.toFixed(2)) }}</td>
                <td class="col-unit">{{ item.unit }}</td>
                <td class="col-number">{{ parseFloat(item.quantity_required.toFixed(2)) }}</td>
                <td class="col-unit">{{ item.unit }}</td>
                <td class="col-number font-bold" :style="{ color: getBalanceColor(item.balance) }">
                  <span v-if="item.balance > 0">+</span>{{ parseFloat(item.balance.toFixed(2)) }}
                </td>
                <td class="col-unit font-bold" :style="{ color: getBalanceColor(item.balance) }">
                  {{ item.unit }}
                </td>
                <td class="col-action">
                  <button class="btn btn-secondary btn-xs" title="Add to latest shopping list"
                    @click="openAddModal(item)">
                    🛒+
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Item Modal -->
    <div v-if="showAddModal" class="modal-backdrop">
      <div class="modal">
        <h3>{{ t('inventory.add_to_list') }}</h3>
        <p v-if="selectedItem" class="mb-4">
          {{ t('inventory.add_to_list_question') }} ({{ selectedItem.ingredient_name }})
        </p>

        <div v-if="selectedItem" class="flex items-center gap-2 mb-6">
          <input type="number" class="input flex-1" v-model="addAmount" step="0.1" />
          <strong>{{ selectedItem.unit }}</strong>
        </div>

        <div class="flex gap-2 justify-end">
          <button class="btn btn-secondary" @click="showAddModal = false">{{ t('btn.cancel') }}</button>
          <button class="btn btn-primary" @click="confirmAdd" :disabled="adding">
            {{ adding ? t('btn.adding') : t('inventory.add_to_list') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-table {
  min-width: 800px;
}
</style>
