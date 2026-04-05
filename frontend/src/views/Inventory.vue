<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  mealsApiGetInventoryStatus, 
  mealsApiGetCamp,
  mealsApiAddManualShoppingItem,
  type InventoryStatusSchema,
  type CampSchema
} from '../client'

const route = useRoute()
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
      mealsApiGetInventoryStatus({ path: { camp_id: campId } }),
      mealsApiGetCamp({ path: { camp_id: campId } })
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
    await mealsApiAddManualShoppingItem({
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
  <div v-if="camp" class="flex-col gap-6">
    <div class="flex justify-between items-center">
      <div>
        <RouterLink :to="`/camps/${campId}`" class="badge" style="margin-bottom: 0.5rem">← Back to Planner</RouterLink>
        <h2 style="margin: 0;">Inventory & Stock: {{ camp.name }}</h2>
        <p class="text-mute">Track what you bought vs. what is still needed for remaining meals.</p>
      </div>
      <button class="btn btn-secondary" @click="fetchData">🔄 Refresh</button>
    </div>

    <div v-if="successMessage" class="card" style="background: var(--color-success); color: white; margin-bottom: 1rem; border: none; font-weight: bold; animation: slideIn 0.3s ease;">
      {{ successMessage }}
    </div>

    <div v-if="loading" class="card text-center py-8 text-mute">
      Calculating current stock and remaining needs...
    </div>

    <div v-else-if="inventory.length === 0" class="card text-center py-8 text-mute">
      No inventory data found. Generate a shopping list and check items to see stock here!
    </div>

    <div v-else class="card" style="padding: 0;">
      <div class="table-container" style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; min-width: 800px;">
          <thead>
            <tr style="text-align: left; font-size: 0.85rem; color: var(--color-text-mute); border-bottom: 2px solid var(--color-border); background: var(--color-bg-mute);">
              <th style="padding: 1rem 0.75rem;">Ingredient</th>
              <!-- In Stock -->
              <th style="padding: 1rem 0.25rem; text-align: right;">In Stock</th>
              <th style="padding: 1rem 0.25rem; text-align: left;"></th>
              <!-- Needed -->
              <th style="padding: 1rem 0.25rem; text-align: right;">Still Needed</th>
              <th style="padding: 1rem 0.25rem; text-align: left;"></th>
              <!-- Balance -->
              <th style="padding: 1rem 0.25rem; text-align: right;">Balance</th>
              <th style="padding: 1rem 0.75rem; text-align: left;"></th>
              <th style="padding: 1rem 0.75rem; text-align: center;">Add to List</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="cat in categories" :key="cat">
              <!-- Category Header Row -->
              <tr style="background: var(--color-bg-base);">
                <td colspan="8" style="padding: 0.75rem; border-bottom: 1px solid var(--color-border);">
                  <h3 style="margin: 0; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1.5px; color: var(--color-primary);">
                    {{ cat }}
                  </h3>
                </td>
              </tr>
              
              <!-- Items -->
              <tr v-for="item in getItemsForCategory(cat)" :key="item.ingredient_id as string" style="border-bottom: 1px solid var(--color-bg-mute);" class="inventory-row">
                <!-- Name -->
                <td style="padding: 0.75rem;">
                  <strong>{{ item.ingredient_name }}</strong>
                </td>
                
                <!-- In Stock -->
                <td style="padding: 0.75rem 0.25rem; text-align: right; width: 80px;">
                  {{ parseFloat(item.quantity_bought.toFixed(2)) }}
                </td>
                <td style="padding: 0.75rem 0.25rem; text-align: left; width: 60px; color: var(--color-text-mute); font-size: 0.85rem;">
                  {{ item.unit }}
                </td>
                
                <!-- Still Needed -->
                <td style="padding: 0.75rem 0.25rem; text-align: right; width: 80px;">
                  {{ parseFloat(item.quantity_required.toFixed(2)) }}
                </td>
                <td style="padding: 0.75rem 0.25rem; text-align: left; width: 60px; color: var(--color-text-mute); font-size: 0.85rem;">
                  {{ item.unit }}
                </td>
                
                <!-- Balance -->
                <td style="padding: 0.75rem 0.25rem; text-align: right; font-weight: bold; width: 100px;" :style="{ color: getBalanceColor(item.balance) }">
                  <span v-if="item.balance > 0">+</span>{{ parseFloat(item.balance.toFixed(2)) }}
                </td>
                <td style="padding: 0.75rem 0.75rem; text-align: left; font-weight: bold;" :style="{ color: getBalanceColor(item.balance) }">
                  {{ item.unit }}
                </td>
                <td style="padding: 0.75rem; text-align: center;">
                  <button class="btn btn-secondary btn-tiny" title="Add to latest shopping list" @click="openAddModal(item)">
                    🛒+
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Summary Legend -->
    <div class="card" style="background: var(--color-bg-mute); border: 1px dashed var(--color-border);">
      <h4 style="margin-top: 0;">How it works:</h4>
      <ul style="font-size: 0.85rem; padding-left: 1.2rem; line-height: 1.6; margin: 0;">
        <li><strong>In Stock:</strong> Sum of all items checked off on any shared shopping list for this camp.</li>
        <li><strong>Still Needed:</strong> Total requirement calculated from all planned meals that are NOT yet marked as "Cooked".</li>
        <li><strong>Balance:</strong> If this is negative, you need to buy more. If positive, you have extra!</li>
      </ul>
    </div>

    <!-- Add Item Modal -->
    <div v-if="showAddModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center;">
      <div class="card" style="width: 100%; max-width: 400px;">
        <h3>Add to Shopping List</h3>
        <p v-if="selectedItem" style="margin-bottom: 1rem;">
          How much <strong>{{ selectedItem.ingredient_name }}</strong> do you want to add?
        </p>
        
        <div v-if="selectedItem" class="flex items-center gap-2" style="margin-bottom: 1.5rem;">
          <input type="number" class="input" v-model="addAmount" style="flex: 1" step="0.1" />
          <strong>{{ selectedItem.unit }}</strong>
        </div>

        <div class="flex gap-2 justify-end">
          <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
          <button class="btn btn-primary" @click="confirmAdd" :disabled="adding">
            {{ adding ? 'Adding...' : '🛒 Add to List' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-container th {
  font-weight: 600;
}
tr:hover {
  background: var(--color-bg-base);
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
