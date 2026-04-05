import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import CampNotes from '../components/CampNotes.vue'

describe('CampNotes.vue', () => {
  it('renders notes when provided', () => {
    const notes = 'Test notes'
    const wrapper = mount(CampNotes, {
      props: { notes }
    })
    expect(wrapper.text()).toContain(notes)
  })

  it('renders default text when notes are empty', () => {
    const wrapper = mount(CampNotes, {
      props: { notes: '' }
    })
    expect(wrapper.text()).toContain('No special notes')
  })

  it('emits edit event when edit button is clicked', async () => {
    const wrapper = mount(CampNotes)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('edit')
  })
})
