"use client";

import { Search } from "lucide-react";
import { motion } from "framer-motion";

export default function CourseCatalogPage() {
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
        <h1 className="text-2xl font-bold text-gray-900">Course Catalog</h1>
        <p className="mt-2 text-gray-600">
          Browse and search through available courses for your degree program
        </p>
      </motion.div>

      <motion.div 
        className="flex space-x-4"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
      >
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search courses..."
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
        <select className="block w-48 pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md">
          <option>All Categories</option>
          <option>Core Courses</option>
          <option>Electives</option>
          <option>AI/ML</option>
          <option>Systems</option>
          <option>Theory</option>
        </select>
      </motion.div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {courses.map((course, index) => (
          <motion.div 
            key={course.id} 
            className="bg-white rounded-lg border p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + index * 0.1, duration: 0.5 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{course.code}</h3>
                <p className="mt-1 text-gray-900">{course.name}</p>
              </div>
              <motion.span 
                className={`px-2 py-1 text-xs font-medium rounded ${getCategoryColor(course.category)}`}
                whileHover={{ scale: 1.05 }}
              >
                {course.category}
              </motion.span>
            </div>
            <p className="mt-3 text-sm text-gray-600">{course.description}</p>
            <motion.div 
              className="mt-4 border-t pt-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
            >
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Credits</p>
                  <p className="font-medium">{course.credits}</p>
                </div>
                <div>
                  <p className="text-gray-500">Prerequisites</p>
                  <p className="font-medium">{course.prerequisites || "None"}</p>
                </div>
                <div>
                  <p className="text-gray-500">Workload</p>
                  <p className="font-medium">{course.workload}</p>
                </div>
                <div>
                  <p className="text-gray-500">Alignment Score</p>
                  <motion.p 
                    className="font-medium text-blue-600"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
                  >
                    {course.alignmentScore}%
                  </motion.p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

const courses = [
  {
    id: 1,
    code: "CS5200",
    name: "Database Management Systems",
    category: "Core",
    description: "Fundamental concepts of database management systems, emphasizing the relational model, database design, and SQL.",
    credits: 4,
    prerequisites: "None",
    workload: "Medium",
    alignmentScore: 95,
  },
  {
    id: 2,
    code: "CS5800",
    name: "Algorithms",
    category: "Core",
    description: "Design and analysis of algorithms, including sorting, searching, graph algorithms, and computational complexity.",
    credits: 4,
    prerequisites: "DS&A",
    workload: "High",
    alignmentScore: 92,
  },
  {
    id: 3,
    code: "CS6140",
    name: "Machine Learning",
    category: "AI/ML",
    description: "Fundamental concepts and algorithms in machine learning, including supervised and unsupervised learning.",
    credits: 4,
    prerequisites: "Statistics, Linear Algebra",
    workload: "High",
    alignmentScore: 88,
  },
];

function getCategoryColor(category: string): string {
  const colors = {
    Core: "bg-blue-100 text-blue-800",
    "AI/ML": "bg-purple-100 text-purple-800",
    Systems: "bg-green-100 text-green-800",
    Theory: "bg-yellow-100 text-yellow-800",
    Electives: "bg-gray-100 text-gray-800",
  };
  return colors[category as keyof typeof colors] || colors.Electives;
} 