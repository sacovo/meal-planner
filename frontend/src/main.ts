import { createApp } from 'vue'
import './style.css'

import App from './App.vue'
import router from './router'
import { client } from './client/client.gen'

client.setConfig({
    baseUrl: ''
})

function getCookie(name: string) {
    let cookieValue = null
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i]!.trim()
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}
let token = (document.querySelector('[name=csrfmiddlewaretoken]') as HTMLInputElement)?.value || ''

let user: { username: string } | null = null

// Add CSRF token to all requests
client.interceptors.request.use(async (request) => {
    const url = new URL(request.url)
    if (url.pathname.startsWith('/api/csrf')) {
        return request
    }
    request.headers.append('X-CSRFToken', token)
    return request
})

client.interceptors.response.use(async (response) => {
    const url = new URL(response.url)

    if (url.pathname === '/api/auth/account') {
        const data = await response
            .clone()
            .json()
            .catch(() => null)
        if (data && data.username) {
            user = {
                username: data.username,
            }
        } else {
            user = null
        }
    }

    return response
})

client.interceptors.response.use(async (response) => {
    if (response.status == 401) {
        if (router.currentRoute.value.meta['doNotRedirectToLogin'] !== true) {
            router.push({ path: '/login', query: { next: router.currentRoute.value.fullPath } })
        }
    }
    token = getCookie('csrftoken') || token
    return response
})


const app = createApp(App)
app.use(router)
app.mount('#app')
