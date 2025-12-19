import { useState } from "react";
import { submitForm } from "../services/api";

type Question = {
  text: string;
  options: string[];
};

const questions: Question[] = [
  {
    text: "Frage 1: Welche IDE bevorzugst du?",
    options: ["VSCode", "IntelliJ", "Sublime Text"],
  },
  {
    text: "Frage 2: Frontend, Backend, Fullstack?",
    options: ["Frontend", "Backend", "Fullstack"],
  },
  {
    text: "Frage 3: Programmiersprache",
    options: ["JavaScript", "Python", "Java"],
  },
  {
    text: "Frage 4: Testing Framework?",
    options: ["Jest", "Mocha", "Cypress"],
  },
  { text: "Frage 5: CI?", options: ["Jenkins", "GitHub Actions", "GitLab CI"] },
];

export default function MultiStepForm() {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<string[]>(
    Array(questions.length).fill("")
  );

  const handleOptionSelect = (option: string) => {
    const newAnswers = [...answers];
    newAnswers[currentStep] = option;
    setAnswers(newAnswers);
  };

  const handleNext = async () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      const res = await submitForm(answers);
      console.log(res);
      alert("Formular abgeschlossen! Antworten: " + answers.join(", "));
      // Hier kannst du die Daten ans Backend senden
    }
  };

  const currentQuestion = questions[currentStep];

  return (
    <div className="max-w-md mx-auto mt-16 p-6 bg-gray-600 rounded-xl shadow-md">
      <h2 className="text-xl font-bold mb-4">{currentQuestion.text}</h2>

      <div className="space-y-2 mb-6">
        {currentQuestion.options.map((option) => (
          <button
            key={option}
            onClick={() => handleOptionSelect(option)}
            className={`w-full py-2 px-4 rounded-lg border transition-colors
              ${
                answers[currentStep] === option
                  ? "bg-blue-500 text-white border-blue-500"
                  : "bg-white text-gray-600 border-gray-300 hover:bg-gray-100"
              }`}
          >
            {option}
          </button>
        ))}
      </div>

      <button
        onClick={handleNext}
        disabled={!answers[currentStep]}
        className={`w-full py-2 px-4 rounded-lg text-white font-semibold transition-colors
          ${
            answers[currentStep]
              ? "bg-blue-600 hover:bg-blue-700"
              : "bg-gray-300 cursor-not-allowed"
          }`}
      >
        {currentStep < questions.length - 1 ? "Weiter" : "Abschließen"}
      </button>

      <div className="mt-4 text-gray-500 text-sm">
        Schritt {currentStep + 1} von {questions.length}
      </div>
    </div>
  );
}
