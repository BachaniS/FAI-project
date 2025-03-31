"use client";

import { useParams, useRouter } from "next/navigation";

const moodContent = {
  happy: {
    title: "Embracing Your Happiness!",
    emoji: "😊",
    color: "from-green-400 to-green-500",
    content: [
      "It's wonderful that you're feeling happy! Here are some ways to maintain this positive energy:",
      "• Share your joy with others - happiness is contagious!",
      "• Document this moment in a gratitude journal",
      "• Channel this energy into a creative project",
      "• Take a moment to appreciate what made you happy"
    ]
  },
  sad: {
    title: "Finding Light in Difficult Moments",
    emoji: "😔",
    color: "from-blue-400 to-blue-500",
    content: [
      "It's okay to feel sad. Here are some gentle suggestions that might help:",
      "• Practice self-compassion - treat yourself with kindness",
      "• Reach out to a friend or family member",
      "• Try some light exercise or a short walk",
      "• Consider talking to a mental health professional"
    ]
  },
  angry: {
    title: "Managing Your Anger Constructively",
    emoji: "😡",
    color: "from-red-400 to-red-500",
    content: [
      "Anger is a natural emotion. Here are some healthy ways to process it:",
      "• Take deep breaths - try counting to 10",
      "• Go for a run or do some physical exercise",
      "• Write down your thoughts and feelings",
      "• Remove yourself from triggering situations"
    ]
  },
  anxious: {
    title: "Finding Calm in the Storm",
    emoji: "😰",
    color: "from-yellow-400 to-yellow-500",
    content: [
      "Feeling anxious is challenging. Here are some grounding techniques:",
      "• Practice the 5-4-3-2-1 sensory exercise",
      "• Try some gentle breathing exercises",
      "• Listen to calming music or nature sounds",
      "• Focus on what you can control"
    ]
  },
  neutral: {
    title: "Finding Balance in Neutrality",
    emoji: "😐",
    color: "from-gray-400 to-gray-500",
    content: [
      "A neutral mood can be a good foundation. Here are some ideas:",
      "• Explore new interests or hobbies",
      "• Set some goals for the future",
      "• Practice mindfulness",
      "• Connect with nature"
    ]
  }
};

export default function MoodResultPage() {
  const router = useRouter();
  const params = useParams();
  const mood = params.mood as string;
  const currentMood = moodContent[mood as keyof typeof moodContent];

  if (!currentMood) {
    return <div>Mood not found</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-4xl mx-auto">
        <div
          className={`bg-gradient-to-r ${currentMood.color} p-8 rounded-xl text-white text-center mb-8`}
        >
          <span className="text-6xl block mb-4">{currentMood.emoji}</span>
          <h1 className="text-3xl md:text-4xl font-bold">
            {currentMood.title}
          </h1>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg">
          {currentMood.content.map((text, index) => (
            <p
              key={index}
              className="text-gray-700 dark:text-gray-300 mb-4 text-lg"
            >
              {text}
            </p>
          ))}
        </div>

        <button
          onClick={() => router.back()}
          className="mt-8 mx-auto block text-blue-600 dark:text-blue-400 hover:underline"
        >
          ← Go back
        </button>
        <button
          onClick={() => router.push("/homepage")}
          className="mt-8 mx-auto block text-blue-600 dark:text-blue-400 hover:underline"
        >
          Go to Homepage;
        </button>
      </div>
    </div>
  );
}