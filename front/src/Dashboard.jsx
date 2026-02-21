import { useEffect, useState } from "react";

function Dashboard() {
  const [cases, setCases] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/cases")
      .then(res => res.json())
      .then(data => setCases(data));
  }, []);

  const highRisk = cases.filter(c => c.risk_level === "HIGH RISK");

  return (
    <div className="container">
      <div className="card-3d">

      {highRisk.length > 0 && (
        <div className="alert">
          🚨 {highRisk.length} HIGH RISK case(s) detected — Immediate attention required!
        </div>
      )}

      <h2>📊 Pharmacovigilance Dashboard</h2>

      <table>
        <thead>
          <tr>
            <th>Drug</th>
            <th>Reaction</th>
            <th>Risk</th>
            <th>Phone</th>
          </tr>
        </thead>
        <tbody>
          {cases.map(c => (
            <tr key={c.id}>
              <td>{c.drug_name}</td>
              <td>{c.reaction}</td>
              <td className={c.risk_level === "HIGH RISK" ? "high" : "low"}>
                {c.risk_level}
              </td>
              <td>{c.phone}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </div>
  );
}

export default Dashboard;
