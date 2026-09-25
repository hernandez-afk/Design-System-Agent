// Sample UI file for the dev-time tools. It carries the DES-512 audit's
// spacing bug (gap-5 = 20px) and an off-brand color, so token_lint.py has
// something to catch. See the README's "Consistency during development".
import { StatTile } from "@/components/stat-tile";

export function DashboardSummaryRow({ kpis }) {
  return (
    <section className="grid grid-cols-2 md:grid-cols-4 gap-5 p-4 bg-slate-50">
      {kpis.map((k) => (
        <StatTile key={k.label} {...k} className="rounded-lg border border-slate-200 text-slate-900" />
      ))}
      <a className="text-blue-500 mt-6" style={{ color: "#3B82F6" }} href="/reports">All reports</a>
    </section>
  );
}
