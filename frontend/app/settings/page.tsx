'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';
import { useUserRole } from '@/hooks/useUserRole';
import { Users, Globe, Brain, List, Loader2, AlertCircle } from 'lucide-react';

const tabs = [
  { id: 'users', label: 'User Management', icon: Users },
  { id: 'api', label: 'External API Configuration', icon: Globe },
  { id: 'llm', label: 'LLM Prompt & Model Config', icon: Brain },
  { id: 'jobs', label: 'Global Job List', icon: List },
];

export default function SettingsPage() {
  const router = useRouter();
  const { isAdmin, loading: roleLoading } = useUserRole();
  const [activeTab, setActiveTab] = useState('users');
  const [componentLoading, setComponentLoading] = useState(true);
  const [TabComponent, setTabComponent] = useState<React.ComponentType | null>(null);

  // Check admin access
  useEffect(() => {
    if (!roleLoading && !isAdmin) {
      router.push('/?error=forbidden');
    }
  }, [isAdmin, roleLoading, router]);

  // Lazy load tab components
  useEffect(() => {
    if (!isAdmin) return;

    setComponentLoading(true);
    const loadComponent = async () => {
      try {
        switch (activeTab) {
          case 'users':
            const { default: UserManagement } = await import('./tabs/UserManagement');
            setTabComponent(() => UserManagement);
            break;
          case 'api':
            const { default: APIConfig } = await import('./tabs/APIConfig');
            setTabComponent(() => APIConfig);
            break;
          case 'llm':
            const { default: LLMConfig } = await import('./tabs/LLMConfig');
            setTabComponent(() => LLMConfig);
            break;
          case 'jobs':
            const { default: GlobalJobs } = await import('./tabs/GlobalJobs');
            setTabComponent(() => GlobalJobs);
            break;
          default:
            setTabComponent(null);
        }
      } catch (error) {
        console.error('Error loading tab component:', error);
      } finally {
        setComponentLoading(false);
      }
    };

    loadComponent();
  }, [activeTab, isAdmin]);

  if (roleLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <SidebarNav />
          <main className="flex-1 p-8">
            <div className="max-w-6xl mx-auto">
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-lg font-semibold text-red-800">Access Restricted</h3>
                  <p className="text-red-700 mt-1">
                    You do not have permission to view this section. Only administrators can access Settings.
                  </p>
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
              <p className="text-gray-500 mt-1">Manage users, APIs, LLM configurations, and view all jobs</p>
            </div>

            {/* Tab Navigation */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-1 px-6" aria-label="Tabs">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`
                          flex items-center gap-2 px-4 py-4 text-sm font-medium border-b-2 transition-colors
                          ${isActive
                            ? 'border-blue-600 text-blue-700'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                          }
                        `}
                      >
                        <Icon className="h-5 w-5" />
                        {tab.label}
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {componentLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                  </div>
                ) : TabComponent ? (
                  <TabComponent />
                ) : (
                  <div className="text-center text-gray-500 py-12">
                    Select a tab to view its content
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
