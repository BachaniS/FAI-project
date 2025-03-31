import { BookOpen, Calendar, GraduationCap, LineChart } from "lucide-react";
import { LucideIcon } from "lucide-react";

// Add this CSS class to your card components
const cardStyle = "bg-white/80 backdrop-blur-sm rounded-xl border border-purple-100 shadow-lg hover:shadow-xl transition-all duration-300";

// Add this to your section headers
const headerStyle = "text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 text-transparent bg-clip-text";

// Add this to your buttons
const buttonStyle = "px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all shadow-md hover:shadow-lg";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome to SchedulEase</h1>
        <p className="mt-2 text-gray-600">
          Your AI-powered course recommendation system for optimal academic planning
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <DashboardCard
          title="Course Catalog"
          description="Browse available courses and their details"
          icon={BookOpen}
          href="/courses"
        />
        <DashboardCard
          title="My Schedule"
          description="View and manage your course schedule"
          icon={Calendar}
          href="/schedule"
        />
        <DashboardCard
          title="Academic Progress"
          description="Track your degree completion progress"
          icon={GraduationCap}
          href="/progress"
        />
        <DashboardCard
          title="Burnout Analysis"
          description="Monitor and manage your academic stress"
          icon={LineChart}
          href="/burnout"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900">Recommended Courses</h2>
          <p className="mt-1 text-sm text-gray-600">Based on your interests and academic goals</p>
          <div className="mt-4 space-y-3">
            {/* Placeholder for recommended courses */}
            <div className="rounded border p-3">
              <h3 className="font-medium">CS5200 - Database Management Systems</h3>
              <p className="text-sm text-gray-600">Alignment Score: 95%</p>
            </div>
            <div className="rounded border p-3">
              <h3 className="font-medium">CS5800 - Algorithms</h3>
              <p className="text-sm text-gray-600">Alignment Score: 92%</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900">Current Semester Overview</h2>
          <p className="mt-1 text-sm text-gray-600">Spring 2024</p>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between rounded border p-3">
              <div>
                <h3 className="font-medium">Current Workload</h3>
                <p className="text-sm text-gray-600">12 Credit Hours</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-green-600 font-medium">Low</span>
              </div>
            </div>
            <div className="flex items-center justify-between rounded border p-3">
              <div>
                <h3 className="font-medium">Burnout Risk</h3>
                <p className="text-sm text-gray-600">Based on current schedule</p>
              </div>
              <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
                <span className="text-yellow-600 font-medium">Med</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DashboardCard({
  title,
  description,
  icon: Icon,
  href,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
}) {
  return (
    <a
      href={href}
      className={`${cardStyle} p-6`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="mt-1 text-sm text-gray-600">{description}</p>
        </div>
        <div className="h-12 w-12 rounded-full bg-purple-100 flex items-center justify-center">
          <Icon className="h-6 w-6 text-purple-600" />
        </div>
      </div>
    </a>
  );
}

// Progress bar component
function ProgressBar({ value, max, color = "purple" }) {
  const percentage = (value / max) * 100;
  return (
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        className={`h-full bg-gradient-to-r from-${color}-500 to-${color}-600 transition-all duration-300`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

// Status badge component
function StatusBadge({ status }) {
  const colors = {
    success: "bg-green-100 text-green-800 border-green-200",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
    error: "bg-red-100 text-red-800 border-red-200",
  };

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${colors[status]}`}>
      {status}
    </span>
  );
}
