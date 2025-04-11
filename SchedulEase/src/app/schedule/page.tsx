'use client';

import { useState, useEffect } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";
import { ChevronDown, ChevronUp, Clock, BookOpen, Activity, Trash2 } from "lucide-react";

interface Course {
  subject_id: string;
  subject_name: string;
  burnout_risk: number;
  utility_score: number;
  workload_level: "High" | "Medium" | "Low";
  assignment_count: number;
  exam_count: number;
}

interface Metrics {
  total_courses: number;
  average_burnout: number;
  average_utility: number;
  workload_assessment: string;
}

interface HistoryEntry {
  timestamp: string;
  previous_state: any; // Type this more specifically if needed
}

interface Schedule {
  id: string;
  name: string;
  courses: Course[];
  created_at: string;
  metrics: Metrics;
  history: HistoryEntry[];
}

export default function SchedulePage() {
  const router = useRouter();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedScheduleId, setExpandedScheduleId] = useState<string | null>(null);
  const [deleteConfirmSchedule, setDeleteConfirmSchedule] = useState<Schedule | null>(null);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
      try {
        const userData = localStorage.getItem("userData");
        if (!userData) {
          router.push("/login");
          return;
        }
        const { nuid } = JSON.parse(userData);
      
      const response = await axios.get(`http://localhost:8000/schedules/${nuid}`);
      setSchedules(response.data.data);
      } catch (err) {
      setError("Failed to fetch your schedules");
      console.error("Error fetching schedules:", err);
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

  const toggleSchedule = (scheduleId: string) => {
    setExpandedScheduleId(expandedScheduleId === scheduleId ? null : scheduleId);
  };

  const handleDeleteSchedule = async (schedule: Schedule) => {
    try {
      const userData = localStorage.getItem("userData");
      if (!userData) {
        router.push("/login");
        return;
      }
      const { nuid } = JSON.parse(userData);
      
      await axios.delete(`http://localhost:8000/delete-schedule/${nuid}/${schedule.name}`);
      
      setSchedules(schedules.filter(s => s.id !== schedule.id));
      setDeleteConfirmSchedule(null);
    } catch (err) {
      setError("Failed to delete schedule");
      console.error("Error deleting schedule:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
      <div>
          <h1 className="text-2xl font-bold text-gray-900">My Course Schedules</h1>
          <p className="mt-2 text-gray-600">View and manage your saved course schedules</p>
        </div>
      </div>

      {schedules.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">No Schedules Yet</h3>
          <p className="mt-2 text-gray-600">
            Start by creating a new schedule from the recommendations page
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSchedule(schedule.id)}
                className="w-full px-6 py-4 bg-white hover:bg-gray-50 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-4">
                  <h2 className="text-lg font-semibold text-gray-900">{schedule.name}</h2>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    {new Date(schedule.created_at).toLocaleDateString()}
                  </div>
                </div>
                {expandedScheduleId === schedule.id ? (
                  <ChevronUp className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                )}
              </button>

              {expandedScheduleId === schedule.id && (
                <div className="border-t px-6 py-4 bg-gray-50">
                  {/* Schedule Metrics */}
                  <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-white rounded-lg">
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Courses</p>
                      <p className="text-xl font-semibold text-gray-900">
                        {schedule.metrics.total_courses}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Avg. Burnout Risk</p>
                      <p className={`text-xl font-semibold ${
                        schedule.metrics.average_burnout > 0.7 ? 'text-red-600' : 
                        schedule.metrics.average_burnout > 0.4 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {Math.round(schedule.metrics.average_burnout * 100)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Avg. Utility</p>
                      <p className="text-xl font-semibold text-blue-600">
                        {Math.round(schedule.metrics.average_utility)}%
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-600">Workload</p>
                      <p className={`text-xl font-semibold ${
                        schedule.metrics.workload_assessment === "High" ? 'text-red-600' :
                        schedule.metrics.workload_assessment === "Medium" ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {schedule.metrics.workload_assessment}
                      </p>
                    </div>
                  </div>

                  {/* Course List */}
                  <div className="space-y-6">
                    {Object.entries(groupCoursesBySemester(schedule.courses)).map(([semester, courses]) => (
                      <div key={semester}>
                        <h3 className="text-lg font-medium text-gray-900 mb-4">{semester}</h3>
                        <div className="grid gap-4 md:grid-cols-2">
                          {courses.map((course) => (
                            <div 
                              key={course.subject_id}
                              className="p-4 bg-white rounded-lg border"
                            >
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <p className="text-sm font-medium text-blue-600">{course.subject_id}</p>
                                  <h4 className="text-gray-900 font-medium">{course.subject_name}</h4>
                                </div>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  course.workload_level === "High" 
                                    ? "bg-red-100 text-red-800" 
                                    : course.workload_level === "Medium"
                                    ? "bg-yellow-100 text-yellow-800"
                                    : "bg-green-100 text-green-800"
                                }`}>
                                  {course.workload_level} Workload
                                </span>
          </div>
                              
                              <div className="mt-3 space-y-2">
                                <div className="flex items-center gap-4 text-sm text-gray-600">
                                  <div className="flex items-center gap-1">
                                    <BookOpen className="h-4 w-4" />
                                    <span>{course.assignment_count} Assignments</span>
              </div>
                                  <div className="flex items-center gap-1">
                                    <Activity className="h-4 w-4" />
                                    <span>{course.exam_count} Exams</span>
              </div>
            </div>
          </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
        </div>

                  <div className="mt-6 flex justify-end gap-2">
                    <button
                      onClick={() => setDeleteConfirmSchedule(schedule)}
                      className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  </div>
                </div>
              )}
              </div>
            ))}
          </div>
      )}

      {deleteConfirmSchedule && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Delete Schedule
            </h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete "{deleteConfirmSchedule.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-4">
              <button
                onClick={() => setDeleteConfirmSchedule(null)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteSchedule(deleteConfirmSchedule)}
                className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors"
              >
                Delete Schedule
              </button>
      </div>
    </div>
      </div>
      )}
    </div>
  );
} 