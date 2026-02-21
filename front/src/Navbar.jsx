function Navbar({ setPage }) {
  return (
    <div className="navbar">
      <span>🧠 AI Pharmacovigilance System</span>

      <div style={{ float: "right" }}>
        <button className="btn" onClick={() => setPage("form")}>
          Submit Case
        </button>

        <button className="btn" onClick={() => setPage("dashboard")}>
          Dashboard
        </button>
      </div>
    </div>
  );
}

export default Navbar;
