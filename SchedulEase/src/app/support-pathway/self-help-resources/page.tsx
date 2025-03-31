"use client";

import { useRouter } from "next/navigation";

export default function SelfHelpPage() {
  const router = useRouter();

  const resources = [
    {
      title: "Guided Meditation",
      description: "Find peace and clarity through our collection of guided meditation sessions, ranging from 5 to 30 minutes.",
      icon: "🧘‍♀️",
      features: ["Beginner-friendly sessions", "Sleep meditation", "Anxiety relief", "Mindfulness practices"]
    },
    {
      title: "Breathing Exercises",
      description: "Learn powerful breathing techniques to reduce stress, increase energy, and improve focus.",
      icon: "🫁",
      features: ["Box breathing", "4-7-8 technique", "Deep breathing", "Stress relief exercises"]
    },
    {
      title: "Journaling Tools",
      description: "Express your thoughts and feelings through guided journaling prompts and reflection exercises.",
      icon: "📔",
      features: ["Daily gratitude prompts", "Mood tracking", "Self-reflection exercises", "Goal setting templates"]
    },
    {
      title: "Wellness Tracker",
      description: "Monitor your daily mental wellness journey and track your progress over time.",
      icon: "📊",
      features: ["Mood tracking", "Habit formation", "Progress insights", "Custom reminders"]
    },
    {
      title: "Sleep Hygiene Guide",
      description: "Learn evidence-based techniques to improve your sleep quality and establish a healthy sleep routine.",
      icon: "😴",
      features: ["Bedtime routines", "Sleep environment optimization", "Relaxation techniques", "Sleep tracking tips"]
    },
    {
      title: "Physical Exercise Library",
      description: "Access a collection of mood-boosting workouts and movement practices suitable for all fitness levels.",
      icon: "🏃‍♀️",
      features: ["Stress-relief exercises", "Yoga sequences", "Walking meditations", "Energy-boosting routines"]
    },
    {
      title: "Cognitive Tools",
      description: "Practice evidence-based cognitive techniques to challenge negative thought patterns and build resilience.",
      icon: "🧠",
      features: ["Thought records", "Cognitive restructuring", "Problem-solving frameworks", "Positive affirmations"]
    },
    {
      title: "Social Connection Tips",
      description: "Discover strategies for building and maintaining meaningful relationships and social support networks.",
      icon: "🤝",
      features: ["Conversation starters", "Boundary setting", "Active listening skills", "Community building"]
    },
    {
      title: "Stress Management Kit",
      description: "Access a comprehensive toolkit of stress management techniques for different situations and triggers.",
      icon: "🎯",
      features: ["Quick relief techniques", "Long-term strategies", "Workplace stress tools", "Crisis management"]
    },
    {
      title: "Creative Expression",
      description: "Explore various creative outlets and art therapy techniques for emotional expression and healing.",
      icon: "🎨",
      features: ["Art therapy prompts", "Music therapy", "Writing exercises", "Movement therapy"]
    },
    {
      title: "Nutrition & Mood",
      description: "Learn about the connection between nutrition and mental health, with practical tips for mood-supporting foods.",
      icon: "🥗",
      features: ["Mood-boosting foods", "Meal planning", "Mindful eating", "Hydration tracking"]
    },
    {
      title: "Mindful Living Guide",
      description: "Incorporate mindfulness into daily activities and develop a more present-centered approach to life.",
      icon: "🌱",
      features: ["Daily mindfulness practices", "Mindful communication", "Nature connection", "Digital wellness"]
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
            Self-Help Resources
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Discover tools and techniques to support your mental wellness journey. Practice at your own pace and build healthy daily habits.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {resources.map((resource, index) => (
            <div
              key={index}
              className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-8 shadow-lg 
                hover:shadow-xl transition-all duration-300 backdrop-blur-sm 
                border border-gray-100 dark:border-gray-700
                hover:scale-[1.02] hover:-translate-y-1 cursor-pointer"
            >
              <div className="flex items-start gap-4">
                <span className="text-4xl" role="img" aria-label="icon">
                  {resource.icon}
                </span>
                <div>
                  <h2 className="text-2xl font-semibold mb-3 text-blue-600 dark:text-blue-400">
                    {resource.title}
                  </h2>
                  <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed mb-4">
                    {resource.description}
                  </p>
                  <ul className="space-y-2">
                    {resource.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-center text-gray-600 dark:text-gray-400">
                        <span className="mr-2">•</span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <button
            onClick={() => router.push("/support-pathway")}
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
          >
            <span className="mr-2">←</span> Back to Support Pathways
          </button>
        </div>
      </div>
    </div>
  );
}