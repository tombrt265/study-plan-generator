import { useState } from "react";
import { extractStudyMaterial, createStudyPlan } from "./services/api";
import type { StudyPlan } from "./models";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [studyMaterial, setStudyMaterial] = useState("");
  const [studyPlan, setStudyPlan] = useState<StudyPlan | string>("");
  const [loading, setLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setStudyMaterial("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await extractStudyMaterial(formData);
      setStudyMaterial(res.text ?? "Kein Text zurückgegeben.");
    } catch {
      setStudyMaterial("Fehler beim Extrahieren.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async () => {
    if (!studyMaterial) return;

    setPlanLoading(true);
    setStudyPlan("");

    try {
      const res = await createStudyPlan(studyMaterial);
      setStudyPlan(res ?? "Kein Graph-Text zurückgegeben.");
    } catch {
      setStudyPlan("Fehler beim Erstellen des Knowledge Graphs.");
    } finally {
      setPlanLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-16 p-6 bg-white rounded-lg shadow-md font-sans">
      <h1 className="text-3xl font-bold text-center mb-8">study planner v1</h1>

      {/* File Upload */}
      <label
        htmlFor="fileUpload"
        className="flex items-center justify-center gap-3 p-4 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition"
      >
        <span className="text-2xl">📄</span>
        <span className="text-gray-700">
          {file ? file.name : "PDF auswählen"}
        </span>
      </label>
      <input
        id="fileUpload"
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!file || loading}
        className={`w-full mt-4 py-3 rounded-lg font-semibold text-white transition
          ${
            file && !loading
              ? "bg-green-600 hover:bg-green-700"
              : "bg-gray-400 cursor-not-allowed"
          }`}
      >
        {loading ? "Verarbeite..." : "PDF hochladen"}
      </button>

      {/* Extracted Text */}
      <textarea
        value={studyMaterial}
        readOnly
        placeholder="Extrahierter Text erscheint hier..."
        className="w-full h-64 mt-6 p-3 border rounded-lg resize-y border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-400"
      />

      {/* Study Plan Button */}
      <button
        onClick={handleCreatePlan}
        disabled={!studyMaterial || planLoading}
        className={`w-full mt-4 py-3 rounded-lg font-semibold text-white transition
          ${
            studyMaterial && !planLoading
              ? "bg-blue-600 hover:bg-blue-700"
              : "bg-gray-400 cursor-not-allowed"
          }`}
      >
        {planLoading ? "Erstelle Study Plan..." : "Study Plan erstellen"}
      </button>

      {/* Study Plan Output */}
      {typeof studyPlan === "string" ? (
        <textarea
          value={studyPlan}
          readOnly
          placeholder="Study Plan Output erscheint hier..."
          className="w-full h-64 mt-6 p-3 border rounded-lg resize-y border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      ) : (
        <div className="mt-6 p-6 bg-gray-50 rounded-lg prose max-w-none">
          <h2>Study Plan Overview</h2>
          <p>{studyPlan.overview}</p>
          <h3>Sessions:</h3>
          {studyPlan.sessions.map((session, index) => (
            <div key={index} className="mb-4">
              <h4>
                {session.topic.name} ({session.duration_minutes} minutes)
              </h4>
              <p>{session.information}</p>
              <p>
                <strong>Methods:</strong> {session.methods.join(", ")}
              </p>
            </div>
          ))}
          <h4>Total Duration: {studyPlan.total_duration_hours} hours</h4>
        </div>
      )}
    </div>
  );
}
