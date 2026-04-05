import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import RecipeSidebar from '../components/RecipeSidebar.vue'

describe('RecipeSidebar.vue', () => {
  const mockRecipes = [
    { id: '1', name: 'Recipe 1', default_portions: 4, preferences: [] },
    { id: '2', name: 'Recipe 2', default_portions: 2, preferences: [{ id: 1, name: 'Vegan' }] }
  ]

  it('renders recipes when not collapsed', () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        recipes: mockRecipes as any,
        searchQuery: '',
        isCollapsed: false
      }
    })
    expect(wrapper.text()).toContain('Recipe 1')
    expect(wrapper.text()).toContain('Recipe 2')
    expect(wrapper.text()).toContain('Vegan')
  })

  it('filters recipes based on search query', () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        recipes: mockRecipes as any,
        searchQuery: 'Recipe 1',
        isCollapsed: false
      }
    })
    expect(wrapper.text()).toContain('Recipe 1')
    expect(wrapper.text()).not.toContain('Recipe 2')
  })

  it('emits update:isCollapsed when toggle button is clicked', async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        recipes: mockRecipes as any,
        searchQuery: '',
        isCollapsed: false
      }
    })
    await wrapper.find('.toggle-sidebar-btn').trigger('click')
    expect(wrapper.emitted('update:isCollapsed')).toBeTruthy()
    expect(wrapper.emitted('update:isCollapsed')![0][0]).toBe(true)
  })

  it('emits dragstart when recipe is dragged', async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        recipes: mockRecipes as any,
        searchQuery: '',
        isCollapsed: false
      }
    })
    const firstRecipe = wrapper.find('.recipe-draggable')
    await firstRecipe.trigger('dragstart')
    expect(wrapper.emitted('dragstart')).toBeTruthy()
  })

  it('shows vertical text when collapsed', () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        recipes: mockRecipes as any,
        searchQuery: '',
        isCollapsed: true
      }
    })
    expect(wrapper.find('.vertical-text').exists()).toBe(true)
    expect(wrapper.find('.content').isVisible()).toBe(false)
  })
})
