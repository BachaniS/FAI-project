'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Calendar,
  GraduationCap,
  Home,
  LineChart,
  Settings,
  User,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Course Catalog", href: "/courses", icon: BookOpen },
  { name: "My Schedule", href: "/schedule", icon: Calendar },
  { name: "Academic Progress", href: "/progress", icon: GraduationCap },
  { name: "Burnout Analysis", href: "/burnout", icon: LineChart },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-white border-r">
      <div className="flex h-16 items-center px-6 border-b">
        <h1 className="text-xl font-bold text-gray-900">SchedulEase</h1>
      </div>
      <nav className="flex-1 space-y-1 px-2 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`
                group flex items-center px-4 py-2 text-sm font-medium rounded-md
                ${
                  isActive
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }
              `}
            >
              <Icon
                className={`mr-3 h-5 w-5 flex-shrink-0 ${
                  isActive ? "text-gray-900" : "text-gray-400 group-hover:text-gray-500"
                }`}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-gray-200" />
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">Student Name</p>
            <p className="text-xs text-gray-500">NUID: 12345</p>
          </div>
        </div>
      </div>
    </div>
  );
}
