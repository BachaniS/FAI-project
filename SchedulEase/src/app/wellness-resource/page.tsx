"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface Resource {
  title: string;
  description: string;
  link: string;
  category: string;
}

export default function WellnessResourcesPage() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);

  const resources: Resource[] = [
    {
      title: "Crisis Text Line",
      description: "24/7 text support with trained crisis counselors",
      link: "https://www.crisistextline.org/",
      category: "Crisis Support",
    },
    {
      title: "National Suicide Prevention Lifeline",
      description: "24/7 support for people in distress",
      link: "https://988lifeline.org/",
      category: "Crisis Support",
    },
    {
      title: "Headspace",
      description: "Guided meditation and mindfulness exercises",
      link: "https://www.headspace.com/",
      category: "Meditation",
    },
    {
      title: "Calm",
      description: "Sleep stories, meditation, and relaxation",
      link: "https://www.calm.com/",
      category: "Meditation",
    },
    {
      title: "Nike Training Club",
      description: "Free workouts and fitness guidance",
      link: "https://www.nike.com/ntc-app",
      category: "Exercise",
    },
    {
      title: "BetterHelp",
      description: "Online counseling and therapy services",
      link: "https://www.betterhelp.com/",
      category: "Therapy",
    },
  ];

  const categories = Array.from(new Set(resources.map((r) => r.category)));

  useEffect(() => {
    // Trigger the fade-in effect on page load
    const timer = setTimeout(() => setIsLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className={`min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16 transition-opacity duration-500 ${
        isLoaded ? "opacity-100" : "opacity-0"
      }`}
    >
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-bold mb-8 text-center bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text [-webkit-background-clip:text] drop-shadow-md">
          Wellness Resources
        </h1>

        <p className="text-center text-gray-600 dark:text-gray-300 mb-12 text-lg">
          Find support and resources to help you on your wellness journey.
        </p>

        <div className="grid grid-cols-1 gap-8">
          {categories.map((category, index) => (
            <div
              key={category}
              className={`bg-white/50 dark:bg-gray-800/50 rounded-2xl p-8 backdrop-blur-sm transition-transform duration-500 delay-[${
                index * 100
              }ms] ${
                isLoaded ? "translate-y-0" : "translate-y-10 opacity-0"
              }`}
            >
              <h2 className="text-2xl font-bold mb-6 text-gray-800 dark:text-gray-100 border-b border-blue-500 pb-2">
                {category}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {resources
                  .filter((resource) => resource.category === category)
                  .map((resource) => (
                    <a
                      key={resource.title}
                      href={resource.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-6 bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-lg 
                        transition-all duration-300 hover:scale-105 border border-gray-100 dark:border-gray-700
                        hover:border-blue-500 dark:hover:border-blue-500"
                    >
                      <h3 className="text-xl font-semibold text-blue-600 dark:text-blue-400 mb-2 flex items-center">
                        {resource.title}
                        <svg
                          className="w-4 h-4 ml-2 transition-transform duration-300 group-hover:translate-x-2"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                          />
                        </svg>
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300">
                        {resource.description}
                      </p>
                    </a>
                  ))}
              </div>
            </div>
          ))}
        </div>

        <button
          onClick={() => router.back()}
          className="mt-8 float-right px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-300"
        >
          ← Go to Home
        </button>
      </div>
    </div>
  );
}