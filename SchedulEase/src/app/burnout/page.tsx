import { Activity, Brain, Clock, BookOpen } from "lucide-react";
import { LucideIcon } from "lucide-react";

export default function BurnoutAnalysisPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Burnout Analysis</h1>
        <p className="mt-2 text-gray-600">
          Monitor your academic stress levels and workload distribution
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Overall Burnout Risk"
          value="Medium"
          trend="stable"
          icon={Activity}
          description="Based on current schedule"
        />
        <MetricCard
          title="Weekly Study Hours"
          value="28"
          trend="increasing"
          icon={Clock}
          description="Average across courses"
        />
        <MetricCard
          title="Course Difficulty"
          value="Moderate"
          trend="stable"
          icon={Brain}
          description="Relative to your background"
        />
        <MetricCard
          title="Assignment Load"
          value="High"
          trend="decreasing"
          icon={BookOpen}
          description="Next 2 weeks forecast"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold text-gray-900">Workload Distribution</h2>
          <div className="mt-4 space-y-4">
            {courses.map((course) => (
              <WorkloadBar
                key={course.code}
                course={course}
                maxHours={40}
              />
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold text-gray-900">Stress Factors</h2>
          <div className="mt-4 space-y-4">
            {stressFactors.map((factor) => (
              <StressIndicator
                key={factor.name}
                name={factor.name}
                value={factor.value}
                impact={factor.impact}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-lg font-semibold text-gray-900">Recommendations</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className="rounded-lg border p-4 bg-gray-50"
            >
              <h3 className="font-medium text-gray-900">{rec.title}</h3>
              <p className="mt-1 text-sm text-gray-600">{rec.description}</p>
              {rec.action && (
                <button className="mt-3 text-sm text-blue-600 hover:text-blue-700">
                  {rec.action}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
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
        <div
          className={`h-full ${difficultyColors[course.difficulty]}`}
          style={{ width: `${percentage}%` }}
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
          <div
            className="h-full bg-blue-600"
            style={{ width: `${value}%` }}
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