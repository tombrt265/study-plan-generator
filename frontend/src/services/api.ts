const API_URL = import.meta.env.VITE_API_BASE_URL;

export async function submitForm(answers: string[]) {
  const res = await fetch(`${API_URL}/submit-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers }),
  });
  return res.json();
}
