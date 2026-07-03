import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import StatusPage from "./pages/StatusPage";
import PredictionPage from "./pages/PredictionPage";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900">
        <Header />
        <Routes>
          <Route path="/" element={<StatusPage />} />
          <Route path="/prediction" element={<PredictionPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;