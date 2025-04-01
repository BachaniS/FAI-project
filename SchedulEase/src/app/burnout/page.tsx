"use client";

import { Activity, Brain, Clock, BookOpen } from "lucide-react";
import { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

export default function BurnoutAnalysisPage() {
  return (
    <motion.div 
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="text-2xl font-bold text-gray-900">Burnout Analysis</h1>
        <p className="mt-2 text-gray-600">
          Monitor your academic stress levels and workload distribution
        </p>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Stagger the metric cards animation */}
        {[
          {
            title: "Overall Burnout Risk",
            value: "Medium",
            trend: "stable" as const,
            icon: Activity,
            description: "Based on current schedule"
          },
          {
            title: "Weekly Study Hours",
            value: "28",
            trend: "increasing" as const,
            icon: Clock,
            description: "Average across courses"
          },
          {
            title: "Course Difficulty",
            value: "Moderate",
            trend: "stable" as const,
            icon: Brain,
            description: "Relative to your background"
          },
          {
            title: "Assignment Load",
            value: "High",
            trend: "decreasing" as const,
            icon: BookOpen,
            description: "Next 2 weeks forecast"
          }
        ].map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.5 }}
          >
            <MetricCard {...metric} />
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <motion.div
          className="bg-white rounded-lg border p-6"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <h2 className="text-lg font-semibold text-gray-900">Workload Distribution</h2>
          <div className="mt-4 space-y-4">
            {courses.map((course, index) => (
              <motion.div
                key={course.code}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
              >
                <WorkloadBar course={course} maxHours={40} />
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div
          className="bg-white rounded-lg border p-6"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <h2 className="text-lg font-semibold text-gray-900">Stress Factors</h2>
          <div className="mt-4 space-y-4">
            {stressFactors.map((factor, index) => (
              <motion.div
                key={factor.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
              >
                <StressIndicator {...factor} />
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
        <h2 className="text-lg font-semibold text-gray-900">Recommendations</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {recommendations.map((rec, index) => (
            <motion.div
              key={index}
              className="rounded-lg border p-4 bg-gray-50"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <h3 className="font-medium text-gray-900">{rec.title}</h3>
              <p className="mt-1 text-sm text-gray-600">{rec.description}</p>
              {rec.action && (
                <motion.button 
                  className="mt-3 text-sm text-blue-600 hover:text-blue-700"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {rec.action}
                </motion.button>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

function MetricCard({
  title,
  value,
  trend,
  icon: Icon,
  description,
}: {
  title: string;
  value: string;
  trend: "increasing" | "decreasing" | "stable";
  icon: LucideIcon;
  description: string;
}) {
  const trendColors = {
    increasing: "text-red-600",
    decreasing: "text-green-600",
    stable: "text-blue-600",
  };

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center">
        <Icon className="h-5 w-5 text-gray-400" />
        <h2 className="ml-2 text-sm font-medium text-gray-600">{title}</h2>
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        <span className={`ml-2 text-sm ${trendColors[trend]}`}>
          {trend === "stable" ? "●" : trend === "increasing" ? "↑" : "↓"}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
    </div>
  );
}

function WorkloadBar({
  course,
  maxHours,
}: {
  course: {
    code: string;
    name: string;
    weeklyHours: number;
    difficulty: "Low" | "Medium" | "High";
  };
  maxHours: number;
}) {
  const percentage = (course.weeklyHours / maxHours) * 100;
  const difficultyColors = {
    Low: "bg-green-200",
    Medium: "bg-yellow-200",
    High: "bg-red-200",
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium text-gray-900">{course.code}</span>
        <span className="text-gray-600">{course.weeklyHours}h/week</span>
      </div>
      <div className="h-4 bg-gray-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${difficultyColors[course.difficulty]}`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

function StressIndicator({
  name,
  value,
  impact,
}: {
  name: string;
  value: number;
  impact: "Low" | "Medium" | "High";
}) {
  const impactColors = {
    Low: "text-green-600",
    Medium: "text-yellow-600",
    High: "text-red-600",
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm font-medium text-gray-900">{name}</span>
      <div className="flex items-center space-x-4">
        <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-blue-600"
            initial={{ width: 0 }}
            animate={{ width: `${value}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
        <span className={`text-sm font-medium ${impactColors[impact]}`}>
          {impact}
        </span>
      </div>
    </div>
  );
}

const courses = [
  {
    code: "CS5200",
    name: "Database Management Systems",
    weeklyHours: 12,
    difficulty: "Medium" as const,
  },
  {
    code: "CS5800",
    name: "Algorithms",
    weeklyHours: 15,
    difficulty: "High" as const,
  },
  {
    code: "CS6140",
    name: "Machine Learning",
    weeklyHours: 14,
    difficulty: "High" as const,
  },
];

const stressFactors = [
  { name: "Assignment Deadlines", value: 75, impact: "High" as const },
  { name: "Course Complexity", value: 60, impact: "Medium" as const },
  { name: "Weekly Workload", value: 80, impact: "High" as const },
  { name: "Prerequisite Match", value: 40, impact: "Low" as const },
];

const recommendations = [
  {
    title: "Redistribute Workload",
    description: "Consider moving CS6140 to next semester to balance the workload.",
    action: "View Alternative Schedules",
  },
  {
    title: "Study Group Formation",
    description: "Join or form study groups for CS5800 to share knowledge and reduce stress.",
    action: "Find Study Groups",
  },
  {
    title: "Time Management",
    description: "Block specific study hours for CS5200 assignments to stay on track.",
  },
  {
    title: "Additional Resources",
    description: "Access supplementary materials for ML prerequisites to reduce complexity.",
    action: "Browse Resources",
  },
]; 