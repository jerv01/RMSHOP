import wolfLogoUrl from "@/assets/logo-lobo.jpg";

interface BrandLogoProps {
  subtitle?: string;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-14 w-14",
} as const;

export { wolfLogoUrl };

export function BrandLogo({ subtitle, size = "md" }: BrandLogoProps) {
  return (
    <span className="inline-flex items-center gap-3">
      <img
        src={wolfLogoUrl}
        alt="Logotipo de RM Shop"
        width={40}
        height={40}
        className={`${sizeClasses[size]} rounded-[2px] border border-border object-contain bg-background`}
      />
      <span className="flex flex-col leading-tight">
        <span className="text-lg font-bold tracking-wider uppercase text-foreground">RM Shop</span>
        {subtitle && <span className="text-xs font-medium text-muted">{subtitle}</span>}
      </span>
    </span>
  );
}
