import { Search } from "lucide-react";

export default function CourseCatalogPage() {
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
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {courses.map((course) => (
          <div key={course.id} className="bg-white rounded-lg border p-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{course.code}</h3>
                <p className="mt-1 text-gray-900">{course.name}</p>
              </div>
              <span className={`px-2 py-1 text-xs font-medium rounded ${getCategoryColor(course.category)}`}>
                {course.category}
              </span>
            </div>
            <p className="mt-3 text-sm text-gray-600">{course.description}</p>
            <div className="mt-4 border-t pt-4">
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
                  <p className="font-medium text-blue-600">{course.alignmentScore}%</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
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