import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CampPlanner from '../views/CampPlanner.vue'
import { useRoute } from 'vue-router'

// Mocking vue-router
vi.mock('vue-router', () => ({
  useRoute: vi.fn(),
  useRouter: vi.fn(() => ({
    push: vi.fn()
  })),
  RouterLink: {
    template: '<a><slot /></a>'
  }
}))

// Mocking the API client
vi.mock('../client', () => ({
  mealsApiCampsGetCamp: vi.fn(() => Promise.resolve({ data: { id: '1', name: 'Test Camp', start_date: '2024-01-01', end_date: '2024-01-05', default_people_count: 10 } })),
  mealsApiMealsListCampMeals: vi.fn(() => Promise.resolve({ data: [] })),
  mealsApiRecipesListRecipes: vi.fn(() => Promise.resolve({ data: { items: [], count: 0 } })),
  mealsApiRecipesListPreferences: vi.fn(() => Promise.resolve({ data: [] })),
  mealsApiCampsListCampGeneralItems: vi.fn(() => Promise.resolve({ data: [] })),
  mealsApiShoppingListCampShoppingLists: vi.fn(() => Promise.resolve({ data: [] })),
  mealsApiIngredientsListTags: vi.fn(() => Promise.resolve({ data: [] })),
  coreApiAccount: vi.fn(() => Promise.resolve({ data: { username: 'testuser' } }))
}))

describe('CampPlanner.vue', () => {
  beforeEach(() => {
    vi.mocked(useRoute).mockReturnValue({
      params: { id: '1' }
    } as any)
  })

  it('renders camp name after loading', async () => {
    const wrapper = mount(CampPlanner, {
      global: {
        stubs: ['RouterLink']
      }
    })

    // Initially might show loading
    // Wait for promises to resolve
    await vi.dynamicImportSettled()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('plan')
    expect(wrapper.text()).toContain('Test Camp')
  })

  it('opens edit modal when edit button is clicked', async () => {
    const wrapper = mount(CampPlanner, {
      global: {
        stubs: ['RouterLink', 'EditCampModal']
      }
    })

    await vi.dynamicImportSettled()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Find the ⚙️ Edit button in the header
    const editBtn = wrapper.findAll('button').find(b => b.text().toLowerCase().includes('edit'))
    expect(editBtn).toBeTruthy()
    
    await editBtn?.trigger('click')
    
    // Check if the EditCampModal (stubbed) is present in some way or if the data state changed
    // Since it's stubbed, we can check for its usage or the local state if exposed
    // But better to check for the modal title if not stubbed, or use findComponent
    expect((wrapper.vm as any).editingCamp).toBe(true)
  })
})
