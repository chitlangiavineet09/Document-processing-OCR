'use client';

import { usePathname, useRouter } from 'next/navigation';
import { FileText, History, Settings, Package } from 'lucide-react';
import { useUserRole } from '@/hooks/useUserRole';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  {
    name: 'Job History',
    href: '/jobs',
    icon: History,
  },
  {
    name: 'Created Draft Bills',
    href: '/drafts',
    icon: FileText,
  },
  {
    name: 'Created Draft E-Way Bills',
    href: '/eway-bills',
    icon: Package,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    adminOnly: true,
  },
];

export function SidebarNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { isAdmin, loading } = useUserRole();

  if (loading) {
    return (
      <aside className="w-64 flex-shrink-0 bg-gray-50 border-r border-gray-200 p-4">
        <nav className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </nav>
      </aside>
    );
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-50 border-r border-gray-200 min-h-screen">
      <nav className="p-4 space-y-2">
        {navItems
          .filter((item) => !item.adminOnly || isAdmin)
          .map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <button
                key={item.name}
                onClick={() => router.push(item.href)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-100 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{item.name}</span>
              </button>
            );
          })}
      </nav>
    </aside>
  );
}

