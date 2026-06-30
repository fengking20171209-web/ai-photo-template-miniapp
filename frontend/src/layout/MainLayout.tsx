import React from 'react';
import { AssetSidebar } from '../components/AssetSidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen w-full bg-white overflow-hidden">
      {/* Left Column: Navigation / Inspiration */}
      <aside className="w-64 border-r border-gray-200 bg-gray-50 flex flex-col hidden md:flex">
        <div className="p-4 border-b border-gray-200 font-bold">Left Sidebar</div>
        <div className="flex-1 p-4">Inspiration & Nav</div>
      </aside>

      {/* Middle Column: Main Content (The "Brain" / Chat / Generation) */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="p-4 border-b border-gray-200 font-bold">Middle - Main Workspace</header>
        <div className="flex-1 overflow-auto p-4">
          {children}
        </div>
      </main>

      {/* Right Column: Asset Waterfall & Traceability */}
      <aside className="w-80 border-l border-gray-200 hidden lg:flex flex-col">
        <AssetSidebar />
      </aside>
    </div>
  );
};
