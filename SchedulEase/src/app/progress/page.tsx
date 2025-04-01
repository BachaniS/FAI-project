import { CheckCircle, Clock, GraduationCap, Star } from "lucide-react";

export default function AcademicProgressPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Academic Progress</h1>
        <p className="mt-2 text-gray-600">
          Track your degree completion and academic achievements
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <ProgressCard
          title="Credits Completed"
          value="24/32"
          description="Required credits"
          icon={Clock}
        />
        <ProgressCard
          title="Core Courses"
          value="4/6"
          description="Required courses"
          icon={Star}
        />
        <ProgressCard
          title="Current GPA"
          value="3.8"
          description="Cumulative GPA"
          icon={GraduationCap}
        />
        <ProgressCard
          title="Requirements Met"
          value="75%"
          description="Degree progress"
          icon={CheckCircle}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold text-gray-900">Degree Requirements</h2>
          <div className="mt-4 space-y-4">
            {degreeRequirements.map((req) => (
              <RequirementItem key={req.name} {...req} />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold text-gray-900">Course History</h2>
          <div className="mt-4 space-y-4">
            {courseHistory.map((semester) => (
              <div key={semester.term}>
                <h3 className="font-medium text-gray-900 mb-2">{semester.term}</h3>
                <div className="space-y-2">
                  {semester.courses.map((course) => (
                    <div
                      key={course.code}
                      className="flex justify-between items-center text-sm"
                    >
                      <span className="text-gray-900">{course.code} - {course.name}</span>
                      <span className={getGradeColor(course.grade)}>{course.grade}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ProgressCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: React.ElementType;
}) {
  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center">
        <Icon className="h-5 w-5 text-gray-400" />
        <h2 className="ml-2 text-sm font-medium text-gray-600">{title}</h2>
      </div>
      <div className="mt-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
    </div>
  );
}

function RequirementItem({
  name,
  completed,
  total,
  description,
}: {
  name: string;
  completed: number;
  total: number;
  description: string;
}) {
  const percentage = (completed / total) * 100;
  return (
    <div className="space-y-2">
      <div className="flex justify-between">
        <span className="text-sm font-medium text-gray-900">{name}</span>
        <span className="text-sm text-gray-600">{completed}/{total}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-600"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-600">{description}</p>
    </div>
  );
}

const degreeRequirements = [
  {
    name: "Core Courses",
    completed: 4,
    total: 6,
    description: "Required foundational courses in computer science",
  },
  {
    name: "AI/ML Specialization",
    completed: 2,
    total: 3,
    description: "Specialized courses in artificial intelligence",
  },
  {
    name: "Electives",
    completed: 2,
    total: 3,
    description: "Choose from approved elective courses",
  },
  {
    name: "Capstone/Thesis",
    completed: 0,
    total: 1,
    description: "Final project or thesis requirement",
  },
];

const courseHistory = [
  {
    term: "Spring 2024",
    courses: [
      { code: "CS5200", name: "Database Management", grade: "A" },
      { code: "CS5800", name: "Algorithms", grade: "A-" },
      { code: "CS6140", name: "Machine Learning", grade: "B+" },
    ],
  },
  {
    term: "Fall 2023",
    courses: [
      { code: "CS5001", name: "Programming Fundamentals", grade: "A" },
      { code: "CS5002", name: "Discrete Math", grade: "A-" },
    ],
  },
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