"use client";

import { useRouter } from "next/navigation";

export default function MoodCheckPage() {
  const router = useRouter();

  const moods = [
    { emoji: "😊", label: "Happy", color: "from-green-400 to-green-500" },
    { emoji: "😔", label: "Sad", color: "from-blue-400 to-blue-500" },
    { emoji: "😡", label: "Angry", color: "from-red-400 to-red-500" },
    { emoji: "😰", label: "Anxious", color: "from-yellow-400 to-yellow-500" },
    { emoji: "😐", label: "Neutral", color: "from-gray-400 to-gray-500" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-bold mb-8 text-center bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
          How are you feeling?
        </h1>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mt-12">
          {moods.map((mood) => (
            <button
              key={mood.label}
              onClick={() => router.push(`/mood-results/${mood.label.toLowerCase()}`)}
              className={`bg-gradient-to-r ${mood.color} hover:opacity-90 text-white p-8 rounded-xl flex flex-col items-center gap-4 transition-all duration-300 transform hover:scale-105 shadow-md`}
            >
              <span className="text-5xl">{mood.emoji}</span>
              <span className="text-xl font-medium">{mood.label}</span>
            </button>
          ))}
        </div>

        <button
          onClick={() => router.back()}
          className="mt-12 mx-auto block text-blue-600 dark:text-blue-400 hover:underline"
        >
          ← Go back
        </button>
      </div>
    </div>
  );
}