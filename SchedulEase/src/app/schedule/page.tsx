"use client";

import { Calendar, AlertTriangle, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function SchedulePage() {
  return (
    <motion.div 
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="text-2xl font-bold text-gray-900">My Schedule</h1>
        <p className="mt-2 text-gray-600">
          View and manage your course schedule across semesters
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div 
          className="bg-white rounded-lg border p-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Current Semester</h2>
            <span className="text-sm text-gray-600">Spring 2024</span>
          </div>
          <div className="mt-4 space-y-4">
            {currentSemester.courses.map((course, index) => (
              <motion.div
                key={course.code}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1, duration: 0.5 }}
              >
                <CourseCard course={course} />
              </motion.div>
            ))}
            <motion.div 
              className="mt-4 pt-4 border-t"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.5 }}
            >
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Total Credits:</span>
                <span className="font-medium">{currentSemester.totalCredits}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-gray-600">Workload Status:</span>
                <span className="font-medium text-yellow-600">Moderate</span>
              </div>
            </motion.div>
          </div>
        </motion.div>

        <motion.div 
          className="bg-white rounded-lg border p-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Upcoming Semesters</h2>
            <motion.button 
              className="text-sm text-blue-600 hover:text-blue-700"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Edit Plan
            </motion.button>
          </div>
          <div className="mt-4 space-y-6">
            {upcomingSemesters.map((semester, semesterIndex) => (
              <motion.div 
                key={semester.term} 
                className="space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + semesterIndex * 0.2, duration: 0.5 }}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">{semester.term}</h3>
                  <span className="text-sm text-gray-600">{semester.totalCredits} Credits</span>
                </div>
                {semester.courses.map((course, courseIndex) => (
                  <motion.div
                    key={course.code}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + semesterIndex * 0.2 + courseIndex * 0.1, duration: 0.5 }}
                  >
                    <CourseCard course={course} isPlanned />
                  </motion.div>
                ))}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div 
        className="bg-white rounded-lg border p-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.5 }}
      >
        <h2 className="text-lg font-semibold text-gray-900">Schedule Analysis</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {[
            {
              title: "Burnout Risk",
              value: "Medium",
              status: "warning" as const,
              description: "Consider redistributing workload"
            },
            {
              title: "Prerequisites",
              value: "All Met",
              status: "success" as const,
              description: "Current plan is valid"
            },
            {
              title: "Graduation Track",
              value: "On Track",
              status: "success" as const,
              description: "Expected: Spring 2025"
            }
          ].map((analysis, index) => (
            <motion.div
              key={analysis.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
            >
              <AnalysisCard {...analysis} />
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

function CourseCard({ course, isPlanned = false }: { course: Course; isPlanned?: boolean }) {
  return (
    <motion.div 
      className="flex items-start space-x-4 p-4 rounded-lg border bg-gray-50"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div 
        className="flex-shrink-0"
        whileHover={{ rotate: 10 }}
      >
        <Calendar className="h-5 w-5 text-gray-400" />
      </motion.div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-900">{course.code}</p>
          <span className="text-xs text-gray-500">{course.credits} Credits</span>
        </div>
        <p className="text-sm text-gray-600 truncate">{course.name}</p>
        {isPlanned && (
          <p className="text-xs text-gray-500 mt-1">
            Prerequisites: {course.prerequisites || "None"}
          </p>
        )}
      </div>
    </motion.div>
  );
}

function AnalysisCard({
  title,
  value,
  status,
  description,
}: {
  title: string;
  value: string;
  status: "success" | "warning" | "error";
  description: string;
}) {
  const statusColors = {
    success: "text-green-600",
    warning: "text-yellow-600",
    error: "text-red-600",
  };

  const StatusIcon = status === "success" ? CheckCircle : AlertTriangle;

  return (
    <motion.div 
      className="rounded-lg border p-4"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      <motion.div 
        className="mt-2 flex items-center"
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <StatusIcon className={`h-5 w-5 ${statusColors[status]} mr-2`} />
        <span className={`text-lg font-semibold ${statusColors[status]}`}>{value}</span>
      </motion.div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
    </motion.div>
  );
}

interface Course {
  code: string;
  name: string;
  credits: number;
  prerequisites?: string;
}

const currentSemester = {
  term: "Spring 2024",
  totalCredits: 12,
  courses: [
    {
      code: "CS5200",
      name: "Database Management Systems",
      credits: 4,
    },
    {
      code: "CS5800",
      name: "Algorithms",
      credits: 4,
    },
    {
      code: "CS6140",
      name: "Machine Learning",
      credits: 4,
    },
  ],
};

const upcomingSemesters = [
  {
    term: "Fall 2024",
    totalCredits: 8,
    courses: [
      {
        code: "CS6220",
        name: "Data Mining Techniques",
        credits: 4,
        prerequisites: "CS5200, Statistics",
      },
      {
        code: "CS6120",
        name: "Natural Language Processing",
        credits: 4,
        prerequisites: "CS6140",
      },
    ],
  },
  {
    term: "Spring 2025",
    totalCredits: 8,
    courses: [
      {
        code: "CS7180",
        name: "Special Topics in AI",
        credits: 4,
        prerequisites: "CS6140",
      },
      {
        code: "CS7995",
        name: "Thesis",
        credits: 4,
        prerequisites: "None",
      },
    ],
  },
]; 