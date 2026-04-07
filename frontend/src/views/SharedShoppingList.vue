<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useRoute } from "vue-router";
import {
  mealsApiShoppingGetSharedShoppingList,
  mealsApiShoppingToggleSharedShoppingItem,
  coreApiGetCurrentUserStatus,
  mealsApiShoppingExportSharedShoppingList,
  type ShoppingListSchema,
  type ShoppingListItemSchema,
} from "../client";
import { useFileDownload } from "../composables/useFileDownload";
import { useI18n } from "@/composables/useI18n";
import { useSSE } from "@/composables/useSSE";

const route = useRoute();
const { downloadBlob } = useFileDownload();
const { t } = useI18n();
const sharedToken = route.params.token as string;

const shoppingList = ref<ShoppingListSchema | null>(null);
const isLoggedIn = ref(false);
const isNavOpen = ref(false);

const sseUrl = computed(
  () => `/api/meals/shared/shopping-lists/${sharedToken}/events`,
);
const { on } = useSSE(() => sseUrl.value);

async function checkAuth() {
  const { data } = await coreApiGetCurrentUserStatus();
  if (data?.is_logged_in) {
    isLoggedIn.value = true;
  }
}
const collapsedCategories = ref<Record<string, boolean>>({});

function toggleCategory(cat: string) {
  collapsedCategories.value[cat] = !collapsedCategories.value[cat];
}

async function fetchList() {
  const { data } = await mealsApiShoppingGetSharedShoppingList({
    path: { token: sharedToken },
  });
  if (data) {
    shoppingList.value = data;
  }
}

// Perform optimistic update
async function toggleItem(item: ShoppingListItemSchema) {
  item.is_checked = !item.is_checked;

  const { data } = await mealsApiShoppingToggleSharedShoppingItem({
    path: { token: sharedToken, item_id: String(item.id!) },
  });

  if (data) {
    item.is_checked = data.is_checked;
  }
}

// Aggregation by category
const itemsByCategory = computed(() => {
  if (!shoppingList.value?.items) return {};
  const grouped: Record<string, ShoppingListItemSchema[]> = {};
  shoppingList.value.items.forEach((item: any) => {
    if (!grouped[item.category]) grouped[item.category] = [];
    grouped[item.category].push(item);
  });
  return grouped;
});

const categoryEntries = computed(() => Object.entries(itemsByCategory.value));

const categoryCounts = computed(() => {
  const counts: Record<string, { done: number; total: number }> = {};
  if (!shoppingList.value) return counts;
  shoppingList.value.items.forEach((item) => {
    const cat = item.category;
    if (!counts[cat]) counts[cat] = { done: 0, total: 0 };
    counts[cat].total++;
    if (item.is_checked) counts[cat].done++;
  });
  return counts;
});

async function exportExcel() {
  const res = await mealsApiShoppingExportSharedShoppingList({
    path: { token: sharedToken },
    parseAs: "blob",
  });
  if (res.data) {
    downloadBlob(res.data as unknown as Blob, "shopping_list.xlsx");
  }
}

function copyLink() {
  const url = window.location.href;
  navigator.clipboard.writeText(url);
  alert("Link copied to clipboard! Anyone with this link can check off items.");
}

function getCategoryAnchor(category: string) {
  return `category-${category
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")}`;
}

function closeNav() {
  isNavOpen.value = false;
}

onMounted(() => {
  fetchList();
  checkAuth();

  on("message", (updatedItem: ShoppingListItemSchema) => {
    if (shoppingList.value && shoppingList.value.items) {
      const idx = shoppingList.value.items.findIndex(
        (i: any) => i.id === updatedItem.id,
      );
      if (idx !== -1) {
        shoppingList.value.items[idx] = updatedItem;
      } else {
        // Fallback: If item is completely new, refetch entire list
        fetchList();
      }
    }
  });
});

onUnmounted(() => {});
</script>

<template>
  <div v-if="shoppingList" class="flex-col gap-4">
    <div class="card shared-header">
      <div class="header-top">
        <RouterLink
          v-if="isLoggedIn && shoppingList"
          :to="`/camps/${shoppingList.camp_id}`"
          class="badge mb-2"
          >{{ t("btn.back") }}</RouterLink
        >
        <h2 class="page-title">Live Shopping List</h2>
        <p class="text-mute text-sm">Changes are synchronized in real-time.</p>
      </div>
      <div class="header-actions">
        <button
          v-if="categoryEntries.length > 0"
          class="btn btn-secondary quick-nav-toggle hide-desktop"
          @click="isNavOpen = true"
        >
          ☰ Quick Nav
        </button>
        <button class="btn btn-secondary" @click="exportExcel">
          📥 Export
        </button>
        <button class="btn btn-secondary" @click="copyLink">
          🔗 Share Link
        </button>
      </div>
    </div>

    <div
      v-if="categoryEntries.length > 0"
      class="drawer-backdrop no-print hide-desktop"
      :class="{ open: isNavOpen }"
      @click="closeNav"
    />

    <aside
      v-if="categoryEntries.length > 0"
      class="quick-nav-drawer no-print hide-desktop"
      :class="{ open: isNavOpen }"
    >
      <div class="drawer-header">
        <h3 class="mb-0">Quick Nav</h3>
        <button class="btn btn-secondary btn-sm" @click="closeNav">
          Close
        </button>
      </div>
      <nav>
        <ul class="quick-nav-list">
          <li
            v-for="[category, items] in categoryEntries"
            :key="`drawer-${category}`"
          >
            <a
              class="quick-nav-link"
              :href="`#${getCategoryAnchor(category)}`"
              @click="closeNav"
            >
              <span>{{ category }}</span>
              <span class="text-mute">{{ items.length }}</span>
            </a>
          </li>
        </ul>
      </nav>
    </aside>

    <div class="shared-layout">
      <div class="flex-col gap-4">
        <!-- Grouped Categories -->
        <div
          v-for="[category, items] in categoryEntries"
          :id="getCategoryAnchor(category)"
          :key="category"
          class="card"
          :class="{
            'category-done':
              categoryCounts[category as string].done ===
              categoryCounts[category as string].total,
          }"
        >
          <div
            class="category-toggle flex justify-between items-center"
            @click="toggleCategory(category as string)"
          >
            <div class="flex items-center gap-2">
              <h3
                class="category-heading"
                :class="{
                  'text-success':
                    categoryCounts[category as string].done ===
                    categoryCounts[category as string].total,
                }"
              >
                {{
                  categoryCounts[category as string].done ===
                  categoryCounts[category as string].total
                    ? "✓ "
                    : ""
                }}{{ category }}
              </h3>
              <span class="text-xs text-mute category-count">
                ({{ categoryCounts[category as string].done }} /
                {{ categoryCounts[category as string].total }} done)
              </span>
            </div>
            <span class="collapse-icon text-mute">
              {{ collapsedCategories[category as string] ? "+" : "−" }}
            </span>
          </div>

          <ul
            v-show="!collapsedCategories[category as string]"
            class="list-reset flex-col gap-2 mt-4"
          >
            <li
              v-for="item in items"
              :key="item.id!"
              class="shopping-item"
              :class="{ 'checked-item text-mute': item.is_checked }"
              @click="toggleItem(item)"
            >
              <div class="checkbox" :class="{ checked: item.is_checked }">
                {{ item.is_checked ? "✓" : "" }}
              </div>

              <div
                class="item-content"
                :class="{ 'line-through': item.is_checked }"
              >
                <div class="item-name">
                  <strong v-if="item.ingredient">{{
                    (item as any).ingredient.name
                  }}</strong>
                  <strong v-else>{{ item.custom_name }}</strong>
                </div>

                <div
                  class="item-sources"
                  v-if="item.source_meals_text && item.source_meals_text.length"
                  @click.stop
                >
                  <!-- Mobile Collapsible -->
                  <details class="source-details hidden-desktop">
                    <summary class="text-mute">
                      {{ item.source_meals_text.length }} Menus (Show)
                    </summary>
                    <ul>
                      <li
                        v-for="(src, idx) in item.source_meals_text"
                        :key="idx"
                      >
                        {{ src }}
                      </li>
                    </ul>
                  </details>

                  <!-- Desktop flat list -->
                  <div class="source-desktop hidden-mobile text-mute">
                    <ul :class="{ 'no-line-through': item.is_checked }">
                      <li
                        v-for="(src, idx) in item.source_meals_text"
                        :key="idx"
                      >
                        {{ src }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <div
                class="item-measurement text-right text-mute"
                :class="{ 'line-through': item.is_checked }"
              >
                <strong
                  >{{ parseFloat(item.amount.toFixed(2)) }}
                  {{ item.unit }}</strong
                >
              </div>
            </li>
          </ul>
        </div>
      </div>

      <aside
        v-if="categoryEntries.length > 0"
        class="quick-nav card no-print hide-mobile"
      >
        <h3 class="mb-2">Quick Nav</h3>
        <nav>
          <ul class="quick-nav-list">
            <li
              v-for="[category, items] in categoryEntries"
              :key="`desktop-${category}`"
            >
              <a
                class="quick-nav-link"
                :href="`#${getCategoryAnchor(category)}`"
              >
                <span>{{ category }}</span>
                <span class="text-mute">{{ items.length }}</span>
              </a>
            </li>
          </ul>
        </nav>
      </aside>
    </div>
  </div>
  <div v-else class="text-center text-mute py-8">
    {{ t("loading") }}
  </div>
</template>

<style scoped>
.shared-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 1.5rem;
  align-items: start;
}

.shared-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.header-top {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.category-done {
  opacity: 0.7;
  border-style: dashed;
}

.category-toggle {
  cursor: pointer;
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 0.5rem;
  text-transform: uppercase;
  font-size: 0.9rem;
  letter-spacing: 1px;
}

.category-heading {
  margin: 0;
  font-size: inherit;
}

.category-count {
  text-transform: none;
  font-weight: normal;
}

.collapse-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.line-through {
  text-decoration: line-through;
}

.no-line-through {
  text-decoration: none;
}

.shopping-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--color-bg-mute);
  border-radius: var(--radius-sm);
  cursor: pointer;
  user-select: none;
}

.shopping-item.checked-item {
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
}

.checkbox {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 2px solid var(--color-border);
  margin-right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: transparent;
  flex-shrink: 0;
}

.checkbox.checked {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-measurement {
  flex-shrink: 0;
  min-width: 60px;
  margin-left: 1rem;
}

.hidden-desktop {
  display: block;
}

.hidden-mobile {
  display: none;
}

.source-details {
  margin-top: 4px;
  font-size: 0.8rem;
}

.source-details summary {
  cursor: pointer;
  font-size: 0.75rem;
}

.source-details ul {
  padding-left: 1rem;
  margin: 4px 0 0 0;
}

@media (min-width: 768px) {
  .item-content {
    display: grid;
    grid-template-columns: 200px 1fr;
    align-items: center;
    gap: 1rem;
  }

  .item-name {
    flex: none;
    width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .item-sources {
    flex: none;
    padding: 0;
  }

  .hidden-desktop {
    display: none;
  }

  .hidden-mobile {
    display: block;
  }

  .source-desktop ul {
    padding: 0;
    margin: 0;
    list-style: disc;
    padding-left: 1rem;
    font-size: 0.75rem;
  }
}

@media (max-width: 900px) {
  .shared-layout {
    display: block;
  }

  .shared-header {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
