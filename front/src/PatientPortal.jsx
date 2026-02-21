import { useState, useEffect } from "react";
import "./styles.css";

function PatientPortal() {
  const [phnNumber, setPhnNumber] = useState("");
  const [patientInfo, setPatientInfo] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState({});

  const API_BASE = "http://localhost:8000/api/patients";

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/summary`);
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      console.error("Error fetching summary:", error);
    }
  };

  const lookupPatient = async () => {
    if (!phnNumber.trim()) {
      setError("Please enter your PHN number");
      return;
    }

    setLoading(true);
    setError("");
    setFeedback("");

    try {
      const response = await fetch(`${API_BASE}/lookup-phn`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ phn_no: phnNumber.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Patient not found");
      }

      const data = await response.json();
      setPatientInfo(data.patient_info);
      setQuestions(data.questions);
      setCurrentQuestionIndex(0);
      setAnswer("");
      
      if (data.questions.length === 0) {
        setFeedback("🎉 All questions have been completed for this patient!");
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) {
      setFeedback("Please provide an answer");
      return;
    }

    const currentQuestion = questions[currentQuestionIndex];
    if (!currentQuestion) {
      setFeedback("No question available");
      return;
    }

    setLoading(true);
    setFeedback("");

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

      if (!response.ok) {
        throw new Error("Failed to submit answer");
      }

      const data = await response.json();
      setFeedback("✅ Response saved successfully!");

      // Update the question in the list as answered
      const updatedQuestions = [...questions];
      updatedQuestions[currentQuestionIndex] = {
        ...currentQuestion,
        patient_answer: answer,
        is_answered: true,
      };
      setQuestions(updatedQuestions);

      // Update patient info with new completion percentage
      setPatientInfo(prev => ({
        ...prev,
        completion_percentage: data.completion_percentage,
        answered_correctly: prev.answered_correctly + 1
      }));

      // Move to next question after a short delay
      setTimeout(() => {
        if (currentQuestionIndex < questions.length - 1) {
          setCurrentQuestionIndex(currentQuestionIndex + 1);
          setAnswer("");
          setFeedback("");
        } else {
          // All questions completed - show risk classification
          const riskStatus = data.is_completed ? getPatientRiskStatus() : "Processing...";
          setFeedback(`🎉 All questions completed! Risk Status: ${riskStatus}`);
          fetchSummary(); // Update overall summary
        }
      }, 2000);

    } catch (error) {
      setFeedback("Error submitting answer. Please try again.");
      console.error("Error submitting answer:", error);
    } finally {
      setLoading(false);
    }
  };

  const getPatientRiskStatus = () => {
    // This will be updated from backend after completion
    return "Assessing...";
  };

  const resetSession = () => {
    setPhnNumber("");
    setPatientInfo(null);
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setAnswer("");
    setFeedback("");
    setError("");
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !patientInfo) {
      lookupPatient();
    }
  };

  return (
    <div className="container">
      <div className="navbar">
        Patient Data Collection Portal
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
            <h3>{summary.high_risk_patients || 0}</h3>
            <p>High Risk</p>
          </div>
          <div className="summary-card">
            <h3>{summary.low_risk_patients || 0}</h3>
            <p>Low Risk</p>
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
      </div>

      {!patientInfo ? (
        /* PHN Entry View */
        <div className="phn-entry">
          <div className="phn-card">
            <h2>Enter Your PHN Number</h2>
            <p>Please enter your Personal Health Number to access your questionnaire</p>
            
            <div className="input-group">
              <input
                type="text"
                value={phnNumber}
                onChange={(e) => setPhnNumber(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter your 10-digit PHN number"
                className="phn-input"
                maxLength={10}
              />
              <button 
                className="btn btn-primary"
                onClick={lookupPatient}
                disabled={loading || !phnNumber.trim()}
              >
                {loading ? "Looking up..." : "Continue"}
              </button>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Question Session View */
        <div className="question-session">
          <div className="session-header">
            <div>
              <h2>Patient: {patientInfo.patient_initials}</h2>
              <p>PHN: {patientInfo.contact_no}</p>
              <p>Progress: {patientInfo.answered_correctly}/{patientInfo.total_questions} ({patientInfo.completion_percentage}%)</p>
            </div>
            <button className="btn btn-secondary" onClick={resetSession}>
              New Patient
            </button>
          </div>

          {questions.length > 0 && currentQuestionIndex < questions.length ? (
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
                    autoFocus
                  />
                  
                  <div className="question-actions">
                    <button 
                      className="btn btn-primary"
                      onClick={submitAnswer}
                      disabled={loading || !answer.trim()}
                    >
                      {loading ? "Submitting..." : "Submit Answer"}
                    </button>
                  </div>
                </div>

                {feedback && (
                  <div className={`feedback ${feedback.includes("✅") ? "success" : ""}`}>
                    {feedback}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="completion-message">
              <h2>🎉 Session Complete!</h2>
              <p>All questions have been answered for this patient.</p>
              <div className="completion-stats">
                <p><strong>Patient:</strong> {patientInfo.patient_initials}</p>
                <p><strong>PHN:</strong> {patientInfo.contact_no}</p>
                <p><strong>Questions Answered:</strong> {patientInfo.answered_correctly}/{patientInfo.total_questions}</p>
                <p><strong>Completion:</strong> {patientInfo.completion_percentage}%</p>
              </div>
              <button className="btn btn-primary" onClick={resetSession}>
                Start New Session
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PatientPortal;
