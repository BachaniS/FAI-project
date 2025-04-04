'use client';

import Link from 'next/link';
import { UserPlus, LogIn } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            SchedulEase
          </h1>
          <p className="text-lg text-gray-600">
            Your AI-powered course recommendation system
          </p>
        </div>

        <div className="space-y-4">
          <Link 
            href="/login" 
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors shadow-lg hover:shadow-xl"
          >
            <LogIn className="w-5 h-5" />
            <span className="text-lg font-medium">Already a registered user?</span>
          </Link>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gradient-to-b from-blue-50 to-white text-gray-500">or</span>
            </div>
          </div>

          <Link 
            href="/register" 
            className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-white text-blue-600 border-2 border-blue-600 rounded-xl hover:bg-blue-50 transition-colors shadow-lg hover:shadow-xl"
          >
            <UserPlus className="w-5 h-5" />
            <span className="text-lg font-medium">Sign up as a new user</span>
          </Link>
        </div>

        <div className="mt-12 text-center space-y-2">
          <p className="text-gray-600 font-medium">What you'll get:</p>
          <div className="text-sm text-gray-500">
            <p>✓ Personalized course recommendations</p>
            <p>✓ Smart schedule planning</p>
            <p>✓ Burnout risk analysis</p>
            <p>✓ Academic progress tracking</p>
          </div>
        </div>
      </div>
    </div>
  );
}
