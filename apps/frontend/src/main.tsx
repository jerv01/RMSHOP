import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { ConfigMissing } from "./app/ConfigMissing";
import { Providers } from "./app/providers";
import { router } from "./app/router";
import { env } from "./shared/lib/env";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {env.clerkPublishableKey ? (
      <Providers>
        <RouterProvider router={router} />
      </Providers>
    ) : (
      <ConfigMissing />
    )}
  </StrictMode>,
);
