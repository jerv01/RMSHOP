import { Link, Outlet } from "react-router";

export function StoreLayout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-200 p-4">
        <Link to="/" className="text-lg font-semibold">
          RM Shop
        </Link>
      </header>
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
}
