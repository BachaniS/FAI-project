'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  BookOpen, 
  Calendar, 
  GraduationCap, 
  LineChart, 
  User,
  Brain,
  Settings,
  CheckCircle,
  LogOut
} from "lucide-react";

interface UserProfile {
  nuid: string;
  fullName: string;
  programmingSkills: { name: string; proficiency: number }[];
  mathSkills: { name: string; proficiency: number }[];
  completedCourses: string[];
}

export default function DashboardPage() {
  const router = useRouter();
  const [userData, setUserData] = useState<UserProfile | null>(null);

  useEffect(() => {
    // Get user data from localStorage
    const storedUserData = localStorage.getItem('userData');
    if (storedUserData) {
      setUserData(JSON.parse(storedUserData));
    } else {
      // If no user data, redirect to login
      router.push('/login');
    }
  }, [router]);

  const handleLogout = () => {
    // Clear all localStorage data
    localStorage.clear();
    // Reset user state
    setUserData(null);
    // Redirect to login page
    router.push('/login');
  };

  if (!userData) {
    return <div>Loading...</div>;
  }

  const navigationCards = [
    {
      title: 'My Schedule',
      description: 'View and manage your course schedule',
      icon: Calendar,
      href: '/schedule',
      color: 'blue'
    },
    {
      title: 'Course Catalog',
      description: 'Browse available courses',
      icon: BookOpen,
      href: '/courses',
      color: 'green'
    },
    {
      title: 'Academic Progress',
      description: 'Track your degree completion',
      icon: GraduationCap,
      href: '/progress',
      color: 'purple'
    },
    {
      title: 'Burnout Analysis',
      description: 'Monitor your academic stress',
      icon: Brain,
      href: '/burnout',
      color: 'red'
    },
    {
      title: 'Profile Settings',
      description: 'Manage your account',
      icon: Settings,
      href: '/settings',
      color: 'gray'
    },
    {
      title: 'Course Recommendations',
      description: 'Get personalized suggestions',
      icon: CheckCircle,
      href: '/recommendations',
      color: 'indigo'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Welcome Section with Logout Button */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Welcome, {userData.fullName}!</h1>
                <p className="text-gray-600">NUID: {userData.nuid}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span>Logout</span>
            </button>
          </div>
        </div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {navigationCards.map((card) => (
            <Link
              key={card.title}
              href={card.href}
              className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
            >
              <div className="flex items-center space-x-4">
                <div className={`h-12 w-12 bg-${card.color}-100 rounded-lg flex items-center justify-center`}>
                  <card.icon className={`h-6 w-6 text-${card.color}-600`} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{card.title}</h3>
                  <p className="text-sm text-gray-500">{card.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Skills Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Programming Skills</h2>
            <div className="space-y-2">
              {userData.programmingSkills?.map((skill, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span>{skill.name}</span>
                  <div className="flex space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`h-2 w-6 rounded ${
                          i < skill.proficiency ? 'bg-blue-500' : 'bg-gray-200'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Math Skills</h2>
            <div className="space-y-2">
              {userData.mathSkills?.map((skill, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span>{skill.name}</span>
                  <div className="flex space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className={`h-2 w-6 rounded ${
                          i < skill.proficiency ? 'bg-green-500' : 'bg-gray-200'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 