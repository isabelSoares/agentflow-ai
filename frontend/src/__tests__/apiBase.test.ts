import { describe, expect, it, vi } from 'vitest'
import { resolveApiBase } from '../api'

describe('resolveApiBase', () => {
  it('defaults to the /api gateway prefix when unset or blank', () => {
    expect(resolveApiBase(undefined)).toBe('/api')
    expect(resolveApiBase('')).toBe('/api')
    expect(resolveApiBase('   ')).toBe('/api')
  })

  it('normalizes a configured prefix by removing trailing slashes', () => {
    expect(resolveApiBase('/api/')).toBe('/api')
    expect(resolveApiBase('http://localhost:8000/')).toBe('http://localhost:8000')
  })

  it('uses VITE_API_BASE_URL for direct-origin deployments', () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://api.example.test/')

    expect(resolveApiBase()).toBe('http://api.example.test')
  })
})
