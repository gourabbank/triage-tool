const API_BASE = "http://localhost:8000";

function requireEl<T extends HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Expected element #${id} to exist`);
  return el as T;
}

requireEl<HTMLButtonElement>("submit-btn").addEventListener("click", async () => {
  const text = requireEl<HTMLTextAreaElement>("raw_text").value;
  const res = await fetch(`${API_BASE}/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_text: text }),
  });
  const data = await res.json();
  requireEl<HTMLElement>("result").innerText = JSON.stringify(data, null, 2);
});

requireEl<HTMLButtonElement>("load-queue-btn").addEventListener("click", async () => {
  const res = await fetch(`${API_BASE}/requests`);
  const data = await res.json();
  requireEl<HTMLElement>("queue").innerText = JSON.stringify(data, null, 2);
});