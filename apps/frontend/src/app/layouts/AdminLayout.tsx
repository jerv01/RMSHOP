import { Outlet } from "react-router";

export function AdminLayout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-200 p-4">
        <span className="text-lg font-semibold">RM Shop · Panel de administración</span>
      </header>
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
}
