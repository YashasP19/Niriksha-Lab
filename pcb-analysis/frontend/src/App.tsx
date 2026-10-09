import { BrowserRouter, Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px" }}>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 0",
            borderBottom: "1px solid #1e293b",
            marginBottom: 24,
          }}
        >
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>
            Arduino Uno R3 Defect Detection
          </h1>
        </header>
        <Routes>
          <Route path="/" element={<UploadPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
