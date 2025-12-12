'use client';

import { Header } from '@/components/Header';
import { SidebarNav } from '@/components/SidebarNav';

export default function EWayBillsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <SidebarNav />
        <main className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Created Draft E-Way Bills</h1>
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              <p>Work in progress</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

