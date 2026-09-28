// Sample for tools/consistency_check.py: every value is on the spacing and type
// scales (so the token lint passes), but the card padding and heading style
// don't match DashboardActivity.tsx or their roles.
import { Card } from "@/components/ui/card";

export function KpiDetails({ kpi }) {
  return (
    <section className="mt-12">
      <h2 className="text-2xl font-semibold text-slate-900">{kpi.label} in detail</h2>
      <Card className="p-6 gap-2">
        <p className="text-base font-normal">{kpi.summary}</p>
      </Card>
    </section>
  );
}
