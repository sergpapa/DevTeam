---
description: An intermittent bug with no obvious cause must trigger systematic debugging (reproduce, isolate, regression test), not a guessed patch.
tags: [debug]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our nightly billing job sometimes double-charges a customer. It happens about once a week, never on the same customer twice, and we can't tell why. You don't have the repo open, so here is the relevant code.

```ts
// billing/charge.ts
export async function chargeInvoice(db: Db, psp: Psp, invoiceId: string) {
  const last = await db.oneOrNone(
    `SELECT status FROM payments WHERE invoice_id = $1 ORDER BY created_at DESC LIMIT 1`,
    [invoiceId],
  );
  if (last?.status === 'succeeded' || last?.status === 'pending') return last;

  const inv = await db.one(`SELECT customer_id, amount_cents FROM invoices WHERE id = $1`, [invoiceId]);
  const result = await psp.charge({ customer: inv.customer_id, amount: inv.amount_cents }); // ~300-800 ms
  await db.none(
    `INSERT INTO payments (invoice_id, psp_charge_id, status) VALUES ($1, $2, $3)`,
    [invoiceId, result.id, result.status],
  );
  return result;
}

// jobs/nightly.ts — cron, 02:00 UTC
export async function runNightly(db: Db, psp: Psp) {
  const due = await db.many(`SELECT id FROM invoices WHERE due_at <= now() AND paid = false`);
  await Promise.all(due.map((i) => chargeInvoice(db, psp, i.id)));
}

// webhooks/psp.ts — the PSP posts here; it retries a delivery if we don't answer 200 within 5 s
export async function onPspEvent(db: Db, psp: Psp, evt: PspEvent) {
  if (evt.type === 'charge.failed' && evt.retryable) {
    await chargeInvoice(db, psp, evt.metadata.invoice_id);
  }
  if (evt.type === 'charge.succeeded') {
    await db.none(`UPDATE invoices SET paid = true WHERE id = $1`, [evt.metadata.invoice_id]);
  }
}
```

Schema: `payments(id serial, invoice_id text, psp_charge_id text, status text, created_at timestamptz default now())`, no unique constraints beyond the primary key. Fix it.
