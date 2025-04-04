'use client';

import { Calendar, AlertTriangle, CheckCircle } from "lucide-react";
import { useEffect, useState } from "react";
import axios from "axios";

// Types
interface Course {
  code: string;
  name: string;
  credits: number;
  prerequisites?: string;
}

interface Semester {
  term: string;
  totalCredits: number;
  courses: Course[];
}

interface Schedule {
  nuid: string;
  schedule: {
    semester: number;
    courses: {
      subject_id: string;
      subject_name: string;
      burnout: number;
      fitness_score: number;
    }[];
  }[];
  total_burnout: number;
}

export default function SchedulePage() {
  const [currentSemester, setCurrentSemester] = useState<Semester | null>(null);
  const [upcomingSemesters, setUpcomingSemesters] = useState<Semester[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSchedule = async () => {
      try {
        // Replace with actual student ID
        const studentId = "123";
        // const studentId = "YOUR_STUDENT_ID";
        const response = await axios.get<Schedule>(`http://localhost:8000/schedule/${studentId}`);
        
        // Transform backend data to frontend format
        const schedule = response.data;
        
        // Set current semester
        if (schedule.schedule[0]) {
          setCurrentSemester({
            term: "Spring 2024",
            totalCredits: schedule.schedule[0].courses.length * 4,
            courses: schedule.schedule[0].courses.map(course => ({
              code: course.subject_id,
              name: course.subject_name,
              credits: 4,
            }))
          });
        }

        // Set upcoming semesters
        const upcoming = schedule.schedule.slice(1).map((sem, index) => ({
          term: index === 0 ? "Fall 2024" : "Spring 2025",
          totalCredits: sem.courses.length * 4,
          courses: sem.courses.map(course => ({
            code: course.subject_id,
            name: course.subject_name,
            credits: 4,
            prerequisites: "To be fetched", // You can fetch this separately if needed
          }))
        }));
        setUpcomingSemesters(upcoming);
        
      } catch (err) {
        setError("Failed to fetch schedule");
        console.error("Error fetching schedule:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedule();
  }, []);

  if (loading) {
    return <div>Loading schedule...</div>;
  }

  if (error) {
    return <div className="text-red-600">{error}</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My Schedule</h1>
        <p className="mt-2 text-gray-600">
          View and manage your course schedule across semesters
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Current Semester</h2>
            <span className="text-sm text-gray-600">Spring 2024</span>
          </div>
          <div className="mt-4 space-y-4">
            {currentSemester?.courses.map((course) => (
              <CourseCard key={course.code} course={course} />
            ))}
            <div className="mt-4 pt-4 border-t">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Total Credits:</span>
                <span className="font-medium">{currentSemester?.totalCredits}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-gray-600">Workload Status:</span>
                <span className="font-medium text-yellow-600">Moderate</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Upcoming Semesters</h2>
            <button className="text-sm text-blue-600 hover:text-blue-700">
              Edit Plan
            </button>
          </div>
          <div className="mt-4 space-y-6">
            {upcomingSemesters.map((semester) => (
              <div key={semester.term} className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">{semester.term}</h3>
                  <span className="text-sm text-gray-600">{semester.totalCredits} Credits</span>
                </div>
                {semester.courses.map((course) => (
                  <CourseCard key={course.code} course={course} isPlanned />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold text-gray-900">Schedule Analysis</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <AnalysisCard
            title="Burnout Risk"
            value="Medium"
            status="warning"
            description="Consider redistributing workload"
          />
          <AnalysisCard
            title="Prerequisites"
            value="All Met"
            status="success"
            description="Current plan is valid"
          />
          <AnalysisCard
            title="Graduation Track"
            value="On Track"
            status="success"
            description="Expected: Spring 2025"
          />
        </div>
      </div>
    </div>
  );
}

function CourseCard({ course, isPlanned = false }: { course: Course; isPlanned?: boolean }) {
  return (
    <div className="flex items-start space-x-4 p-4 rounded-lg border bg-gray-50">
      <div className="flex-shrink-0">
        <Calendar className="h-5 w-5 text-gray-400" />
      </div>
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
        <span className={`text-lg font-semibold ${statusColors[status]}`}>{value}</span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
    </div>
  );
} 