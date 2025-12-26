import { useState } from "react";
import { extractStudyMaterial, createKnowledgeGraph } from "./services/api";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [graphText, setGraphText] = useState("");
  const [loading, setLoading] = useState(false);
  const [graphLoading, setGraphLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setText("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await extractStudyMaterial(formData);
      setText(res.text ?? "Kein Text zurückgegeben.");
    } catch {
      setText("Fehler beim Extrahieren.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGraph = async () => {
    if (!text) return;

    setGraphLoading(true);
    setGraphText("");

    try {
      const res = await createKnowledgeGraph(text);
      setGraphText(res.text ?? "Kein Graph-Text zurückgegeben.");
    } catch {
      setGraphText("Fehler beim Erstellen des Knowledge Graphs.");
    } finally {
      setGraphLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-16 p-6 bg-white rounded-lg shadow-md font-sans">
      <h1 className="text-3xl font-bold text-center mb-8">
        material extracter v1
      </h1>

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
        value={text}
        readOnly
        placeholder="Extrahierter Text erscheint hier..."
        className="w-full h-64 mt-6 p-3 border rounded-lg resize-y border-gray-300 focus:outline-none focus:ring-2 focus:ring-green-400"
      />

      {/* Knowledge Graph Button */}
      <button
        onClick={handleCreateGraph}
        disabled={!text || graphLoading}
        className={`w-full mt-4 py-3 rounded-lg font-semibold text-white transition
          ${
            text && !graphLoading
              ? "bg-blue-600 hover:bg-blue-700"
              : "bg-gray-400 cursor-not-allowed"
          }`}
      >
        {graphLoading
          ? "Erstelle Knowledge Graph..."
          : "Knowledge Graph erstellen"}
      </button>

      {/* Knowledge Graph Output */}
      <textarea
        value={graphText}
        readOnly
        placeholder="Knowledge Graph Output erscheint hier..."
        className="w-full h-64 mt-6 p-3 border rounded-lg resize-y border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
    </div>
  );
}
