import { openDB } from "idb";
import api, { type CaseCreate } from "./api";

// Offline queue (G11): forms are stored on the phone and synced when internet returns.

const STORE = "queued_cases";
const getDb = () =>
  openDB("rahbar-offline", 1, {
    upgrade(db) {
      db.createObjectStore(STORE, { keyPath: "local_id" });
    },
  });

export async function queueCase(data: CaseCreate & { citizen_id: string }) {
  const db = await getDb();
  await db.put(STORE, { ...data, local_id: crypto.randomUUID(), queued_at: new Date().toISOString() });
}

export async function queuedCount(): Promise<number> {
  try {
    return (await getDb()).count(STORE);
  } catch {
    return 0;
  }
}

/** Send everything queued to the server. Returns how many were synced. */
export async function flushQueue(helperId: string): Promise<number> {
  const db = await getDb();
  const items = await db.getAll(STORE);
  if (items.length === 0) return 0;
  const batchId = `batch-${items[0].local_id}`; // same id on retry => server can de-duplicate
  await api.syncOfflineBatch(helperId, batchId, items);
  const tx = db.transaction(STORE, "readwrite");
  await Promise.all(items.map((i) => tx.store.delete(i.local_id)));
  await tx.done;
  return items.length;
}