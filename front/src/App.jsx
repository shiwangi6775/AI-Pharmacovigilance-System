import { useState } from "react";
import CaseForm from "./CaseForm";
import Dashboard from "./Dashboard";
import PatientPortal from "./PatientPortal";
import "./styles.css";

function App() {
  const [page, setPage] = useState("portal");

  return (
    <>
      <div className="navbar">
        AI Pharmacovigilance System
      </div>

      <div style={{ padding: 20 }}>
        <button className="btn" onClick={() => setPage("form")}>
          Submit Case
        </button>

        <button className="btn" onClick={() => setPage("dashboard")}>
          View Dashboard
        </button>

        <button className="btn" onClick={() => setPage("portal")}>
          Patient Portal
        </button>
      </div>

      {page === "form" ? <CaseForm /> : 
       page === "dashboard" ? <Dashboard /> : 
       <PatientPortal />}
    </>
  );
}

export default App;
