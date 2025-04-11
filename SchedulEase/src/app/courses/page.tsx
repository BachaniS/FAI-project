"use client";

import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface CourseData {
  subject_id: string;
  subject_name: string;
  description: string;
  is_core: boolean;
  enrollment_demand: "High" | "Medium" | "Low";
  assignment_count: number;
  exam_count: number;
  course_outcomes: string[];
  programming_knowledge_needed: string[];
  math_requirements: string[];
  prerequisite: string[];
}

interface CourseResponse {
  success: boolean;
  message: string;
  data: CourseData[];
}

export default function CourseCatalogPage() {
  const router = useRouter();
  const [courseData, setCourseData] = useState<CourseData[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCourse, setSelectedCourse] = useState<CourseData | null>(null);
  const [searchName, setSearchName] = useState<string>("");
  const [searchId, setSearchId] = useState<string>("");

  // Helper function to get demand badge color
  const getDemandBadgeStyle = (demand: string) => {
    switch (demand.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const userData = localStorage.getItem("userData");
        if (!userData) {
          router.push("/login");
          return;
        }

        const { nuid } = JSON.parse(userData);
        const response = await fetch(
          `http://localhost:8000/course-catalog/${nuid}`
        );
        const responseData: CourseResponse = await response.json();

        if (!response.ok) {
          throw new Error(
            responseData.message || "Failed to fetch course catalog"
          );
        }

        setCourseData(responseData.data);
      } catch (err) {
        console.error("Error fetching course catalog:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load course catalog"
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchCourseData();
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-600 text-center p-4">{error}</div>;
  }

  if (!courseData) {
    return <div className="text-center p-4">No course data available</div>;
  }

  const filteredCourses = courseData.filter(course => {
    const nameMatch = course.subject_name.toLowerCase().includes(searchName.toLowerCase());
    const idMatch = course.subject_id.toLowerCase().includes(searchId.toLowerCase());
    return (searchName === "" || nameMatch) && (searchId === "" || idMatch);
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Course Catalog</h1>
        <p className="mt-2 text-gray-600">
          Browse and search through available courses for your degree program
        </p>
      </div>

      <div className="flex space-x-4">
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search by course name..."
            value={searchName || ""}
            onChange={(e) => setSearchName(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="Search by course ID..."
            value={searchId || ""}
            onChange={(e) => setSearchId(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredCourses.map((course, index) => (
          <div
            key={`${course.subject_id}-${index}`}
            className="bg-white rounded-xl border border-gray-200 hover:border-blue-500 p-6 relative hover:shadow-lg transition-all duration-300 cursor-pointer group"
            onClick={() => setSelectedCourse(course)}
          >
            <div className="flex gap-2 absolute top-4 right-4">
              {course.is_core && (
                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full shadow-sm">
                  Core
                </span>
              )}
              <span
                className={`px-3 py-1 text-xs font-medium rounded-full shadow-sm ${getDemandBadgeStyle(
                  course.enrollment_demand
                )}`}
              >
                {course.enrollment_demand} Demand
              </span>
            </div>
            <div className="flex flex-col mt-2">
              <div className="mb-4">
                <p className="text-sm font-medium text-blue-600 mb-2">
                  {course.subject_id}
                </p>
                <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                  {course.subject_name}
                </h3>
              </div>
              <div className="flex gap-4 mt-auto">
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">
                    {course.assignment_count} Assignments
                  </span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm text-gray-600">
                    {course.exam_count} Exams
                  </span>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {course.programming_knowledge_needed.slice(0, 2).map((lang, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                  >
                    {lang}
                  </span>
                ))}
                {course.programming_knowledge_needed.length > 2 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                    +{course.programming_knowledge_needed.length - 2} more
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for course details */}
      {selectedCourse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl my-8 relative">
            <div className="flex justify-between items-start mb-6">
              <div>
                <p className="text-sm font-medium text-blue-600 mb-2">
                  {selectedCourse.subject_id}
                </p>
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedCourse.subject_name}
                </h2>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCourse(null);
                }}
                className="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Description */}
              <div className="bg-gray-50 p-4 rounded-xl">
                <p className="text-gray-700 leading-relaxed">
                  {selectedCourse.description}
                </p>
              </div>

              {/* Badges Section */}
              <div className="flex flex-wrap gap-2">
                <span className={`px-3 py-1.5 rounded-full text-sm font-medium ${getDemandBadgeStyle(selectedCourse.enrollment_demand)}`}>
                  {selectedCourse.enrollment_demand} Demand
                </span>
                {selectedCourse.is_core && (
                  <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    Core Course
                  </span>
                )}
              </div>

              {/* Course Structure */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-3 rounded-xl">
                  <h4 className="font-medium text-blue-900 text-sm">Assignments</h4>
                  <p className="text-xl font-bold text-blue-700">{selectedCourse.assignment_count}</p>
                </div>
                <div className="bg-purple-50 p-3 rounded-xl">
                  <h4 className="font-medium text-purple-900 text-sm">Exams</h4>
                  <p className="text-xl font-bold text-purple-700">{selectedCourse.exam_count}</p>
                </div>
              </div>

              {/* Course Outcomes */}
              <div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">Course Outcomes</h3>
                <div className="grid grid-cols-2 gap-4">
                  {selectedCourse.course_outcomes.reduce((columns, outcome, index) => {
                    const columnIndex = index % 2;
                    if (!columns[columnIndex]) {
                      columns[columnIndex] = [];
                    }
                    columns[columnIndex].push(
                      <li key={index} className="flex items-start mb-1.5">
                        <span className="text-blue-500 mr-2">•</span>
                        <span className="text-sm text-gray-700">{outcome}</span>
                      </li>
                    );
                    return columns;
                  }, [] as JSX.Element[][]).map((column, i) => (
                    <ul key={i} className="space-y-1">
                      {column}
                    </ul>
                  ))}
                </div>
              </div>

              {/* Prerequisites */}
              <div>
                <h3 className="text-base font-semibold text-gray-900 mb-2">Prerequisites</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedCourse.prerequisite.length > 0 ? (
                    selectedCourse.prerequisite.map((prereq, index) => (
                      <span key={index} className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                        {prereq}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-gray-500">-</span>
                  )}
                </div>
              </div>

              {/* Required Knowledge */}
              <div>
                <h3 className="text-base font-semibold text-gray-900 mb-3">Required Knowledge</h3>
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-1.5">Programming Languages</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCourse.programming_knowledge_needed.length > 0 ? (
                        selectedCourse.programming_knowledge_needed.map((lang, index) => (
                          <span key={index} className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                            {lang}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-600 mb-1.5">Mathematics</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedCourse.math_requirements.length > 0 ? (
                        selectedCourse.math_requirements.map((math, index) => (
                          <span key={index} className="px-2.5 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                            {math}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
