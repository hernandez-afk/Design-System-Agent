// Sample for tools/consistency_check.py: on-token, and consistent with its roles.
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DashboardActivity({ items }) {
  return (
    <section className="mt-12">
      <h2 className="text-xl font-bold text-slate-900">Recent activity</h2>
      <Card className="p-4 gap-2">
        {items.map((i) => <p key={i.id} className="text-base font-normal">{i.text}</p>)}
        <Button className="px-4 py-2">See all activity</Button>
      </Card>
    </section>
  );
}
