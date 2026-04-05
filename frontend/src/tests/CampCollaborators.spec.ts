import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import CampCollaborators from '../components/CampCollaborators.vue'

describe('CampCollaborators.vue', () => {
  const mockProps = {
    collaborators: ['user1', 'user2'],
    ownerUsername: 'owner',
    currentUserUsername: 'owner'
  }

  it('renders collaborators and owner', () => {
    const wrapper = mount(CampCollaborators, {
      props: mockProps
    })
    expect(wrapper.text()).toContain('owner')
    expect(wrapper.text()).toContain('user1')
    expect(wrapper.text()).toContain('user2')
    expect(wrapper.text()).toContain('Invite')
  })

  it('shows remove buttons only for owner or self', () => {
    const wrapper = mount(CampCollaborators, {
      props: { ...mockProps, currentUserUsername: 'owner' }
    })
    const removeButtons = wrapper.findAll('.btn-danger-outline')
    // owner cannot be removed (in my UI logic it's not a button for owner)
    // user1, user2 can be removed by owner
    expect(removeButtons.length).toBe(2)
  })

  it('shows leave button for collaborator self', () => {
    const wrapper = mount(CampCollaborators, {
      props: { ...mockProps, currentUserUsername: 'user1' }
    })
    const removeButtons = wrapper.findAll('.btn-danger-outline')
    // user1 can remove self, but cannot remove user2 or owner
    expect(removeButtons.length).toBe(1)
    expect(removeButtons[0].text()).toBe('Leave')
  })

  it('emits invite when invite button is clicked', async () => {
    const wrapper = mount(CampCollaborators, {
      props: mockProps
    })
    const input = wrapper.find('input')
    await input.setValue('newuser ') // test trim
    await wrapper.find('.btn-primary').trigger('click')
    expect(wrapper.emitted('invite')).toBeTruthy()
    expect(wrapper.emitted('invite')![0][0]).toBe('newuser')
  })
})
