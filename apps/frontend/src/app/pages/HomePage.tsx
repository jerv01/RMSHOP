import { DevApiStatus } from "@/app/DevApiStatus";

export function HomePage() {
  return (
    <>
      <h1 className="text-2xl font-bold">RM Shop</h1>
      {import.meta.env.DEV && <DevApiStatus />}
    </>
  );
}
