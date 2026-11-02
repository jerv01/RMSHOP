import { Link, Outlet } from "react-router";
import { SessionControls } from "@/features/auth/SessionControls";

export function StoreLayout() {
  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-gray-200 p-4">
        <Link to="/" className="text-lg font-semibold">
          RM Shop
        </Link>
        <SessionControls />
      </header>
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
}
