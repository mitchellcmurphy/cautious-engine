import type { z } from 'zod'
import { errorBodySchema } from './types'

const API_BASE: string = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  status: number
  code: string | undefined

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  const body = errorBodySchema.safeParse(await res.json().catch(() => null))
  if (body.success) {
    const { error, message, detail } = body.data
    const text = message ?? (typeof detail === 'string' ? detail : undefined)
    if (text) return new ApiError(text, res.status, error)
  }
  return new ApiError(res.statusText || `Request failed (${res.status})`, res.status)
}

export async function getJson<T>(path: string, schema: z.ZodType<T>, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { signal, headers: { Accept: 'application/json' } })
  if (!res.ok) throw await toApiError(res)
  const parsed = schema.safeParse(await res.json())
  if (!parsed.success) {
    throw new ApiError(`Unexpected response shape from ${path}`, res.status)
  }
  return parsed.data
}
