'use client';

import { useEffect, useState } from "react";
import { Clock, GraduationCap, Award } from "lucide-react";
import { useRouter } from 'next/navigation';

interface ProgressResponse {
  success: boolean;
  message: string;
  data: {
    total_credits: number;
    total_courses: number;
    current_grade: string;
    completed_courses: {
      [courseId: string]: string;  // Key-value pairs of course ID to course name
    };
    programming_experience: {
      [language: string]: number;
    };
    math_experience: {
      [subject: string]: number;
    };
    course_outcomes: string[];
  }
}

export default function AcademicProgressPage() {
  const router = useRouter();
  const [progressData, setProgressData] = useState<ProgressResponse['data'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchProgressData = async () => {
      try {
        const userData = localStorage.getItem('userData');
        if (!userData) {
          router.push('/login');
          return;
        }

        const { nuid } = JSON.parse(userData);
        const response = await fetch(`http://localhost:8000/progress/${nuid}`);
        const responseData: ProgressResponse = await response.json();
        console.log('Progress data:', responseData);

        if (!response.ok) {
          throw new Error(responseData.message || 'Failed to fetch progress data');
        }

        setProgressData(responseData.data);
      } catch (err) {
        console.error('Error fetching progress data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load progress data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProgressData();
  }, [router]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  if (error) {
    return <div className="text-red-600 text-center p-4">{error}</div>;
  }

  if (!progressData) {
    return <div className="text-center p-4">No progress data available</div>;
  }

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      <div className="text-center sm:text-left">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Academic Progress
        </h1>
        <p className="mt-2 text-gray-600">Track your academic achievements and progress</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Credits Card with Progress Bar */}
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center mb-4">
            <Clock className="h-8 w-8 text-blue-500" />
            <h2 className="ml-3 text-xl font-semibold text-gray-900">Total Credits</h2>
          </div>
          <div className="mt-2">
            <div className="flex justify-between items-center">
              <div className="text-3xl font-bold text-blue-700">
                {progressData.total_credits}
              </div>
              <span className="text-blue-600 font-medium">out of 32</span>
            </div>
            <p className="text-gray-600 mt-1">Credits completed</p>
          </div>
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-blue-700 font-medium">
                {Math.round((progressData.total_credits / 32) * 100)}% Complete
              </span>
              <span className="text-blue-600">
                {32 - progressData.total_credits} credits remaining
              </span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${(progressData.total_credits / 32) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Courses Card */}
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center mb-4">
            <GraduationCap className="h-8 w-8 text-green-500" />
            <h2 className="ml-3 text-xl font-semibold text-gray-900">Total Courses</h2>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-green-700">
              {progressData.total_courses}
            </div>
            <p className="text-gray-600 mt-1">Courses completed</p>
          </div>
        </div>

        {/* Grade Card */}
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300">
          <div className="flex items-center mb-4">
            <Award className="h-8 w-8 text-purple-500" />
            <h2 className="ml-3 text-xl font-semibold text-gray-900">Current Grade</h2>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-purple-700">
              {progressData.current_grade}
            </div>
            <p className="text-gray-600 mt-1">Current Letter Grade</p>
          </div>
        </div>
      </div>

      {/* Completed Courses Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Completed Courses
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(progressData.completed_courses).map(([courseId, courseName]) => (
            <div 
              key={courseId}
              className="bg-gradient-to-br from-gray-50 to-gray-100 p-4 rounded-lg border border-gray-200 hover:border-blue-500 hover:shadow-md transition-all duration-300"
            >
              <h3 className="font-medium text-blue-600">{courseId}</h3>
              <p className="text-gray-700 mt-1">
                {courseName === courseId ? 'Course name not available' : courseName}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Programming Experience Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Programming Experience
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(progressData.programming_experience).map(([language, score]) => (
            <div key={language} className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg hover:shadow-md transition-all duration-300">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-900">{language}</h3>
                <span className="text-blue-700 font-semibold">{score.toFixed(1)}/5.0</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2.5">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2.5 rounded-full shadow-sm"
                  style={{ width: `${(score / 5) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Math Experience Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Mathematics Experience
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(progressData.math_experience).map(([subject, score]) => (
            <div key={subject} className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-lg hover:shadow-md transition-all duration-300">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium text-gray-900">{subject}</h3>
                <span className="text-green-700 font-semibold">{score.toFixed(1)}/5.0</span>
              </div>
              <div className="w-full bg-green-200 rounded-full h-2.5">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2.5 rounded-full shadow-sm"
                  style={{ width: `${(score / 5) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Course Outcomes Section */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
          Learning Outcomes Achieved
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {progressData.course_outcomes.map((outcome, index) => (
            <div 
              key={index}
              className="flex items-center space-x-3 bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-lg hover:shadow-md transition-all duration-300"
            >
              <div className="flex-shrink-0 w-8 h-8 bg-purple-200 rounded-full flex items-center justify-center">
                <span className="text-purple-700 text-sm font-medium">{index + 1}</span>
              </div>
              <p className="text-gray-700 flex-1">{outcome}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}