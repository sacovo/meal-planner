import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ShoppingListManager from '../components/ShoppingListManager.vue'

describe('ShoppingListManager.vue', () => {
  const mockShoppingLists = [
    { 
      id: '1', 
      created_at: '2024-01-01T12:00:00Z', 
      shared_token: 'token1', 
      included_meals: ['2024-01-01 (Lunch): Pasta'] 
    }
  ]

  it('renders action bar with correct count', () => {
    const wrapper = mount(ShoppingListManager, {
      props: {
        selectedMealsCount: 5,
        showShoppingLists: false,
        shoppingLists: [],
        loading: false
      }
    })
    expect(wrapper.text()).toContain('5 checked menus')
  })

  it('renders loading state', () => {
    const wrapper = mount(ShoppingListManager, {
      props: {
        selectedMealsCount: 0,
        showShoppingLists: true,
        shoppingLists: [],
        loading: true
      }
    })
    expect(wrapper.text()).toContain('Loading lists...')
  })

  it('renders shopping lists when shown', () => {
    const wrapper = mount(ShoppingListManager, {
      props: {
        selectedMealsCount: 0,
        showShoppingLists: true,
        shoppingLists: mockShoppingLists as any,
        loading: false
      }
    })
    expect(wrapper.text()).toContain('Shopping Lists')
    expect(wrapper.text()).toContain('Pasta')
    expect(wrapper.text()).toContain('2024-01-01')
  })

  it('emits generate event when button is clicked', async () => {
    const wrapper = mount(ShoppingListManager, {
      props: {
        selectedMealsCount: 1,
        showShoppingLists: false,
        shoppingLists: [],
        loading: false
      }
    })
    await wrapper.find('.btn-primary').trigger('click')
    expect(wrapper.emitted('generate')).toBeTruthy()
  })

  it('emits delete event when delete button is clicked', async () => {
    const wrapper = mount(ShoppingListManager, {
      props: {
        selectedMealsCount: 0,
        showShoppingLists: true,
        shoppingLists: mockShoppingLists as any,
        loading: false
      }
    })
    await wrapper.find('.delete-btn').trigger('click')
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0][0]).toBe('1')
  })
})
