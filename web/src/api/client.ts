export interface AskRequest {
  question: string
  car?: string
  drivetrain?: string
  class_target?: string
  discipline?: 'road' | 'street' | 'dirt' | 'cross-country' | 'drag' | 'drift'
  horsepower?: number
  weight_lbs?: number
  tires?: string
  upgrades?: string[]
  build_notes?: string
}

export interface EvidenceItem {
  type: 'effect' | 'interaction' | 'baseline' | 'car' | 'build' | 'recommendation'
  title: string
  summary: string
}

export interface SafetyInfo {
  mode: 'deterministic' | 'llm_disabled'
  refused: boolean
  refusal_reason?: string
}

export interface AskResponse {
  answer: string
  likely_cause: string
  try_in_order: string[]
  watch_for: string[]
  evidence: EvidenceItem[]
  safety: SafetyInfo
}

export interface RefusalResponse {
  answer: string
  safety: SafetyInfo
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest extends Omit<AskRequest, 'question'> {
  messages: ChatMessage[]
}

export interface ChatResponse {
  message: ChatMessage
  answer: AskResponse | RefusalResponse
}

export interface CarResult {
  id: number
  make: string
  car_name: string
  full_name: string
  year: number | null
  car_type: string | null
  class_letter: string | null
  pi: number | null
}

export interface CarSearchResponse {
  results: CarResult[]
  total: number
}

export async function askQuestion(req: AskRequest): Promise<AskResponse> {
  const res = await fetch('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export async function searchCars(q: string): Promise<CarSearchResponse> {
  const res = await fetch(`/api/cars/search?q=${encodeURIComponent(q)}&limit=8`)
  if (!res.ok) throw new Error('Search failed')
  return res.json()
}
