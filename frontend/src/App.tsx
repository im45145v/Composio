import { Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { DirectoryPage } from "./pages/DirectoryPage";
import { GuidePage } from "./pages/GuidePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { ResearchPage } from "./pages/ResearchPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<DirectoryPage />} />
        <Route path="guides/:slug" element={<GuidePage />} />
        <Route path="research" element={<ResearchPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
