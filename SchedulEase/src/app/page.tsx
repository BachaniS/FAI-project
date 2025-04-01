import { BookOpen, Calendar, GraduationCap, LineChart } from "lucide-react";
import { LucideIcon } from "lucide-react";

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
      className="rounded-lg border bg-white p-6 hover:border-gray-300 transition-colors"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-50">
        <Icon className="h-6 w-6 text-gray-600" />
      </div>
      <h2 className="mt-4 font-semibold text-gray-900">{title}</h2>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
    </a>
  );
}
