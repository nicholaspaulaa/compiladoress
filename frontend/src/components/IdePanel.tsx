import type { ReactNode } from "react";

interface IdePanelProps {
  label: string;
  ariaLabel: string;
  children: ReactNode;
  className?: string;
}

export function IdePanel({
  label,
  ariaLabel,
  children,
  className = "",
}: IdePanelProps) {
  return (
    <section
      className={`ide-panel ${className}`.trim()}
      aria-label={ariaLabel}
    >
      <header className="ide-panel__header retro-subtitle">{label}</header>
      <div className="ide-panel__body">{children}</div>
    </section>
  );
}
