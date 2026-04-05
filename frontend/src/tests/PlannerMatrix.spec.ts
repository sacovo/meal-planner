import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import PlannerMatrix from '../components/PlannerMatrix.vue'

describe('PlannerMatrix.vue', () => {
  const mockCamp = { id: '1', name: 'Test Camp' }
  const mockDays = ['2024-01-01', '2024-01-02']
  const mockMealTypes = [{ val: 'LUNCH', label: 'Lunch' }]
  const mockMealsGrid = {
    '2024-01-01': {
      'LUNCH': [{ id: 'm1', recipe: 'r1', is_done: false }]
    }
  }
  const mockRecipeNames = { 'r1': 'Recipe 1' }

  it('renders days and meal types', () => {
    const wrapper = mount(PlannerMatrix, {
      props: {
        camp: mockCamp as any,
        campDays: mockDays,
        mealTypesConfig: mockMealTypes,
        mealsGrid: mockMealsGrid as any,
        selectedMeals: [],
        recipeNames: mockRecipeNames
      }
    })
    expect(wrapper.text()).toContain('1.')
    expect(wrapper.text()).toContain('Jan')
    expect(wrapper.text()).toContain('Lunch')
    expect(wrapper.text()).toContain('Recipe 1')
  })

  it('emits switch-day when day header is clicked', async () => {
    const wrapper = mount(PlannerMatrix, {
      props: {
        camp: mockCamp as any,
        campDays: mockDays,
        mealTypesConfig: mockMealTypes,
        mealsGrid: mockMealsGrid as any,
        selectedMeals: [],
        recipeNames: mockRecipeNames
      }
    })
    await wrapper.find('.day-header-container').trigger('click')
    expect(wrapper.emitted('switch-day')).toBeTruthy()
    expect(wrapper.emitted('switch-day')![0][0]).toBe('2024-01-01')
  })

  it('emits toggle-day when select day checkbox is changed', async () => {
    const wrapper = mount(PlannerMatrix, {
      props: {
        camp: mockCamp as any,
        campDays: mockDays,
        mealTypesConfig: mockMealTypes,
        mealsGrid: mockMealsGrid as any,
        selectedMeals: [],
        recipeNames: mockRecipeNames
      }
    })
    await wrapper.find('.select-day-label input').trigger('change')
    expect(wrapper.emitted('toggle-day')).toBeTruthy()
    expect(wrapper.emitted('toggle-day')![0][0]).toBe('2024-01-01')
  })

  it('emits drop when a recipe is dropped', async () => {
    const wrapper = mount(PlannerMatrix, {
      props: {
        camp: mockCamp as any,
        campDays: mockDays,
        mealTypesConfig: mockMealTypes,
        mealsGrid: mockMealsGrid as any,
        selectedMeals: [],
        recipeNames: mockRecipeNames
      }
    })
    const cell = wrapper.find('.droppable-cell')
    await cell.trigger('drop')
    expect(wrapper.emitted('drop')).toBeTruthy()
  })
})
