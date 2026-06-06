import { useState } from "react";
import Home from "./pages/Home";
import NovelDetail from "./pages/NovelDetail";
import ProjectDetail from "./pages/ProjectDetail";
import Settings from "./pages/Settings";
import CreateNovelModal from "./components/CreateNovelModal";

type Page =
  | { kind: "home" }
  | { kind: "novel"; novelId: string }
  | { kind: "chapter"; chapterId: string }
  | { kind: "settings" };

export default function App() {
  const [page, setPage] = useState<Page>({ kind: "home" });
  const [showCreateNovel, setShowCreateNovel] = useState(false);

  const navigate = (p: Page) => setPage(p);

  switch (page.kind) {
    case "home":
      return (
        <>
          <Home
            onNewNovel={() => setShowCreateNovel(true)}
            onSelectNovel={(id) => navigate({ kind: "novel", novelId: id })}
            onSelectChapter={(id) => navigate({ kind: "chapter", chapterId: id })}
            onSettings={() => navigate({ kind: "settings" })}
          />
          {showCreateNovel && (
            <CreateNovelModal
              onCreated={(id) => { setShowCreateNovel(false); navigate({ kind: "novel", novelId: id }); }}
              onClose={() => setShowCreateNovel(false)}
            />
          )}
        </>
      );
    case "novel":
      return (
        <NovelDetail
          novelId={page.novelId}
          onBack={() => navigate({ kind: "home" })}
          onSelectChapter={(id) => navigate({ kind: "chapter", chapterId: id })}
        />
      );
    case "chapter":
      return (
        <ProjectDetail
          projectId={page.chapterId}
          onBack={() => {
            // 回到所属小说
            fetch(`/api/projects/${page.chapterId}`)
              .then(r => r.json())
              .then(d => {
                if (d.novel_id) {
                  navigate({ kind: "novel", novelId: d.novel_id });
                } else {
                  navigate({ kind: "home" });
                }
              })
              .catch(() => navigate({ kind: "home" }));
          }}
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
