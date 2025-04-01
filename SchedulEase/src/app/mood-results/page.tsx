"use client";

import { useRouter, useSearchParams } from "next/navigation";

export default function MoodResultPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mood = searchParams.get('mood');

  const getMoodMessage = (mood: string | null) => {
    switch (mood) {
      case 'happy':
        return "It's great that you're feeling happy! Here are some ways to maintain your positive mood.";
      case 'sad':
        return "It's okay to feel sad. Here are some resources that might help you feel better.";
      case 'angry':
        return "We understand you're feeling angry. Here are some techniques to manage these emotions.";
      case 'anxious':
        return "Feeling anxious is common. Here are some calming exercises you might find helpful.";
      case 'neutral':
        return "A neutral mood is perfectly normal. Here are some activities to explore.";
      default:
        return "Thank you for sharing how you're feeling.";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-8 shadow-lg backdrop-blur-sm border border-gray-100 dark:border-gray-700">
          <h1 className="text-3xl font-bold mb-6 text-blue-600 dark:text-blue-400">
            Your Mood: {mood && mood.charAt(0).toUpperCase() + mood.slice(1)}
          </h1>
          
          <p className="text-gray-700 dark:text-gray-300 text-lg mb-8">
            {getMoodMessage(mood)}
          </p>

          <div className="space-y-4">
            <button
              onClick={() => router.push('/mood-check')}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg text-lg font-medium transition-all duration-300"
            >
              Check Again
            </button>
            
            <button
              onClick={() => router.push('/')}
              className="w-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 px-8 py-3 rounded-lg text-lg font-medium transition-all duration-300"
            >
              Return Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}