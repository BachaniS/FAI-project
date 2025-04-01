'use client'

import {useUser } from "@clerk/nextjs"
import { FaEnvelope, FaUser, FaCrown, FaBell, FaHistory, FaCog } from "react-icons/fa"
import { useState } from "react"
import { motion } from "framer-motion"
import { Code, Calculator, Target } from "lucide-react"
import type { LucideIcon } from "lucide-react"

export default function ProfilePage() {
  const { user } = useUser()

  if (!user) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">Please sign in to view your profile</h2>
          <p className="mt-2 text-gray-600">You need to be authenticated to access this page</p>
        </div>
      </div>
    )
  }

  const subscriptionTiers = [
    {
      name: 'Basic',
      price: '$9.99/mo',
      features: ['Basic Features', 'Email Support', 'Limited Access'],
      color: 'bg-blue-500'
    },
    {
      name: 'Pro',
      price: '$19.99/mo',
      features: ['All Basic Features', 'Priority Support', 'Full Access', 'Advanced Analytics'],
      color: 'bg-purple-500'
    }
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Academic Profile</h1>
        <p className="mt-2 text-gray-600">
          Manage your academic information and preferences
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900">Personal Information</h2>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Full Name</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  value={user.fullName || `${user.firstName} ${user.lastName}`}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Email</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  value={user.primaryEmailAddress?.emailAddress}
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Program</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  value="MS in Computer Science"
                  readOnly
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Expected Graduation</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  value="Spring 2025"
                  readOnly
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900">Academic Background</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Programming Experience</label>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  {programmingSkills.map((skill) => (
                    <SkillLevel
                      key={skill.name}
                      name={skill.name}
                      level={skill.level}
                      icon={Code}
                    />
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Mathematics Background</label>
                <div className="mt-2 grid grid-cols-2 gap-4">
                  {mathSkills.map((skill) => (
                    <SkillLevel
                      key={skill.name}
                      name={skill.name}
                      level={skill.level}
                      icon={Calculator}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900">Learning Preferences</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Preferred Study Hours</label>
                <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm">
                  <option>Morning (6 AM - 12 PM)</option>
                  <option>Afternoon (12 PM - 6 PM)</option>
                  <option>Evening (6 PM - 12 AM)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Maximum Weekly Study Hours</label>
                <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm">
                  <option>20-25 hours</option>
                  <option>25-30 hours</option>
                  <option>30-35 hours</option>
                  <option>35-40 hours</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Preferred Course Load</label>
                <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm">
                  <option>2 courses (8 credits)</option>
                  <option>3 courses (12 credits)</option>
                  <option>4 courses (16 credits)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900">Academic Goals</h2>
            <div className="mt-4 space-y-4">
              {academicGoals.map((goal, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <Target className="h-5 w-5 text-blue-500 mt-0.5" />
                  <span className="text-sm text-gray-600">{goal}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <h2 className="text-lg font-semibold text-gray-900">Completed Courses</h2>
            <div className="mt-4 space-y-3">
              {completedCourses.map((course) => (
                <div key={course.code} className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-900">{course.code}</span>
                  <span className={`font-medium ${getGradeColor(course.grade)}`}>
                    {course.grade}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function SkillLevel({
  name,
  level,
  icon: Icon,
}: {
  name: string;
  level: number;
  icon: LucideIcon;
}) {
  return (
    <div className="flex items-center space-x-3">
      <Icon className="h-5 w-5 text-gray-400" />
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-900">{name}</span>
          <span className="text-sm text-gray-600">{level}/5</span>
        </div>
        <div className="mt-1 h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600"
            style={{ width: `${(level / 5) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

const programmingSkills = [
  { name: "Python", level: 4 },
  { name: "Java", level: 3 },
  { name: "JavaScript", level: 4 },
  { name: "C++", level: 2 },
];

const mathSkills = [
  { name: "Linear Algebra", level: 4 },
  { name: "Statistics", level: 3 },
  { name: "Calculus", level: 4 },
  { name: "Discrete Math", level: 3 },
];

const academicGoals = [
  "Specialize in Artificial Intelligence and Machine Learning",
  "Maintain a GPA of 3.5 or higher",
  "Complete an industry-focused capstone project",
  "Participate in research opportunities",
  "Develop practical software engineering skills",
];

const completedCourses = [
  { code: "CS5001", grade: "A" },
  { code: "CS5002", grade: "A-" },
  { code: "CS5004", grade: "B+" },
  { code: "CS5008", grade: "A" },
];

function getGradeColor(grade: string): string {
  const colors = {
    "A": "text-green-600",
    "A-": "text-green-600",
    "B+": "text-blue-600",
    "B": "text-blue-600",
    "B-": "text-yellow-600",
    "C+": "text-yellow-600",
    "C": "text-red-600",
  };
  return colors[grade as keyof typeof colors] || "text-gray-600";
}