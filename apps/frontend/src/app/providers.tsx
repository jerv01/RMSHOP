import { ClerkProvider } from "@clerk/react";
import { esES } from "@clerk/localizations";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { env } from "@/shared/lib/env";
import { router } from "./router";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider
      publishableKey={env.clerkPublishableKey}
      localization={esES}
      afterSignOutUrl="/"
      // Clerk navega con el router de la SPA en lugar de recargar la página.
      routerPush={(to) => router.navigate(to)}
      routerReplace={(to) => router.navigate(to, { replace: true })}
    >
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ClerkProvider>
  );
}
