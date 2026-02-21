import Sidebar from "../components/Sidebar";
import CaseTable from "../components/CaseTable";

export default function Dashboard() {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />

      <div className="flex-1 p-6">
        <h1 className="text-3xl font-bold mb-6">
          Pharmacovigilance Dashboard
        </h1>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded shadow">Total Cases</div>
          <div className="bg-red-100 p-4 rounded shadow">High Risk</div>
          <div className="bg-green-100 p-4 rounded shadow">Low Risk</div>
          <div className="bg-blue-100 p-4 rounded shadow">Follow-ups</div>
        </div>

        <CaseTable />
      </div>
    </div>
  );
}
  