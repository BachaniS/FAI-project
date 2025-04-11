"use client";

import { AlertTriangle, CheckCircle } from "lucide-react";
import { useState } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";

interface Course {
  subject_id: string;
  subject_name: string;
  burnout_risk: number;
  workload_level: "High" | "Medium" | "Low";
  prerequisites: number;
  reasons: string;
}

interface Summary {
  total_courses: number;
  average_burnout: number;
  completed_courses: number;
  remaining_core: number;
}

interface ScheduleResponse {
  data: {
    recommendations: Course[];
    summary: Summary;
  };
}

interface FullDegreeRecommendation {
  recommendations: Course[];
  summary: {
    total_recommended: number;
    average_burnout: number;
    average_utility: number;
    completed_courses: number;
    selected_courses: number;
    remaining_core: number;
    semester_number: number;
  };
}

interface FullDegreeResponse {
  success: boolean;
  message: string;
  data: FullDegreeRecommendation;
}

interface SaveScheduleResponse {
  success: boolean;
  message: string;
}

export default function SchedulePage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<"none" | "semester" | "degree">(
    "none"
  );
  const [degreeError, setDegreeError] = useState<string | null>(null);
  const [selectedCourses, setSelectedCourses] = useState<Course[]>([]);
  const [currentSemesterCourses, setCurrentSemesterCourses] = useState<
    Course[]
  >([]);
  const [degreeSummary, setDegreeSummary] = useState<
    FullDegreeRecommendation["summary"] | null
  >(null);
  const [isNamingSchedule, setIsNamingSchedule] = useState(false);
  const [scheduleName, setScheduleName] = useState("");

  const fetchNextSemester = async () => {
    setLoading(true);
    setActiveView("semester");
    setError(null);
    setDegreeError(null);
    try {
      const userData = localStorage.getItem("userData");
      if (!userData) {
        router.push("/login");
        return;
      }

      const { nuid } = JSON.parse(userData);
      const response = await axios.get<ScheduleResponse>(
        `http://localhost:8000/recommendations/${nuid}`
      );

      setCourses(response.data.data.recommendations);
      setSummary(response.data.data.summary);
    } catch (err) {
      setError("Failed to fetch schedule data");
      console.error("Error fetching schedule:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFullDegree = async () => {
    setLoading(true);
    setActiveView("degree");
    setError(null);
    setDegreeError(null);
    try {
      const userData = localStorage.getItem("userData");
      if (!userData) {
        router.push("/login");
        return;
      }
      const { nuid } = JSON.parse(userData);

      const response = await axios.post<FullDegreeResponse>(
        `http://localhost:8000/recommend-full/${nuid}`,
        {
          selected_courses: [],
          blacklisted_courses: [],
        }
      );

      setCurrentSemesterCourses(response.data.data.recommendations.slice(0, 2));
      setDegreeSummary(response.data.data.summary);
    } catch (err) {
      setDegreeError("Failed to fetch degree plan");
      console.error("Error fetching degree plan:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCourseSelection = async (accepted: boolean) => {
    try {
      // Check if we've already selected 8 courses
      if (selectedCourses.length >= 8) {
        return;
      }

      setLoading(true);
      const userData = localStorage.getItem("userData");
      if (!userData) {
        router.push("/login");
        return;
      }
      const { nuid } = JSON.parse(userData);

      // Create updated selected courses list based on acceptance
      const updatedSelectedCourses = accepted
        ? [...selectedCourses, ...currentSemesterCourses]
        : selectedCourses;

      // Send the updated list to backend
      const response = await axios.post<FullDegreeResponse>(
        `http://localhost:8000/recommend-full/${nuid}`,
        {
          selected_courses: updatedSelectedCourses.map(
            (course) => course.subject_id
          ),
          blacklisted_courses: accepted
            ? []
            : currentSemesterCourses.map((course) => course.subject_id),
        }
      );

      // Update state with new data
      if (accepted) {
        setSelectedCourses(updatedSelectedCourses);
      }

      // Only update current semester courses if we haven't reached the limit
      if (updatedSelectedCourses.length < 8) {
        setCurrentSemesterCourses(
          response.data.data.recommendations.slice(0, 2)
        );
        setDegreeSummary(response.data.data.summary);
      }
    } catch (err) {
      setDegreeError("Failed to fetch next semester recommendations");
      console.error("Error fetching next recommendations:", err);
    } finally {
      setLoading(false);
    }
  };

  const groupCoursesBySemester = (courses: Course[]) => {
    const semesters: { [key: string]: Course[] } = {};
    courses.forEach((course, index) => {
      const semesterNumber = Math.floor(index / 2) + 1;
      if (!semesters[`Semester ${semesterNumber}`]) {
        semesters[`Semester ${semesterNumber}`] = [];
      }
      semesters[`Semester ${semesterNumber}`].push(course);
    });
    return semesters;
  };

  const saveScheduleToProfile = async () => {
    if (!scheduleName.trim()) {
      alert("Please enter a name for your schedule");
      return;
    }

    try {
      setLoading(true);
      const userData = localStorage.getItem("userData");
      if (!userData) {
        router.push("/login");
        return;
      }
      const { nuid } = JSON.parse(userData);

      const response = await axios.post<SaveScheduleResponse>(
        `http://localhost:8000/save-schedule/${nuid}`,
        {
          name: scheduleName.trim(),
          courses: selectedCourses.map((course) => course.subject_id),
        }
      );

      if (response.data.success) {
        alert("Schedule successfully saved to your profile!");
        setIsNamingSchedule(false);
        setScheduleName("");
      }
    } catch (err) {
      console.error("Error saving schedule:", err);
      alert("Failed to save schedule to profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            Course Schedule Planning
          </h1>
          {selectedCourses.length >= 8 && (
            <button
              onClick={() => setIsNamingSchedule(true)}
              className="px-4 py-2 rounded-lg font-medium bg-green-600 text-white hover:bg-green-700 transition-colors duration-200 flex items-center gap-2"
            >
              <CheckCircle className="h-5 w-5" />
              Export to Profile
            </button>
          )}
        </div>
        <p className="mt-2 text-gray-600">
          Generate optimized course recommendations based on your profile
        </p>
      </div>

      {/* Move completion message here, right after the header */}
      {selectedCourses.length >= 8 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mb-4">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-green-800 mb-2">
            Course Selection Complete!
          </h3>
          <p className="text-green-600">
            You have successfully planned your courses for all four semesters.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={fetchNextSemester}
          className={`px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
            activeView === "semester"
              ? "bg-blue-600 text-white"
              : "bg-white text-blue-600 border border-blue-600 hover:bg-blue-50"
          }`}
        >
          Generate Next Semester Courses
        </button>
        <button
          onClick={fetchFullDegree}
          className={`px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
            activeView === "degree"
              ? "bg-blue-600 text-white"
              : "bg-white text-blue-600 border border-blue-600 hover:bg-blue-50"
          }`}
        >
          Plan Full Degree (2 Years)
        </button>
      </div>

      {loading && (
        <div className="flex justify-center items-center h-48">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {activeView === "degree" && degreeError && (
        <div className="text-blue-600 text-center p-4 bg-blue-50 rounded-lg">
          {degreeError}
        </div>
      )}

      {activeView === "semester" && error && (
        <div className="text-red-600 text-center p-4 bg-red-50 rounded-lg">
          {error}
        </div>
      )}

      {activeView === "degree" && !loading && !degreeError && (
        <>
          {/* Only show recommendations if we haven't selected all 8 courses */}
          {selectedCourses.length < 8 && (
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  Semester {Math.floor(selectedCourses.length / 2) + 1}{" "}
                  Recommendations
                </h2>
                <span className="text-sm text-gray-600">
                  {selectedCourses.length} of 8 courses selected
                </span>
              </div>

              <div className="grid gap-4">
                {currentSemesterCourses.map((course) => (
                  <div
                    key={course.subject_id}
                    className="bg-gray-50 rounded-xl border hover:border-blue-500 transition-all duration-300 overflow-hidden"
                  >
                    <div className="p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-blue-600 mb-1">
                            {course.subject_id}
                          </p>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {course.subject_name}
                          </h3>
                        </div>
                        <div
                          className={`px-3 py-1 rounded-full text-sm font-medium ${
                            course.workload_level === "High"
                              ? "bg-red-100 text-red-800"
                              : course.workload_level === "Medium"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {course.workload_level} Workload
                        </div>
                      </div>

                      <div className="mt-4 space-y-3">
                        <div className="flex items-center gap-4">
                          <div className="flex-1">
                            <p className="text-sm text-gray-600 mb-1">
                              Burnout Risk
                            </p>
                            <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${
                                  course.burnout_risk > 0.7
                                    ? "bg-red-500"
                                    : course.burnout_risk > 0.4
                                    ? "bg-yellow-500"
                                    : "bg-green-500"
                                }`}
                                style={{
                                  width: `${course.burnout_risk * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                          <span className="text-sm font-medium">
                            {Math.round(course.burnout_risk * 100)}%
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">
                            Prerequisites needed:
                          </span>
                          <span
                            className={`text-sm font-medium ${
                              course.prerequisites > 0
                                ? "text-red-600"
                                : "text-green-600"
                            }`}
                          >
                            {course.prerequisites > 0
                              ? `${course.prerequisites} unmet`
                              : "All met"}
                          </span>
                        </div>

                        <p className="text-sm text-gray-600 mt-2">
                          {course.reasons}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex gap-4 justify-center">
                <button
                  onClick={() => handleCourseSelection(false)}
                  className="px-6 py-3 rounded-lg font-medium bg-red-50 text-red-600 hover:bg-red-100"
                >
                  Reject Recommendations
                </button>
                <button
                  onClick={() => handleCourseSelection(true)}
                  className="px-6 py-3 rounded-lg font-medium bg-green-50 text-green-600 hover:bg-green-100"
                >
                  Accept Recommendations
                </button>
              </div>
            </div>
          )}

          {/* Show selected courses section with improved UI */}
          {selectedCourses.length > 0 && (
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                {selectedCourses.length >= 8
                  ? "Your Complete Course Plan"
                  : "Selected Courses"}
              </h2>
              <div className="space-y-8">
                {Object.entries(groupCoursesBySemester(selectedCourses)).map(
                  ([semester, courses]) => (
                    <div key={semester} className="relative">
                      <div className="flex items-center mb-4">
                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                          <span className="text-blue-600 font-semibold">
                            {semester.split(" ")[1]}
                          </span>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-800">
                          {semester}
                        </h3>
                      </div>
                      <div className="grid gap-4 md:grid-cols-2">
                        {courses.map((course, index) => (
                          <div
                            key={index}
                            className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-all duration-300"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <p className="text-sm font-medium text-blue-600">
                                  {course.subject_id}
                                </p>
                                <h4 className="text-gray-900 font-medium">
                                  {course.subject_name}
                                </h4>
                              </div>
                              <div
                                className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  course.workload_level === "High"
                                    ? "bg-red-100 text-red-800"
                                    : course.workload_level === "Medium"
                                    ? "bg-yellow-100 text-yellow-800"
                                    : "bg-green-100 text-green-800"
                                }`}
                              >
                                {course.workload_level}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                              <div className="flex-1">
                                <div className="h-1.5 w-full bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full ${
                                      course.burnout_risk > 0.7
                                        ? "bg-red-500"
                                        : course.burnout_risk > 0.4
                                        ? "bg-yellow-500"
                                        : "bg-green-500"
                                    }`}
                                    style={{
                                      width: `${course.burnout_risk * 100}%`,
                                    }}
                                  />
                                </div>
                              </div>
                              <span className="text-xs font-medium text-gray-600">
                                {Math.round(course.burnout_risk * 100)}% Risk
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                      {/* Add connecting line between semesters */}
                      {semester !==
                        `Semester ${Math.floor(
                          selectedCourses.length / 2
                        )}` && (
                        <div className="absolute left-4 top-12 bottom-0 w-0.5 bg-blue-100"></div>
                      )}
                    </div>
                  )
                )}
              </div>

              {/* Summary stats at the bottom */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Total Credits</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {selectedCourses.length * 4}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Semesters Planned</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {Math.ceil(selectedCourses.length / 2)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600">Average Workload</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {selectedCourses.reduce(
                        (acc, course) =>
                          acc +
                          (course.workload_level === "High"
                            ? 3
                            : course.workload_level === "Medium"
                            ? 2
                            : 1),
                        0
                      ) / selectedCourses.length}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Only show course recommendations when semester view is active and we have data */}
      {activeView === "semester" &&
        !loading &&
        !error &&
        courses.length > 0 && (
          <>
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  Next Semester Courses
                </h2>
                <span className="text-sm text-gray-600">
                  {courses.length * 4} Credits
                </span>
              </div>

              <div className="grid gap-4">
                {courses.map((course) => (
                  <div
                    key={course.subject_id}
                    className="bg-gray-50 rounded-xl border hover:border-blue-500 transition-all duration-300 overflow-hidden"
                  >
                    <div className="p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm font-medium text-blue-600 mb-1">
                            {course.subject_id}
                          </p>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {course.subject_name}
                          </h3>
                        </div>
                        <div
                          className={`px-3 py-1 rounded-full text-sm font-medium ${
                            course.workload_level === "High"
                              ? "bg-red-100 text-red-800"
                              : course.workload_level === "Medium"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {course.workload_level} Workload
                        </div>
                      </div>

                      <div className="mt-4 space-y-3">
                        <div className="flex items-center gap-4">
                          <div className="flex-1">
                            <p className="text-sm text-gray-600 mb-1">
                              Burnout Risk
                            </p>
                            <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${
                                  course.burnout_risk > 0.7
                                    ? "bg-red-500"
                                    : course.burnout_risk > 0.4
                                    ? "bg-yellow-500"
                                    : "bg-green-500"
                                }`}
                                style={{
                                  width: `${course.burnout_risk * 100}%`,
                                }}
                              />
                            </div>
                          </div>
                          <span className="text-sm font-medium">
                            {Math.round(course.burnout_risk * 100)}%
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">
                            Prerequisites needed:
                          </span>
                          <span
                            className={`text-sm font-medium ${
                              course.prerequisites > 0
                                ? "text-red-600"
                                : "text-green-600"
                            }`}
                          >
                            {course.prerequisites > 0
                              ? `${course.prerequisites} unmet`
                              : "All met"}
                          </span>
                        </div>

                        <p className="text-sm text-gray-600 mt-2">
                          {course.reasons}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {summary && (
              <div className="bg-white rounded-lg border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Progress Summary
                </h2>
                <div className="grid gap-4 md:grid-cols-4">
                  <AnalysisCard
                    title="Average Burnout Risk"
                    value={`${Math.round(summary.average_burnout * 100)}%`}
                    status={
                      summary.average_burnout > 0.7
                        ? "error"
                        : summary.average_burnout > 0.4
                        ? "warning"
                        : "success"
                    }
                    description="For recommended courses"
                  />
                  <AnalysisCard
                    title="Completed Courses"
                    value={summary.completed_courses.toString()}
                    status="success"
                    description="Courses finished so far"
                  />
                  <AnalysisCard
                    title="Remaining Core"
                    value={summary.remaining_core.toString()}
                    status={summary.remaining_core > 4 ? "warning" : "success"}
                    description="Core courses left to take"
                  />
                  <AnalysisCard
                    title="Next Semester"
                    value={`${summary.total_courses * 4} Credits`}
                    status="success"
                    description="Recommended course load"
                  />
                </div>
              </div>
            )}
          </>
        )}

      {isNamingSchedule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Name Your Schedule
            </h3>
            <input
              type="text"
              value={scheduleName}
              onChange={(e) => setScheduleName(e.target.value)}
              placeholder="Enter schedule name"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <div className="mt-6 flex gap-4 justify-end">
              <button
                onClick={() => {
                  setIsNamingSchedule(false);
                  setScheduleName("");
                }}
                className="px-4 py-2 rounded-lg font-medium text-gray-600 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={saveScheduleToProfile}
                className="px-4 py-2 rounded-lg font-medium bg-green-600 text-white hover:bg-green-700"
              >
                Save Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
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
    <div className="rounded-lg border p-4">
      <h3 className="text-sm font-medium text-gray-900">{title}</h3>
      <div className="mt-2 flex items-center">
        <StatusIcon className={`h-5 w-5 ${statusColors[status]} mr-2`} />
        <span className={`text-lg font-semibold ${statusColors[status]}`}>
          {value}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
    </div>
  );
}
