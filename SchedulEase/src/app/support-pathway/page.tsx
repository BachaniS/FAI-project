"use client";

import { useRouter } from "next/navigation";

export default function SupportPathwayPage() {
  const router = useRouter();

  const pathways = [
    {
      title: "Self-Help Resources",
      description: "Access guided meditation, breathing exercises, and journaling tools to support your daily mental wellness routine.",
      icon: "🧘‍♀️",
      link: "/support-pathway/self-help-resources"
    },
    {
      title: "Peer Support Groups",
      description: "Connect with others who share similar experiences in a safe, moderated environment.",
      icon: "👥",
      link: "/support-pathway/peer-support-groups"
    },
    {
      title: "Crisis Resources",
      description: "Immediate support and helpline information for urgent mental health needs.",
      icon: "🆘",
      link: "/support-pathway/crisis-resource"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 px-4 py-16">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text">
            Support Pathways
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Everyone's journey is unique. Explore different support options and find what works best for you.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {pathways.map((pathway, index) => (
            <div
              key={index}
              onClick={() => router.push(pathway.link)}
              className="bg-white/80 dark:bg-gray-800/90 rounded-xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-102 cursor-pointer backdrop-blur-sm border border-gray-100 dark:border-gray-700"
            >
              <div className="flex items-start gap-4">
                <span className="text-4xl" role="img" aria-label="icon">
                  {pathway.icon}
                </span>
                <div>
                  <h2 className="text-2xl font-semibold mb-3 text-blue-600 dark:text-blue-400">
                    {pathway.title}
                  </h2>
                  <p className="text-gray-700 dark:text-gray-300 text-lg leading-relaxed">
                    {pathway.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <button
            onClick={() => router.push("/")}
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
          >
            <span className="mr-2">←</span> Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}