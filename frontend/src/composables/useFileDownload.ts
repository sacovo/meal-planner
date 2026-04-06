/**
 * Utility for downloading blob responses from the API as files.
 * Used by inventory export, shopping list export, etc.
 */
export function useFileDownload() {
  function downloadBlob(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  }

  return { downloadBlob }
}
