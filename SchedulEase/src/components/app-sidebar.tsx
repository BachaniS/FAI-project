'use client';

import Link from "next/link";
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
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Course Catalog", href: "/courses", icon: BookOpen },
  { name: "My Schedule", href: "/schedule", icon: Calendar },
  { name: "Academic Progress", href: "/progress", icon: GraduationCap },
  { name: "Burnout Analysis", href: "/burnout", icon: LineChart },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function AppSidebar() {
  
  // Use simple, non-dynamic classes first to test
  return (
    <div className="w-64 bg-white border-r">
      <div className="flex h-16 items-center px-6 border-b">
        <h1 className="text-xl font-bold">SchedulEase</h1>
      </div>
      <nav className="p-4">
        {navigation.map((item) => (
          <Link
            key={item.name}
            href={item.href}
            className="flex items-center px-4 py-2 my-1 rounded-lg"
          >
            <item.icon className="mr-3 h-5 w-5" />
            <span>{item.name}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
