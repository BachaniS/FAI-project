'use client';

import { useEffect, useState } from "react";
import { Activity, Brain, Clock, BookOpen } from "lucide-react";
import { LucideIcon } from "lucide-react";
import { useRouter } from 'next/navigation';

interface BurnoutAnalysis {
  overall_burnout_risk: {
    level: "High" | "Medium" | "Low";
    description: string;
  };
  weekly_study_hours: {
    total: number;
    trend: "increasing" | "stable";
  };
  course_difficulty: {
    level: "High" | "Moderate";
    description: string;
  };
  stress_factors: {
    assignment_deadlines: "High" | "Medium" | "Low";
    course_complexity: "High" | "Medium" | "Low";
    weekly_workload: "High" | "Medium" | "Low";
    prerequisite_match: "High" | "Medium" | "Low";
  };
}

export default function BurnoutAnalysisPage() {
  const router = useRouter();
  const [burnoutData, setBurnoutData] = useState<BurnoutAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchBurnoutData = async () => {
      try {
        const userData = localStorage.getItem('userData');
        if (!userData) {
          router.push('/login');
          return;
        }

        const { nuid } = JSON.parse(userData);
        const response = await fetch(`http://localhost:8000/burnout-analysis/${nuid}`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.message || 'Failed to fetch burnout data');
        }

        setBurnoutData(data);
      } catch (err) {
        console.error('Error fetching burnout data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load burnout data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchBurnoutData();
  }, [router]);

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>;
  }

  if (error) {
    return <div className="text-red-600 text-center p-4">{error}</div>;
  }

  if (!burnoutData) {
    return <div className="text-center p-4">No burnout analysis data available</div>;
  }

  return (
    <div className="space-y-8 p-4 sm:p-6 max-w-7xl mx-auto">
      <div className="text-center sm:text-left">
        <h1 className="text-3xl font-bold text-gray-900 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Burnout Analysis
        </h1>
        <p className="mt-2 text-gray-600">
          Monitor your academic stress levels and workload distribution
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Overall Burnout Risk"
          value={burnoutData.overall_burnout_risk.level}
          trend="stable"
          icon={Activity}
          description={burnoutData.overall_burnout_risk.description}
        />
        <MetricCard
          title="Weekly Study Hours"
          value={burnoutData.weekly_study_hours.total.toString()}
          trend={burnoutData.weekly_study_hours.trend}
          icon={Clock}
          description="Average across courses"
        />
        <MetricCard
          title="Course Difficulty"
          value={burnoutData.course_difficulty.level}
          trend="stable"
          icon={Brain}
          description={burnoutData.course_difficulty.description}
        />
        <MetricCard
          title="Assignment Load"
          value={burnoutData.stress_factors.assignment_deadlines}
          trend="stable"
          icon={BookOpen}
          description="Based on current workload"
        />
      </div>

      <div className="bg-white rounded-xl border shadow-sm hover:shadow-md transition-shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Stress Factors</h2>
        <div className="space-y-2">
          <StressIndicator
            name="Assignment Deadlines"
            value={getStressValue(burnoutData.stress_factors.assignment_deadlines)}
            impact={burnoutData.stress_factors.assignment_deadlines}
          />
          <StressIndicator
            name="Course Complexity"
            value={getStressValue(burnoutData.stress_factors.course_complexity)}
            impact={burnoutData.stress_factors.course_complexity}
          />
          <StressIndicator
            name="Weekly Workload"
            value={getStressValue(burnoutData.stress_factors.weekly_workload)}
            impact={burnoutData.stress_factors.weekly_workload}
          />
          <StressIndicator
            name="Prerequisite Match"
            value={getStressValue(burnoutData.stress_factors.prerequisite_match)}
            impact={burnoutData.stress_factors.prerequisite_match}
          />
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
  const getBgColor = (value: string) => {
    if (value === "High") return "bg-gradient-to-br from-red-50 to-red-100 border-red-200";
    if (value === "Medium") return "bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200";
    if (value === "Low") return "bg-gradient-to-br from-green-50 to-green-100 border-green-200";
    if (value === "Moderate") return "bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200";
    return "bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200";
  };

  const getIconColor = (value: string) => {
    if (value === "High") return "text-red-500";
    if (value === "Medium") return "text-yellow-500";
    if (value === "Low") return "text-green-500";
    if (value === "Moderate") return "text-blue-500";
    return "text-gray-500";
  };

  return (
    <div className={`rounded-xl border p-6 transition-all duration-300 hover:shadow-lg ${getBgColor(value)}`}>
      <div className="flex items-center">
        <Icon className={`h-6 w-6 ${getIconColor(value)}`} />
        <h2 className="ml-2 text-sm font-medium text-gray-800">{title}</h2>
      </div>
      <div className="mt-3">
        <span className={`text-3xl font-bold ${getIconColor(value)}`}>{value}</span>
        <span className={`ml-2 text-sm animate-pulse ${getIconColor(value)}`}>
          {trend === "stable" ? "●" : trend === "increasing" ? "↑" : "↓"}
        </span>
      </div>
      <p className="mt-2 text-sm text-gray-600">{description}</p>
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
    Low: "text-green-600 bg-green-50",
    Medium: "text-yellow-600 bg-yellow-50",
    High: "text-red-600 bg-red-50"
  };

  const barColors = {
    Low: "bg-gradient-to-r from-green-400 to-green-500",
    Medium: "bg-gradient-to-r from-yellow-400 to-yellow-500",
    High: "bg-gradient-to-r from-red-400 to-red-500"
  };

  return (
    <div className="p-3 rounded-lg hover:bg-gray-50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="min-w-[180px] flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{name}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${impactColors[impact]}`}>
            {impact}
          </span>
        </div>
        <div className="flex-1">
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden shadow-inner">
            <div
              className={`h-full ${barColors[impact]} transition-all duration-500`}
              style={{ width: `${value}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper function to convert stress levels to numerical values for the progress bars
function getStressValue(level: "High" | "Medium" | "Low"): number {
  switch (level) {
    case "High": return 80;
    case "Medium": return 50;
    case "Low": return 20;
    default: return 0;
  }
} 