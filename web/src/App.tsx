import { useEffect, useMemo, useRef, useState } from 'react'
import { searchCars, sendChat, type AskResponse, type CarResult, type ChatMessage, type RefusalResponse } from './api/client'
import AnswerPanel from './components/AnswerPanel'

const STARTERS = [
  {
    title: 'Pushes wide on corner exit',
    prompt: 'It pushes wide when I get back on throttle at corner exit. What should I try first?',
  },
  {
    title: 'Rear snaps under braking',
    prompt: 'The rear snaps loose on corner entry when I brake. How would you calm it down?',
  },
  {
    title: 'Too much wheelspin',
    prompt: 'It cannot put power down out of slow corners and spins through the lower gears.',
  },
  {
    title: 'Bouncy over bumps',
    prompt: 'The car bounces over curbs and rough sections and will not settle before the next corner.',
  },
]

const DRIVETRAINS = ['', 'FWD', 'RWD', 'AWD'] as const
const CLASSES = ['', 'D', 'C', 'B', 'A', 'S1', 'S2', 'R', 'X'] as const
const DISCIPLINES = ['', 'road', 'street', 'dirt', 'cross-country', 'drag', 'drift'] as const
const TIRE_OPTIONS = ['', 'stock tires', 'street tires', 'sport tires', 'semi-slick race tires', 'slick race tires', 'rally tires', 'drag tires', 'drift tires'] as const

type LoadState = 'idle' | 'loading' | 'error'
type ChatAnswer = AskResponse | RefusalResponse

type ConversationMessage = ChatMessage & {
  id: string
  answer?: ChatAnswer
}

const WELCOME: ConversationMessage = {
  id: 'welcome',
  role: 'assistant',
  content:
    'Start with the build details above if you know them, then tell me what happens on track. If something is missing, just ask anyway — I’ll work with what you have.',
}

function isAskResponse(answer?: ChatAnswer): answer is AskResponse {
  return Boolean(answer && 'likely_cause' in answer && Array.isArray((answer as AskResponse).try_in_order))
}

function makeId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function toNumber(value: string) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined
}

function splitUpgrades(value: string) {
  return value
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
    .slice(0, 12)
}

function carBadge(car: CarResult) {
  const classText = car.class_letter || car.pi ? `${car.class_letter ?? ''}${car.pi ?? ''}` : ''
  return [car.year, car.car_type, classText].filter(Boolean).join(' · ')
}

export default function App() {
  const [messages, setMessages] = useState<ConversationMessage[]>([WELCOME])
  const [draft, setDraft] = useState('')
  const [car, setCar] = useState('')
  const [drivetrain, setDrivetrain] = useState('')
  const [classTarget, setClassTarget] = useState('')
  const [discipline, setDiscipline] = useState('')
  const [horsepower, setHorsepower] = useState('')
  const [weightLbs, setWeightLbs] = useState('')
  const [tires, setTires] = useState('')
  const [upgrades, setUpgrades] = useState('')
  const [buildNotes, setBuildNotes] = useState('')
  const [carResults, setCarResults] = useState<CarResult[]>([])
  const [carSearchOpen, setCarSearchOpen] = useState(false)
  const [carSearchLoading, setCarSearchLoading] = useState(false)
  const [loadState, setLoadState] = useState<LoadState>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const composerRef = useRef<HTMLTextAreaElement | null>(null)

  const apiMessages = useMemo(
    () => messages
      .filter(message => message.id !== 'welcome')
      .slice(-10)
      .map(({ role, content }) => ({ role, content: content.slice(0, 3500) })),
    [messages],
  )

  const contextSummary = useMemo(() => {
    const pieces = [
      car,
      drivetrain,
      classTarget,
      discipline,
      horsepower ? `${horsepower} hp` : '',
      tires,
    ].filter(Boolean)
    return pieces.length > 0 ? pieces.join(' · ') : 'No setup details yet'
  }, [car, drivetrain, classTarget, discipline, horsepower, tires])

  useEffect(() => {
    const query = car.trim()
    if (!carSearchOpen || query.length < 2) {
      setCarResults([])
      setCarSearchLoading(false)
      return
    }

    let cancelled = false
    setCarSearchLoading(true)
    const timeout = window.setTimeout(async () => {
      try {
        const res = await searchCars(query)
        if (!cancelled) setCarResults(res.results)
      } catch {
        if (!cancelled) setCarResults([])
      } finally {
        if (!cancelled) setCarSearchLoading(false)
      }
    }, 180)

    return () => {
      cancelled = true
      window.clearTimeout(timeout)
    }
  }, [car, carSearchOpen])

  const submitPrompt = async (prompt?: string) => {
    const q = (prompt ?? draft).trim()
    if (!q || q.length < 3 || loadState === 'loading') return

    const userMessage: ConversationMessage = { id: makeId('user'), role: 'user', content: q }
    const nextApiMessages = [...apiMessages, { role: 'user' as const, content: q }]

    setMessages(current => [...current, userMessage])
    setDraft('')
    setErrorMsg('')
    setLoadState('loading')

    try {
      const res = await sendChat({
        messages: nextApiMessages,
        car: car.trim() || undefined,
        drivetrain: drivetrain || undefined,
        class_target: classTarget || undefined,
        discipline: discipline ? discipline as 'road' | 'street' | 'dirt' | 'cross-country' | 'drag' | 'drift' : undefined,
        horsepower: toNumber(horsepower),
        weight_lbs: toNumber(weightLbs),
        tires: tires.trim() || undefined,
        upgrades: splitUpgrades(upgrades),
        build_notes: buildNotes.trim() || undefined,
      })

      setMessages(current => [
        ...current,
        {
          id: makeId('assistant'),
          role: 'assistant',
          content: res.message.content,
          answer: res.answer,
        },
      ])
      setLoadState('idle')
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : 'Request failed')
      setLoadState('error')
    }
  }

  const handleCarSelect = (c: CarResult) => {
    setCar(c.full_name)
    setCarResults([])
    setCarSearchOpen(false)
    composerRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void submitPrompt()
    }
  }

  return (
    <div className="lab-shell">
      <header className="lab-container pb-4 pt-5 sm:pt-7">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#8f4b2f] text-sm font-black text-white shadow-[0_10px_26px_rgba(143,75,47,0.24)]">
              HTL
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Horizon Tune Lab</p>
              <h1 className="text-lg font-semibold tracking-[-0.03em] text-stone-950">Forza setup coach</h1>
            </div>
          </div>
          <span className="hidden rounded-full bg-white/65 px-3 py-1.5 text-xs font-medium text-stone-500 sm:inline-flex">
            read-only tuning index
          </span>
        </div>
      </header>

      <main className="lab-container pb-10">
        <section className="mb-5 rounded-[32px] bg-[#2d2822] p-5 text-white shadow-[0_24px_70px_rgba(45,40,34,0.18)] sm:p-7">
          <p className="mb-3 text-sm font-medium text-white/60">Where to start</p>
          <h2 className="max-w-2xl text-3xl font-semibold leading-tight tracking-[-0.055em] sm:text-5xl">
            Put in the build once. Then talk through the handling.
          </h2>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-white/72 sm:text-base">
            Add horsepower, tires, drivetrain, and upgrades up front. After that, every chat message uses that setup as context, so the answer can feel more like a tuner reasoning with you instead of a form response.
          </p>
        </section>

        <section className="lab-card mb-5 p-4 sm:p-5">
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="lab-label mb-1">Step 1</p>
              <h3 className="text-xl font-semibold tracking-[-0.035em] text-stone-950">Your car setup</h3>
            </div>
            <p className="text-sm text-stone-500">Saved for this chat: <span className="font-medium text-stone-700">{contextSummary}</span></p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="relative space-y-2 sm:col-span-2">
              <label className="lab-label" htmlFor="car-combobox">Car</label>
              <div className="relative">
                <input
                  id="car-combobox"
                  role="combobox"
                  aria-expanded={carSearchOpen}
                  aria-controls="car-options"
                  aria-autocomplete="list"
                  value={car}
                  onChange={e => {
                    setCar(e.target.value)
                    setCarSearchOpen(true)
                  }}
                  onFocus={() => setCarSearchOpen(true)}
                  onBlur={() => window.setTimeout(() => setCarSearchOpen(false), 140)}
                  placeholder="Search car index… Ferrari, Supra, Lambo"
                  maxLength={80}
                  className="lab-input pr-11"
                />
                <button
                  type="button"
                  aria-label="Open index results"
                  onMouseDown={e => e.preventDefault()}
                  onClick={() => setCarSearchOpen(open => !open)}
                  className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-stone-500 transition hover:bg-stone-100 hover:text-stone-900"
                >
                  ⌄
                </button>
              </div>
              {carSearchOpen && (
                <div id="car-options" role="listbox" className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-[0_18px_48px_rgba(64,48,35,0.16)]">
                  {car.trim().length < 2 && (
                    <div className="px-4 py-3 text-sm text-stone-500">Type at least 2 letters to search cars.</div>
                  )}
                  {car.trim().length >= 2 && carSearchLoading && (
                    <div className="px-4 py-3 text-sm text-stone-500">Searching car index…</div>
                  )}
                  {car.trim().length >= 2 && !carSearchLoading && carResults.length === 0 && (
                    <div className="px-4 py-3 text-sm text-stone-500">No matching cars found. You can still type the car manually.</div>
                  )}
                  {carResults.map(result => (
                    <button
                      key={result.id}
                      type="button"
                      role="option"
                      aria-selected={car === result.full_name}
                      onMouseDown={e => e.preventDefault()}
                      onClick={() => handleCarSelect(result)}
                      className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-stone-100 px-4 py-3 text-left transition last:border-b-0 hover:bg-[#f8f1e8]"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold text-stone-950">{result.full_name}</span>
                        <span className="mt-0.5 block truncate text-xs text-stone-500">{carBadge(result) || 'FH6 index entry'}</span>
                      </span>
                      <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-semibold text-stone-600">Select</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <label className="space-y-2">
              <span className="lab-label">Drivetrain</span>
              <select value={drivetrain} onChange={e => setDrivetrain(e.target.value)} className="lab-input">
                {DRIVETRAINS.map(d => <option key={d} value={d}>{d || 'Any'}</option>)}
              </select>
            </label>
            <label className="space-y-2">
              <span className="lab-label">Class</span>
              <select value={classTarget} onChange={e => setClassTarget(e.target.value)} className="lab-input">
                {CLASSES.map(c => <option key={c} value={c}>{c || 'Any'}</option>)}
              </select>
            </label>
            <label className="space-y-2">
              <span className="lab-label">HP</span>
              <input value={horsepower} onChange={e => setHorsepower(e.target.value.replace(/[^0-9]/g, ''))} placeholder="920" inputMode="numeric" maxLength={4} className="lab-input" />
            </label>
            <label className="space-y-2">
              <span className="lab-label">Weight</span>
              <input value={weightLbs} onChange={e => setWeightLbs(e.target.value.replace(/[^0-9]/g, ''))} placeholder="2420 lb" inputMode="numeric" maxLength={5} className="lab-input" />
            </label>
            <label className="space-y-2">
              <span className="lab-label">Tires</span>
              <select value={tires} onChange={e => setTires(e.target.value)} className="lab-input">
                {TIRE_OPTIONS.map(t => <option key={t} value={t}>{t || 'Unknown'}</option>)}
              </select>
            </label>
            <label className="space-y-2">
              <span className="lab-label">Surface</span>
              <select value={discipline} onChange={e => setDiscipline(e.target.value)} className="lab-input">
                {DISCIPLINES.map(d => <option key={d} value={d}>{d || 'Any'}</option>)}
              </select>
            </label>
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <label className="space-y-2">
              <span className="lab-label">Major upgrades</span>
              <input value={upgrades} onChange={e => setUpgrades(e.target.value)} placeholder="race diff, front aero, race suspension" maxLength={320} className="lab-input" />
            </label>
            <label className="space-y-2">
              <span className="lab-label">Build notes</span>
              <input value={buildNotes} onChange={e => setBuildNotes(e.target.value)} placeholder="widebody, engine swap, rear aero, power build…" maxLength={280} className="lab-input" />
            </label>
          </div>

        </section>

        <section className="lab-card overflow-hidden">
          <div className="border-b border-stone-200/80 bg-white/50 px-4 py-4 sm:px-5">
            <p className="lab-label mb-1">Step 2</p>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h3 className="text-2xl font-semibold tracking-[-0.045em] text-stone-950">Ask the tuner</h3>
                <p className="mt-1 text-sm text-stone-500">Describe what happens, when it happens, and what you tried already.</p>
              </div>
              <span className="lab-chip w-fit">uses your setup above</span>
            </div>
          </div>

          <div className="space-y-5 bg-[#fffdf8] px-4 py-5 sm:px-5">
            {messages.map(message => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={message.role === 'user' ? 'max-w-[86%]' : 'w-full max-w-[94%]'}>
                  {isAskResponse(message.answer) ? (
                    <AnswerPanel response={message.answer} />
                  ) : (
                    <div className={`rounded-[26px] px-4 py-3 text-sm leading-7 shadow-sm ${message.role === 'user' ? 'bg-[#8f4b2f] text-white' : 'border border-stone-200 bg-white/80 text-stone-700'}`}>
                      {message.content}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loadState === 'loading' && (
              <div className="flex justify-start">
                <div className="rounded-[26px] border border-stone-200 bg-white/80 px-4 py-3 text-sm leading-7 text-stone-600 shadow-sm">
                  Thinking through the setup and checking the tuning index…
                </div>
              </div>
            )}
            {loadState === 'error' && (
              <div className="rounded-3xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{errorMsg}</div>
            )}
          </div>

          <div className="border-t border-stone-200/80 bg-[#f8f1e8] p-4 sm:p-5">
            <div className="mb-3 flex flex-wrap gap-2">
              {STARTERS.map(starter => (
                <button key={starter.title} onClick={() => void submitPrompt(starter.prompt)} disabled={loadState === 'loading'} className="lab-chip transition hover:border-[#8f4b2f]/35 hover:bg-white disabled:opacity-50">
                  {starter.title}
                </button>
              ))}
            </div>
            <label className="block">
              <span className="sr-only">Message the tuner</span>
              <textarea
                ref={composerRef}
                value={draft}
                onChange={e => setDraft(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask naturally: it rotates fine on entry but pushes on throttle in 3rd gear…"
                rows={3}
                maxLength={800}
                className="lab-input min-h-[104px] resize-none bg-white"
              />
            </label>
            <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs text-stone-500">{draft.length}/800 · Enter sends · Shift+Enter makes a new line</p>
              <button onClick={() => void submitPrompt()} disabled={loadState === 'loading' || draft.trim().length < 3} className="lab-button-primary w-full sm:w-auto">
                {loadState === 'loading' ? 'Reasoning…' : 'Send'}
              </button>
            </div>
          </div>
        </section>
      </main>

      <footer className="lab-container pb-8 text-center text-xs leading-6 text-stone-500">
        Unofficial fan project. No login, no personal save data, read-only tuning index.
      </footer>
    </div>
  )
}
