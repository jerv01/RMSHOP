import { ClerkProvider } from "@clerk/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { env } from "@/shared/lib/env";
import { wolfLogoUrl } from "@/shared/ui/BrandLogo";
import { localization } from "./localization";
import { router } from "./router";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

const clerkAppearance = {
  layout: {
    logoImageUrl: wolfLogoUrl,
    logoPlacement: "inside" as const,
  },
  variables: {
    colorPrimary: "#000000",
    colorText: "#000000",
    colorTextOnPrimaryBackground: "#FFFFFF",
    colorTextSecondary: "#767677",
    colorBackground: "#FFFFFF",
    colorInputBackground: "#FFFFFF",
    colorInputText: "#000000",
    colorDanger: "#E4002B",
    colorSuccess: "#1F7A5C",
    colorWarning: "#B26A00",
    borderRadius: "2px",
  },
  elements: {
    card: "rounded-[2px] border border-[#E0E0E0] shadow-[0_2px_8px_rgba(0,0,0,0.08)]",
    formButtonPrimary:
      "min-h-11 rounded-[2px] bg-[#000000] text-[#FFFFFF] uppercase tracking-wider font-semibold hover:bg-[#000000]/90",
    formFieldInput: "min-h-11 rounded-[2px] border-[#000000] text-[#000000]",
    footerActionLink: "text-[#000000] font-semibold underline",
  },
};

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider
      publishableKey={env.clerkPublishableKey}
      localization={localization}
      appearance={clerkAppearance}
      afterSignOutUrl="/"
      // Clerk navega con el router de la SPA en lugar de recargar la página.
      routerPush={(to) => router.navigate(to)}
      routerReplace={(to) => router.navigate(to, { replace: true })}
    >
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ClerkProvider>
  );
}
