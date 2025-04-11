'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Book, Brain, Star, AlertCircle } from 'lucide-react';

interface CourseRecommendation {
  subject_id: string;
  name: string;
  credits: number;
  burnout_risk: number;
  utility_score: number;
  prerequisites?: string[];
  description?: string;
}

export default function CourseRecommendationsPage() {
  const router = useRouter();
  const [recommendations, setRecommendations] = useState<CourseRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const userData = localStorage.getItem('userData');
        if (!userData) {
          router.push('/login');
          return;
        }

        const { nuid } = JSON.parse(userData);
        const response = await fetch(
          `http://localhost:8000/recommendations/${nuid}`
        );
        const data = await response.json();

        console.log('Recommendations data:', data);

        if (!response.ok) {
          throw new Error(data.message || 'Failed to fetch recommendations');
        }

        setRecommendations(data);
      } catch (err) {
        console.error('Error fetching recommendations:', err);
        setError(err instanceof Error ? err.message : 'Failed to load recommendations');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600 text-center p-4">
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        {error}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Course Recommendations</h1>
        <p className="mt-2 text-gray-600">
          Personalized course suggestions based on your profile and interests
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {recommendations.map((course) => (
          <div
            key={course.subject_id}
            className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden"
          >
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    {course.name}
                  </h2>
                  <p className="text-sm text-gray-600 mb-4">
                    {course.subject_id}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                {/* Credits */}
                <div className="flex items-center text-gray-700">
                  <Book className="h-5 w-5 mr-2" />
                  <span>{course.credits} Credits</span>
                </div>

                {/* Utility Score */}
                <div className="flex items-center">
                  <Star className="h-5 w-5 mr-2 text-yellow-500" />
                  <div className="flex-1">
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-2 bg-yellow-500 rounded-full"
                        style={{ width: `${(course.utility_score * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Utility Score: {(course.utility_score * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Burnout Risk */}
                <div className="flex items-center">
                  <Brain className="h-5 w-5 mr-2 text-blue-500" />
                  <div className="flex-1">
                    <div className="h-2 bg-gray-200 rounded-full">
                      <div
                        className={`h-2 rounded-full ${getBurnoutColor(course.burnout_risk)}`}
                        style={{ width: `${(course.burnout_risk * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      Burnout Risk: {(course.burnout_risk * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                {/* Prerequisites */}
                {course.prerequisites && course.prerequisites.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-1">Prerequisites:</p>
                    <div className="flex flex-wrap gap-2">
                      {course.prerequisites.map((prereq) => (
                        <span
                          key={prereq}
                          className="px-2 py-1 bg-gray-100 rounded-full text-xs text-gray-600"
                        >
                          {prereq}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Description */}
                {course.description && (
                  <p className="text-sm text-gray-600 mt-4">
                    {course.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getBurnoutColor(risk: number): string {
  if (risk >= 0.7) return 'bg-red-500';
  if (risk >= 0.4) return 'bg-yellow-500';
  return 'bg-green-500';
} 