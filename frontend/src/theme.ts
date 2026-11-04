export const APPEARANCE_STORAGE_KEY = 'dark-mode'
export const DARK_APPEARANCE = 'true'
export const LIGHT_APPEARANCE = 'false'

export type AppearanceMode = 'dark' | 'light'

export type AppearanceStorage = Pick<Storage, 'getItem' | 'setItem'>

const getDefaultStorage = (): AppearanceStorage | null => {
  try {
    return typeof window === 'undefined' ? null : window.localStorage
  } catch {
    return null
  }
}

export const resolveAppearance = (storedValue: string | null): AppearanceMode =>
  storedValue === LIGHT_APPEARANCE ? 'light' : 'dark'

export const readAppearance = (storage: AppearanceStorage | null = getDefaultStorage()): AppearanceMode => {
  try {
    return resolveAppearance(storage ? storage.getItem(APPEARANCE_STORAGE_KEY) : null)
  } catch {
    return 'dark'
  }
}

export const writeAppearance = (mode: AppearanceMode, storage: AppearanceStorage | null = getDefaultStorage()): void => {
  try {
    storage?.setItem(APPEARANCE_STORAGE_KEY, mode === 'dark' ? DARK_APPEARANCE : LIGHT_APPEARANCE)
  } catch {
    return
  }
}

export const themeColorFor = (mode: AppearanceMode): string =>
  mode === 'dark' ? '#17262b' : '#f4f0e8'

export const applyAppearance = (mode: AppearanceMode): void => {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.classList.toggle('dark-mode', mode === 'dark')

  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
  if (meta) {
    meta.setAttribute('content', themeColorFor(mode))
  }
}
