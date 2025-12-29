const API_URL = import.meta.env.VITE_API_BASE_URL;
import type { StudyPlan } from "../models";

export async function extractStudyMaterial(
  formData: FormData
): Promise<{ text: string }> {
  const res = await fetch(`${API_URL}/extract-study-material`, {
    method: "POST",
    body: formData,
  });
  return res.json();
}

export async function createStudyPlan(text: string): Promise<StudyPlan> {
  const res = await fetch(`${API_URL}/create-study-plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ study_material: text }),
  });
  return res.json();
}
