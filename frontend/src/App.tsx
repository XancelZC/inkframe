import { useState } from "react";
import Home from "./pages/Home";
import NewProject from "./pages/NewProject";
import ProjectDetail from "./pages/ProjectDetail";
import Settings from "./pages/Settings";

type Page =
  | { kind: "home" }
  | { kind: "new" }
  | { kind: "detail"; projectId: string }
  | { kind: "settings" };

export default function App() {
  const [page, setPage] = useState<Page>({ kind: "home" });

  const navigate = (p: Page) => setPage(p);

  switch (page.kind) {
    case "home":
      return (
        <Home
          onNewProject={() => navigate({ kind: "new" })}
          onSelectProject={(id) => navigate({ kind: "detail", projectId: id })}
          onSettings={() => navigate({ kind: "settings" })}
        />
      );
    case "new":
      return (
        <NewProject
          onBack={() => navigate({ kind: "home" })}
          onCreated={(id) => navigate({ kind: "detail", projectId: id })}
        />
      );
    case "detail":
      return (
        <ProjectDetail
          projectId={page.projectId}
          onBack={() => navigate({ kind: "home" })}
        />
      );
    case "settings":
      return (
        <Settings
          onBack={() => navigate({ kind: "home" })}
        />
      );
  }
}
