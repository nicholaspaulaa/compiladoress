import type { ReactNode } from "react";

interface IdeLayoutProps {
  header: ReactNode;
  toolbar?: ReactNode;
  children: ReactNode;
}

export function IdeLayout({ header, toolbar, children }: IdeLayoutProps) {
  return (
    <div className="ide-layout retro-screen">
      {header}
      {toolbar}
      <main className="ide-workspace">{children}</main>
    </div>
  );
}
