import { useState } from "react";
import { useEffect } from "react";

function CaseForm() {
  const [drug, setDrug] = useState("");
  const [reaction, setReaction] = useState("");
  const [phone, setPhone] = useState("");
  const [risk, setRisk] = useState("");
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState("");
  const [caseId, setCaseId] = useState(null);
  const [message, setMessage] = useState("");
  const [points, setPoints] = useState(20);
  const [completed, setCompleted] = useState(false);
  const [streak, setStreak] = useState(1);
  const [level, setLevel] = useState("Bronze");
  const [leaderboard, setLeaderboard] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [allAnswers, setAllAnswers] = useState([]);
  const [language, setLanguage] = useState(null);

useEffect(() => {
  const fetchLeaderboard = async () => {
    const res = await fetch("http://localhost:8000/leaderboard");
    const data = await res.json();
    setLeaderboard(data);
  };

  fetchLeaderboard();

  const interval = setInterval(fetchLeaderboard, 5000);
  return () => clearInterval(interval);
}, []);

  const submitCase = async () => {
    const res = await fetch("http://localhost:8000/submit-case", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drug_name: drug, reaction, phone, language: language }),
    });

    const data = await res.json();
    setRisk(data.risk_level);
    setQuestions(data.follow_up_questions);
    setCaseId(data.case_id);
  };

  const submitAnswers = async () => {
  await fetch("http://localhost:8000/submit-followup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      case_id: caseId,
      answers
    })
  });

  const newPoints = points + 30;
  setPoints(newPoints);
  setCompleted(true);
  setStreak(streak + 1);

  if (newPoints >= 100) setLevel("Gold");
  else if (newPoints >= 50) setLevel("Silver");
  else setLevel("Bronze");

  setAiMessage(
    "🌟 Excellent work! Your response helps protect patients and improve drug safety."
  );
};


  return (
    <div className="container">
      <div className="card-3d">
        <h2>🧾 Submit Adverse Drug Reaction</h2>
        {!language && (
  <div style={{
    background:"#fff",
    padding:"20px",
    borderRadius:"12px",
    marginBottom:"20px",
    textAlign:"center",
    boxShadow:"0 2px 10px rgba(0,0,0,0.08)"
  }}>
    <h3>🤖 Select Language / भाषा चुनें</h3>

    <div style={{display:"flex", justifyContent:"center", gap:"15px", marginTop:"15px"}}>

      <button onClick={()=>setLanguage("en")} className="btn">
        English
      </button>

      <button onClick={()=>setLanguage("hi")} className="btn">
        हिन्दी
      </button>

    </div>
  </div>
)}


        <label>Drug Name</label>
        <input value={drug} onChange={e => setDrug(e.target.value)} />

        <label>Reaction</label>
        <input value={reaction} onChange={e => setReaction(e.target.value)} />

        <label>Patient Phone</label>
        <input value={phone} onChange={e => setPhone(e.target.value)} />

        <button className="btn" onClick={submitCase}>
          Submit Case
        </button>

        {risk && (
          <p className={risk === "HIGH RISK" ? "high" : "low"}>
            Risk Level: {risk}
          </p>
        )}

        {questions.length > 0 && currentQuestionIndex < questions.length && (
        <div className="card-3d">

        <h2 className="title">🤖 AI Safety Assistant</h2>

        <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>

      <img
        src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
        alt="robot"
        style={{
        width: "90px",
        transform: "perspective(800px) rotateY(-6deg) rotateX(4deg)",
        filter: "drop-shadow(0px 18px 18px rgba(0,0,0,0.25))",
        transition: "all 0.4s ease",
        animation: "botBlink 4.5s infinite",
        transformOrigin: "center bottom"
  }}
  onMouseEnter={(e)=>{
    e.currentTarget.style.transform =
      "perspective(800px) rotateY(0deg) rotateX(0deg) scale(1.05)";
  }}
  onMouseLeave={(e)=>{
    e.currentTarget.style.transform =
      "perspective(800px) rotateY(-6deg) rotateX(4deg)";
  }}
/>

      <p style={{ fontSize: "18px" }}>
        <b>Question {currentQuestionIndex + 1}:</b><br />
        {questions[currentQuestionIndex]}
      </p>

    </div>

    <textarea
      placeholder="Type your answer..."
      value={currentAnswer}
      onChange={(e) => setCurrentAnswer(e.target.value)}
      rows={3}
    />

    <button
      className="btn"
      onClick={() => {
        setAllAnswers([...allAnswers, currentAnswer]);
        setCurrentAnswer("");
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }}
    >
      ➡️ Next
    </button>

  </div>
)}
{questions.length > 0 &&
 currentQuestionIndex === questions.length && (
  <div className="card-3d">

    <h2 className="title">✅ Follow-up Completed</h2>

    <button
      className="btn"
      onClick={async () => {
  await fetch("http://localhost:8000/submit-followup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      case_id: caseId,
      answers: allAnswers.join(" | ")
    })
  });

  // UI STATES
  const newPoints = points + 30;

  setPoints(newPoints);
  setCompleted(true);
  setStreak(streak + 1);

  if (newPoints >= 100) setLevel("Gold");
  else if (newPoints >= 50) setLevel("Silver");
  else setLevel("Bronze");

  setAiMessage(
    "🎉 Great job! Your responses help improve medicine safety."
  );
}}

    >
      📤 Submit All Answers
    </button>

  </div>
)}


      </div>
      {/* 🎮 Health Mission (Unified UI) */}
{caseId && (
  <div className="card-3d">

    <h2 className="title">🎮 Health Mission</h2>

    <p><b>Health Points</b></p>
    <div style={{ fontSize: "32px", fontWeight: "bold", color: "#2563eb" }}>
      {points} ⭐
    </div>

    <br />

    <p><b>Progress</b></p>
    <div className="progress">
      <div
        className="progress-fill"
        style={{ width: completed ? "100%" : "55%" }}
      ></div>
    </div>

    <br />
    <p><b>Status</b></p>
<ul>
  <li>✅ Case Submitted</li>
  <li>{completed ? "✅ Follow-up Completed" : "🕒 Follow-up Pending"}</li>
  <li>🔵 Under Safety Monitoring</li>
</ul>
<p><b>Level:</b> {level}</p>
<p>🔥 Streak: {streak} day(s)</p>


    <p><b>Achievements</b></p>

    <span className="badge">🛡 Safety Rookie</span>
    {completed && <span className="badge">🏆 Follow-up Hero</span>}

    <br /><br />

    {!completed ? (
      <>
        <p>🎯 Complete follow-up questions to unlock rewards</p>
        <button className="btn">
          🚀 Complete Mission
        </button>
      </>
    ) : (
      <p style={{ color: "#16a34a", fontWeight: "bold" }}>
        🎉 Mission Completed! Thank you for helping drug safety.
      </p>
    )}

  </div>
)}
{/* 🏆 Real-Time Leaderboard */}
<div className="card-3d">

  <h2 className="title">🏆 Safety Champions Leaderboard</h2>

  {leaderboard.length === 0 ? (
    <p>No responses yet</p>
  ) : (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Case ID</th>
          <th>Responses</th>
        </tr>
      </thead>
      <tbody>
        {leaderboard.map((item, index) => (
          <tr key={item.id}>
            <td>#{index + 1}</td>
            <td>Case {item.id}</td>
            <td>⭐ {item.responses}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )}

</div>



    </div>
  );
}

export default CaseForm;
