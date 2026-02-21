import { useState, useEffect } from "react";
import "./styles.css";

function PatientDashboard() {
  const [patients, setPatients] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [isRunningComparison, setIsRunningComparison] = useState(false);

  const API_BASE = "http://localhost:8000/api/patients";

  useEffect(() => {
    fetchPatients();
    fetchSummary();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await fetch(`${API_BASE}/`);
      const data = await response.json();
      setPatients(data);
    } catch (error) {
      console.error("Error fetching patients:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/summary`);
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error("Error fetching summary:", error);
    }
  };

  const runComparison = async () => {
    setIsRunningComparison(true);
    try {
      const response = await fetch(`${API_BASE}/run-comparison`, {
        method: "POST",
      });
      const data = await response.json();
      alert(data.message);
      await fetchPatients();
      await fetchSummary();
    } catch (error) {
      console.error("Error running comparison:", error);
      alert("Error running comparison");
    } finally {
      setIsRunningComparison(false);
    }
  };

  const fetchPatientQuestions = async (contactNo) => {
    try {
      const response = await fetch(`${API_BASE}/${contactNo}/questions`);
      const data = await response.json();
      setQuestions(data.questions);
      setSelectedPatient(data.patient_info);
      setCurrentQuestionIndex(0);
      setAnswer("");
      setFeedback("");
    } catch (error) {
      console.error("Error fetching questions:", error);
      alert("Error fetching patient questions");
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) {
      setFeedback("Please provide an answer");
      return;
    }

    const currentQuestion = questions[currentQuestionIndex];
    if (!currentQuestion.response_id) {
      setFeedback("Question not properly loaded");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/submit-response`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          response_id: currentQuestion.response_id,
          patient_answer: answer,
        }),
      });

      const data = await response.json();
      
      if (data.is_correct) {
        setFeedback("✅ Correct answer!");
      } else {
        setFeedback(`❌ Incorrect. Expected: ${data.expected_answer}`);
      }

      // Update the question in the list
      const updatedQuestions = [...questions];
      updatedQuestions[currentQuestionIndex] = {
        ...currentQuestion,
        patient_answer: answer,
        is_answered: true,
        is_correct: data.is_correct,
      };
      setQuestions(updatedQuestions);

      // Move to next question after a short delay
      setTimeout(() => {
        if (currentQuestionIndex < questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1);
          setAnswer("");
          setFeedback("");
        } else {
          setFeedback("🎉 All questions completed for this patient!");
          fetchPatients();
          fetchSummary();
        }
      }, 2000);

    } catch (error) {
      console.error("Error submitting answer:", error);
      setFeedback("Error submitting answer");
    }
  };

  const resetPatientSession = () => {
    setSelectedPatient(null);
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setAnswer("");
    setFeedback("");
  };

  if (loading) {
    return <div className="container"><h2>Loading patient data...</h2></div>;
  }

  return (
    <div className="container">
      <div className="navbar">
        Patient Data Collection System
      </div>

      {/* Summary Section */}
      <div className="summary-section">
        <h2>System Overview</h2>
        <div className="summary-cards">
          <div className="summary-card">
            <h3>{summary.total_patients || 0}</h3>
            <p>Total Patients</p>
          </div>
          <div className="summary-card">
            <h3>{summary.completed_patients || 0}</h3>
            <p>Completed</p>
          </div>
          <div className="summary-card">
            <h3>{summary.pending_patients || 0}</h3>
            <p>Pending</p>
          </div>
          <div className="summary-card">
            <h3>{summary.overall_completion_percentage || 0}%</h3>
            <p>Overall Progress</p>
          </div>
        </div>
        <button 
          className="btn btn-primary" 
          onClick={runComparison}
          disabled={isRunningComparison}
        >
          {isRunningComparison ? "Running Comparison..." : "Run CSV Comparison"}
        </button>
      </div>

      {!selectedPatient ? (
        /* Patients List View */
        <div>
          <h2>Patient List</h2>
          <div className="patient-grid">
            {patients.map((patient) => (
              <div key={patient.contact_no} className="patient-card">
                <h3>{patient.patient_initials}</h3>
                <p><strong>PHN:</strong> {patient.contact_no}</p>
                <p><strong>Questions:</strong> {patient.answered_correctly}/{patient.total_questions}</p>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${patient.completion_percentage}%` }}
                  ></div>
                </div>
                <p className="progress-text">{patient.completion_percentage}% Complete</p>
                <button 
                  className="btn btn-secondary"
                  onClick={() => fetchPatientQuestions(patient.contact_no)}
                  disabled={patient.completion_percentage === 100}
                >
                  {patient.completion_percentage === 100 ? "Completed" : "Start Session"}
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Question Session View */
        <div className="question-session">
          <div className="session-header">
            <h2>Patient Session: {selectedPatient.patient_initials} (PHN: {selectedPatient.contact_no})</h2>
            <button className="btn btn-secondary" onClick={resetPatientSession}>
              ← Back to Patients
            </button>
          </div>

          {questions.length > 0 && currentQuestionIndex < questions.length && (
            <div className="question-card">
              <div className="question-progress">
                Question {currentQuestionIndex + 1} of {questions.length}
              </div>
              
              <div className="question-content">
                <h3>{questions[currentQuestionIndex].question}</h3>
                
                <div className="answer-section">
                  <textarea
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="answer-input"
                    rows="3"
                  />
                  
                  <div className="question-actions">
                    <button 
                      className="btn btn-primary"
                      onClick={submitAnswer}
                      disabled={!answer.trim()}
                    >
                      Submit Answer
                    </button>
                  </div>
                </div>

                {feedback && (
                  <div className={`feedback ${feedback.includes("✅") ? "correct" : "incorrect"}`}>
                    {feedback}
                  </div>
                )}
              </div>
            </div>
          )}

          {currentQuestionIndex >= questions.length && (
            <div className="completion-message">
              <h2>🎉 Session Complete!</h2>
              <p>All questions have been answered for this patient.</p>
              <button className="btn btn-primary" onClick={resetPatientSession}>
                Back to Patient List
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PatientDashboard;
