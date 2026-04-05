import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import MealCard from '../components/MealCard.vue'

describe('MealCard.vue', () => {
  const mockMeal = {
    id: '1',
    recipe: '101',
    is_done: false,
    override_people_count: null,
    serves_preference: null
  }
  const mockCamp = {
    default_people_count: 10
  }

  it('renders meal details correctly', () => {
    const wrapper = mount(MealCard, {
      props: {
        meal: mockMeal as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    expect(wrapper.text()).toContain('Test Recipe')
    expect(wrapper.text()).toContain('10 people')
  })

  it('renders overrides when provided', () => {
    const mealWithOverride = { ...mockMeal, override_people_count: 5, serves_preference: { name: 'Kids' } }
    const wrapper = mount(MealCard, {
      props: {
        meal: mealWithOverride as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    expect(wrapper.text()).toContain('5 people')
    expect(wrapper.text()).toContain('(Kids)')
  })

  it('emits update:isSelected when checkbox is changed', async () => {
    const wrapper = mount(MealCard, {
      props: {
        meal: mockMeal as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    await wrapper.find('input[type="checkbox"]').trigger('change')
    expect(wrapper.emitted('update:isSelected')).toBeTruthy()
  })

  it('emits edit when card is clicked', async () => {
    const wrapper = mount(MealCard, {
      props: {
        meal: mockMeal as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('edit')).toBeTruthy()
  })

  it('emits toggle-done when icon is clicked', async () => {
    const wrapper = mount(MealCard, {
      props: {
        meal: mockMeal as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    await wrapper.find('.done-btn').trigger('click')
    expect(wrapper.emitted('toggle-done')).toBeTruthy()
  })

  it('emits remove when remove button is clicked', async () => {
    const wrapper = mount(MealCard, {
      props: {
        meal: mockMeal as any,
        camp: mockCamp as any,
        recipeName: 'Test Recipe',
        isSelected: false
      }
    })
    await wrapper.find('.remove-btn').trigger('click')
    expect(wrapper.emitted('remove')).toBeTruthy()
  })
})
