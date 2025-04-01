"use client";

import { useRouter } from "next/navigation";
import { Phone, ArrowLeft, HelpCircle } from "lucide-react";

export default function CrisisResourcesPage() {
  const router = useRouter();

  const emergencyResources = [
    {
      name: "National Emergency",
      number: "911",
      description: "For immediate life-threatening emergencies",
      available: "24/7",
    },
    {
      name: "988 Suicide & Crisis Lifeline",
      number: "988",
      description:
        "Free, confidential support for anyone in suicidal crisis or emotional distress",
      available: "24/7",
    },
    {
      name: "Crisis Text Line",
      number: "Text HOME to 741741",
      description: "Free crisis counseling via text message",
      available: "24/7",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-white dark:from-gray-900 dark:via-gray-850 dark:to-gray-800 px-4 py-16">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-transparent bg-clip-text animate-gradient">
            Crisis Resources
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto leading-relaxed">
            If you're experiencing a crisis, help is available right now. These
            resources are here to support you 24/7.
          </p>
        </div>

        {/* Important Notice */}
        <div className="mt-16">
          <div className="bg-red-50 dark:bg-red-900/30 p-8 rounded-2xl border border-red-100 dark:border-red-800 shadow-md hover:shadow-lg transition-shadow duration-300">
            <h2 className="text-2xl font-bold text-red-700 dark:text-red-400 mb-4">
              Important Notice
            </h2>
            <p className="text-red-600 dark:text-red-300 text-lg leading-relaxed">
              If you or someone else is in immediate danger, please call
              emergency services (911) immediately. Don&apos;t wait – your
              safety is the top priority.
            </p>
          </div>
        </div>

        <br />

        {/* Resources Section */}
        <div className="space-y-8">
          {emergencyResources.map((resource, index) => (
            <div
              key={index}
              className="group flex flex-col md:flex-row items-center bg-white/90 dark:bg-gray-800/95 rounded-2xl p-8 shadow-lg backdrop-blur-sm border border-gray-100 dark:border-gray-700 hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
            >
              <div className="flex-1 text-center md:text-left mb-4 md:mb-0">
                <h2 className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                  {resource.name}
                </h2>
                <p className="text-gray-700 dark:text-gray-300 text-lg mb-2">
                  {resource.description}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Available: {resource.available}
                </p>
              </div>
              <div className="w-full md:w-auto">
                <a
                  href={`tel:${resource.number.replace(/\D/g, "")}`}
                  className="w-full md:w-auto inline-flex items-center justify-center gap-3 px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-all duration-300 hover:shadow-lg hover:scale-105"
                  aria-label={`Call ${resource.name}`}
                >
                  <Phone className="w-6 h-6" />
                  <span className="text-lg">{resource.number}</span>
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Back Button */}
        <div className="mt-16 text-center">
          <button
            onClick={() => router.push("/support-pathway")}
            className="inline-flex items-center gap-3 px-6 py-3 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-all duration-300 font-semibold text-lg hover:scale-105"
          >
            <ArrowLeft className="w-6 h-6" />
            Back to Support Pathways
          </button>
        </div>
      </div>
    </div>
  );
}
