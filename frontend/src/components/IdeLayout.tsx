import type { ReactNode } from "react";

interface IdeLayoutProps {
  header: ReactNode;
  children: ReactNode;
}

export function IdeLayout({ header, children }: IdeLayoutProps) {
  return (
    <div className="ide-layout retro-screen">
      {header}
      <main className="ide-workspace">{children}</main>
    </div>
  );
}
