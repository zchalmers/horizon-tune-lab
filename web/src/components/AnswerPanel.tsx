import type { AskResponse, EvidenceItem } from '../api/client'

interface Props {
  response: AskResponse
}

const EVIDENCE_LABELS: Record<string, string> = {
  effect: 'Effect',
  interaction: 'Interaction',
  baseline: 'Baseline',
  car: 'Car data',
  build: 'Build',
  recommendation: 'Guide note',
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white/70 p-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-400">
        {EVIDENCE_LABELS[item.type] ?? item.type}
      </div>
      <div className="text-sm font-semibold leading-snug text-stone-900">{item.title}</div>
      <div className="mt-1 text-xs leading-5 text-stone-600">{item.summary}</div>
    </div>
  )
}

function conversationalLead(likelyCause: string) {
  return `My read: ${likelyCause} I’d avoid changing everything at once — start with the first item below, test a few corners, then move down the list only if the balance still feels wrong.`
}

export default function AnswerPanel({ response }: Props) {
  const { safety, likely_cause, try_in_order, watch_for, evidence } = response

  if (safety.refused) {
    return (
      <div className="rounded-3xl border border-amber-200 bg-amber-50/90 p-5 text-amber-950">
        <p className="mb-1 text-sm font-semibold">I can keep this to tuning.</p>
        <p className="text-sm leading-6">{response.answer}</p>
      </div>
    )
  }

  return (
    <div className="rounded-[26px] border border-stone-200 bg-[#fffdf8] p-4 shadow-[0_16px_42px_rgba(64,48,35,0.08)] sm:p-5">
      <div className="mb-5 flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#8f4b2f] text-xs font-bold text-white">
          HTL
        </div>
        <div>
          <p className="text-sm leading-7 text-stone-700">{conversationalLead(likely_cause)}</p>
        </div>
      </div>

      <section className="rounded-3xl bg-[#f7efe5] p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="text-sm font-semibold text-stone-950">Try first</p>
          <span className="lab-chip bg-white/70">ordered plan</span>
        </div>
        {try_in_order.length > 0 ? (
          <ol className="space-y-3">
            {try_in_order.map((step, i) => (
              <li key={i} className="grid grid-cols-[30px_minmax(0,1fr)] gap-3">
                <span className="lab-mono flex h-7 w-7 items-center justify-center rounded-full bg-white text-[11px] font-semibold text-[#8f4b2f] shadow-sm">
                  {i + 1}
                </span>
                <span className="pt-0.5 text-sm leading-6 text-stone-800">{step}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-sm text-stone-600">I do not have a confident ordered adjustment for this yet.</p>
        )}
      </section>

      {watch_for.length > 0 && (
        <section className="mt-4 rounded-3xl border border-stone-200 bg-white/70 p-4">
          <p className="mb-2 text-sm font-semibold text-stone-950">Watch while testing</p>
          <ul className="space-y-2">
            {watch_for.map((w, i) => (
              <li key={i} className="text-sm leading-6 text-stone-700">
                <span className="mr-2 text-[#8f4b2f]">•</span>{w}
              </li>
            ))}
          </ul>
        </section>
      )}

      {evidence.length > 0 && (
        <details className="mt-4 group rounded-3xl border border-stone-200 bg-white/45 p-4">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-stone-800">
            <span>Why I’m suggesting this</span>
            <span className="text-xs font-medium text-stone-500 group-open:hidden">show evidence</span>
            <span className="hidden text-xs font-medium text-stone-500 group-open:inline">hide evidence</span>
          </summary>
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {evidence.map((ev, i) => (
              <EvidenceCard key={`${ev.type}-${i}`} item={ev} />
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
