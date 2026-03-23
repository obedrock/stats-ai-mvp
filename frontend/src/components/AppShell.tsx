import { useState } from "react";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <main className="flex-1 overflow-auto p-6">
        {children}
      </main>
    </div>
  );
}
