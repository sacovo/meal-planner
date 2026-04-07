import { ref, onMounted, onUnmounted } from 'vue'

export function useSSE(url: string | (() => string)) {
    const isConnected = ref(false)
    const eventSource = ref<EventSource | null>(null)

    // A generic map of listeners
    const listeners: Record<string, Array<(data: any) => void>> = {}

    const on = (event: string, callback: (data: any) => void) => {
        if (!listeners[event]) listeners[event] = []
        listeners[event].push(callback)
    }

    const connect = () => {
        const finalUrl = typeof url === 'function' ? url() : url
        if (!finalUrl) return

        eventSource.value = new EventSource(finalUrl)

        eventSource.value.onopen = () => {
            isConnected.value = true
        }

        // Default message handler
        eventSource.value.onmessage = (event) => {
            if (listeners['message']) {
                try {
                    const data = JSON.parse(event.data)
                    listeners['message'].forEach(cb => cb(data))
                } catch (e) {
                    console.error("Failed to parse SSE message", e)
                }
            }
        }

        eventSource.value.onerror = (error) => {
            console.error("SSE connection error", error)
            isConnected.value = false
            eventSource.value?.close()

            // Attempt to reconnect? EventSource handles reconnection natively most of the time,
            // but if explicit closed, we might need a timeout to retry depending on use case.
            // EventSource usually auto-reconnects with 3-5 seconds backoff.
        }
    }

    const disconnect = () => {
        if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
            isConnected.value = false
        }
    }

    onMounted(() => {
        connect()
    })

    onUnmounted(() => {
        disconnect()
    })

    return {
        isConnected,
        on,
        disconnect,
        connect
    }
}
