import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:5000/predict";
const MONTH_COUNT = 5;

const emptyMonth = {
  menstrualPainLevel: "",
  painDuration: "",
  heavyMenstrualBleeding: "",
  menstrualIrregularity: "",
  pelvicPainLevel: "",
  infertility: "",
};

const emptyPersonal = {
  age: "",
  height: "",
  weight: "",
};

const createMonths = () =>
  Array.from({ length: MONTH_COUNT }, () => ({ ...emptyMonth }));

const isMonthComplete = (month) =>
  Object.values(month).every((value) => value !== "" && value !== null && value !== undefined);

function App() {
  const [page, setPage] = useState("home");
  const [user, setUser] = useState(null);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({ name: "", email: "", password: "" });
  const [personalData, setPersonalData] = useState({ ...emptyPersonal });
  const [monthlyData, setMonthlyData] = useState(createMonths);
  const [currentMonth, setCurrentMonth] = useState(0);
  const [predictionResult, setPredictionResult] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const bmiPreview = useMemo(() => {
    const height = Number(personalData.height);
    const weight = Number(personalData.weight);
    if (!height || !weight || height <= 0 || weight <= 0) return null;
    return weight / Math.pow(height / 100, 2);
  }, [personalData.height, personalData.weight]);

  useEffect(() => {
    const currentEmail = localStorage.getItem("endoCareCurrentUser");
    if (!currentEmail) return;

    const saved = localStorage.getItem(`user_${currentEmail}`);
    if (!saved) return;

    try {
      const savedUser = JSON.parse(saved);
      setUser(savedUser);
      setPersonalData(savedUser.personalData || { ...emptyPersonal });
      setMonthlyData(normalizeMonths(savedUser.monthlyData));
      setPredictionResult(savedUser.predictionResult || null);
      setPage("dashboard");
    } catch {
      localStorage.removeItem("endoCareCurrentUser");
    }
  }, []);

  function normalizeMonths(savedMonths) {
    const months = Array.isArray(savedMonths) ? savedMonths : [];
    return Array.from({ length: MONTH_COUNT }, (_, index) => ({
      ...emptyMonth,
      ...(months[index] || {}),
    }));
  }

  const saveUser = (updatedUser) => {
    localStorage.setItem(`user_${updatedUser.email}`, JSON.stringify(updatedUser));
    localStorage.setItem("endoCareCurrentUser", updatedUser.email);
    setUser(updatedUser);
  };

  const clearMessage = () => setMessage("");

  const goTo = (nextPage) => {
    clearMessage();
    setPage(nextPage);
  };

  const handleRegister = (event) => {
    event.preventDefault();
    clearMessage();

    const name = registerData.name.trim();
    const email = registerData.email.trim().toLowerCase();
    const password = registerData.password;

    if (!name) {
      setMessage("Please enter your full name.");
      return;
    }

    if (password.length < 6) {
      setMessage("Password must contain at least 6 characters.");
      return;
    }

    if (localStorage.getItem(`user_${email}`)) {
      setMessage("An account with this email already exists. Please login.");
      return;
    }

    const newUser = {
      name,
      email,
      password,
      personalData: null,
      monthlyData: [],
      predictionResult: null,
    };

    saveUser(newUser);
    setPersonalData({ ...emptyPersonal });
    setMonthlyData(createMonths());
    setCurrentMonth(0);
    setPredictionResult(null);
    setRegisterData({ name: "", email: "", password: "" });
    setPage("personalDetails");
  };

  const handleLogin = (event) => {
    event.preventDefault();
    clearMessage();

    const email = loginData.email.trim().toLowerCase();
    const saved = localStorage.getItem(`user_${email}`);

    if (!saved) {
      setMessage("User not found. Please register first.");
      return;
    }

    try {
      const savedUser = JSON.parse(saved);

      if (savedUser.password !== loginData.password) {
        setMessage("Incorrect password.");
        return;
      }

      const savedMonths = normalizeMonths(savedUser.monthlyData);
      const completedMonths = savedMonths.filter(isMonthComplete).length;

      setUser(savedUser);
      setPersonalData(savedUser.personalData || { ...emptyPersonal });
      setMonthlyData(savedMonths);
      setPredictionResult(savedUser.predictionResult || null);
      localStorage.setItem("endoCareCurrentUser", email);
      setLoginData({ email: "", password: "" });

      if (savedUser.personalData && completedMonths === MONTH_COUNT) {
        setCurrentMonth(0);
        setPage("dashboard");
      } else if (savedUser.personalData) {
        setCurrentMonth(Math.min(completedMonths, MONTH_COUNT - 1));
        setPage("monthlyForm");
      } else {
        setCurrentMonth(0);
        setPage("personalDetails");
      }
    } catch {
      setMessage("Saved account data is invalid. Please register again.");
    }
  };

  const handlePersonalSubmit = (event) => {
    event.preventDefault();
    clearMessage();

    const age = Number(personalData.age);
    const height = Number(personalData.height);
    const weight = Number(personalData.weight);

    if (!Number.isFinite(age) || age < 18 || age > 100) {
      setMessage("Age must be between 18 and 100.");
      return;
    }
    if (!Number.isFinite(height) || height < 100 || height > 220) {
      setMessage("Height must be between 100 cm and 220 cm.");
      return;
    }
    if (!Number.isFinite(weight) || weight < 20 || weight > 200) {
      setMessage("Weight must be between 20 kg and 200 kg.");
      return;
    }

    const normalized = {
      age: String(age),
      height: String(height),
      weight: String(weight),
    };

    setPersonalData(normalized);

    if (user) {
      const updatedUser = {
        ...user,
        personalData: normalized,
        predictionResult: null,
      };
      saveUser(updatedUser);
    }

    setPredictionResult(null);
    setCurrentMonth(0);
    setPage("monthlyForm");
  };

  const updateMonth = (field, value) => {
    setMonthlyData((old) =>
      old.map((month, index) =>
        index === currentMonth ? { ...month, [field]: value } : month
      )
    );
  };

  const validateMonth = (index = currentMonth) => {
    const month = monthlyData[index];

    if (!month.menstrualPainLevel) {
      setMessage("Please enter menstrual pain level.");
      return false;
    }
    if (!month.painDuration) {
      setMessage("Please enter pain duration.");
      return false;
    }
    if (month.heavyMenstrualBleeding === "") {
      setMessage("Please select heavy menstrual bleeding.");
      return false;
    }
    if (month.menstrualIrregularity === "") {
      setMessage("Please select menstrual irregularity.");
      return false;
    }
    if (!month.pelvicPainLevel && month.pelvicPainLevel !== "0") {
      setMessage("Please enter pelvic pain level.");
      return false;
    }
    if (month.infertility === "") {
      setMessage("Please select infertility.");
      return false;
    }

    const menstrualPain = Number(month.menstrualPainLevel);
    const duration = Number(month.painDuration);
    const pelvicPain = Number(month.pelvicPainLevel);

    if (!Number.isInteger(menstrualPain) || menstrualPain < 0 || menstrualPain > 10) {
      setMessage("Menstrual pain must be an integer from 0 to 10.");
      return false;
    }
    if (!Number.isInteger(duration) || duration < 1 || duration > 31) {
      setMessage("Pain duration must be an integer from 1 to 31 days.");
      return false;
    }
    if (!Number.isInteger(pelvicPain) || pelvicPain < 0 || pelvicPain > 10) {
      setMessage("Pelvic pain must be an integer from 0 to 10.");
      return false;
    }

    return true;
  };

  const persistCurrentData = (prediction = predictionResult) => {
    if (!user) return;

    const updatedUser = {
      ...user,
      personalData,
      monthlyData,
      predictionResult: prediction,
    };
    saveUser(updatedUser);
  };

  const handleNextMonth = (event) => {
    event.preventDefault();
    clearMessage();

    if (!validateMonth()) return;

    const updatedMonths = monthlyData.map((month, index) =>
      index === currentMonth ? { ...month } : month
    );
    setMonthlyData(updatedMonths);

    if (user) {
      const updatedUser = {
        ...user,
        personalData,
        monthlyData: updatedMonths,
        predictionResult: null,
      };
      saveUser(updatedUser);
    }

    if (currentMonth < MONTH_COUNT - 1) {
      setCurrentMonth((month) => month + 1);
    }
  };

  const handlePreviousMonth = () => {
    clearMessage();
    if (currentMonth > 0) setCurrentMonth((month) => month - 1);
  };

  const analyzeRisk = async (event) => {
    event.preventDefault();
    clearMessage();

    for (let index = 0; index < MONTH_COUNT; index += 1) {
      if (!validateMonth(index)) {
        setCurrentMonth(index);
        return;
      }
    }

    const payload = {
      age: Number(personalData.age),
      height_cm: Number(personalData.height),
      weight_kg: Number(personalData.weight),
      monthly_data: monthlyData.map((month) => ({
        Menstrual_Pain_Level: Number(month.menstrualPainLevel),
        Pain_Duration: Number(month.painDuration),
        Heavy_Menstrual_Bleeding: Number(month.heavyMenstrualBleeding),
        Menstrual_Irregularity: Number(month.menstrualIrregularity),
        Pelvic_Pain_Level: Number(month.pelvicPainLevel),
        Infertility: Number(month.infertility),
      })),
    };

    try {
      setLoading(true);

      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let data;
      try {
        data = await response.json();
      } catch {
        throw new Error("Backend returned an invalid response.");
      }

      if (!response.ok || data.status !== "success") {
        throw new Error(data.message || "Prediction failed.");
      }

      if (!Array.isArray(data.monthly_results) || data.monthly_results.length !== MONTH_COUNT) {
        throw new Error("Backend returned an invalid 5-month prediction result.");
      }

      setPredictionResult(data);
      persistCurrentData(data);
      setPage("risk");
    } catch (error) {
      console.error("Prediction error:", error);
      setMessage(
        error.message?.includes("Failed to fetch")
          ? "Could not connect to Flask. Start the backend on http://127.0.0.1:5000."
          : error.message || "Prediction failed."
      );
    } finally {
      setLoading(false);
    }
  };

  const startNewAssessment = () => {
    clearMessage();
    setPersonalData({ ...emptyPersonal });
    setMonthlyData(createMonths());
    setCurrentMonth(0);
    setPredictionResult(null);
    if (user) {
      saveUser({
        ...user,
        personalData: null,
        monthlyData: [],
        predictionResult: null,
      });
    }
    setPage("personalDetails");
  };

  const updateInformation = () => {
    clearMessage();
    setPredictionResult(null);
    setCurrentMonth(0);
    setPage("personalDetails");
  };

  const handleLogout = () => {
    localStorage.removeItem("endoCareCurrentUser");
    setUser(null);
    setLoginData({ email: "", password: "" });
    setPredictionResult(null);
    setMessage("");
    setPage("home");
  };

  const brand = (
    <div className="brand">
      <div className="brand-icon">E</div>
      <div>
        <strong>EndoCare</strong>
        <small>Endometriosis Early Detection System</small>
      </div>
    </div>
  );

  if (page === "home") {
    return (
      <div className="home-page">
        <nav className="home-navbar">
          {brand}
          <div className="home-nav-links">
            <a href="#home">Home</a>
            <a href="#features">Features</a>
            <a href="#about">About</a>
            <button className="nav-login" onClick={() => goTo("login")}>Login</button>
          </div>
        </nav>

        <section className="hero-section" id="home">
          <div className="hero-left">
            <span className="hero-badge">ML-BASED EARLY SCREENING</span>
            <h1>Understand Your <span>Menstrual Health</span> Better</h1>
            <p>
              EndoCare is a non-invasive machine-learning based early risk screening
              system that analyzes menstrual and symptom information across five months.
            </p>
            <div className="hero-buttons">
              <button className="hero-primary" onClick={() => goTo("register")}>Get Started <span>→</span></button>
              <button className="hero-secondary" onClick={() => goTo("login")}>Existing User</button>
            </div>
            <div className="hero-info">
              <div><strong>5</strong><small>Months Tracking</small></div>
              <div><strong>LSTM</strong><small>Risk Analysis</small></div>
              <div><strong>9</strong><small>Health Features</small></div>
            </div>
          </div>

          <div className="hero-right">
            <div className="health-card">
              <div className="card-top">
                <div><small>MONTHLY HEALTH</small><h3>Track Your Symptoms</h3></div>
                <div className="heart-icon">♡</div>
              </div>
              <div className="tracking-circle"><strong>5</strong><span>Months</span></div>
              <div className="tracking-details">
                <div><span>Menstrual Data</span><strong>✓</strong></div>
                <div><span>Symptom Tracking</span><strong>✓</strong></div>
                <div><span>LSTM Assessment</span><strong>Ready</strong></div>
              </div>
            </div>
          </div>
        </section>

        <section className="features-section" id="features">
          <div className="section-title">
            <span>HOW IT WORKS</span>
            <h2>Simple. Personal. Data-driven.</h2>
            <p>Record health information month by month and analyze the five-month sequence using the LSTM model.</p>
          </div>
          <div className="feature-grid">
            <div className="feature-card"><div className="feature-number">01</div><h3>Create Your Account</h3><p>Register and create your personal profile before starting the assessment.</p></div>
            <div className="feature-card"><div className="feature-number">02</div><h3>Track 5 Months</h3><p>Enter six menstrual and symptom features for each of five months.</p></div>
            <div className="feature-card"><div className="feature-number">03</div><h3>LSTM Risk Assessment</h3><p>The five-month sequence is sent to the trained LSTM model for risk analysis.</p></div>
          </div>
        </section>

        <section className="about-section" id="about">
          <span className="section-label">ABOUT ENDOCARE</span>
          <h2>Early awareness through technology.</h2>
          <p>EndoCare is designed as a non-invasive machine-learning based system for early risk screening of endometriosis.</p>
          <p>The system uses information collected across multiple menstrual cycles rather than relying on one month alone.</p>
        </section>

        <footer className="home-footer">{brand}<p>Endometriosis Early Detection Project</p></footer>
      </div>
    );
  }

  if (page === "login" || page === "register") {
    const isLogin = page === "login";
    return (
      <div className="auth-page">
        <div className="auth-left">
          <div className="auth-brand">{brand}</div>
          <div className="auth-visual">
            <div className="auth-circle">{isLogin ? "♡" : "+"}</div>
            <h1>{isLogin ? <>Your health journey,<br /><span>tracked over time.</span></> : <>Start your<br /><span>health journey.</span></>}</h1>
            <p>{isLogin ? "Keep your monthly health information organized and ready for intelligent analysis." : "Create your account and begin recording your monthly health information."}</p>
          </div>
        </div>

        <div className="auth-right">
          <div className="auth-box">
            <button className="back-home" onClick={() => goTo("home")}>← Back to Home</button>
            <h2>{isLogin ? "Welcome back" : "Create your account"}</h2>
            <p className="auth-description">{isLogin ? "Login to access your health dashboard." : "It only takes a minute to get started."}</p>
            {message && <div className="error-message">{message}</div>}

            {isLogin ? (
              <form onSubmit={handleLogin}>
                <label>Email Address<input type="email" value={loginData.email} onChange={(e) => setLoginData({ ...loginData, email: e.target.value })} placeholder="you@example.com" required /></label>
                <label>Password<input type="password" value={loginData.password} onChange={(e) => setLoginData({ ...loginData, password: e.target.value })} placeholder="Enter your password" required /></label>
                <button className="auth-button" type="submit">Login <span>→</span></button>
              </form>
            ) : (
              <form onSubmit={handleRegister}>
                <label>Full Name<input type="text" value={registerData.name} onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })} placeholder="Enter your full name" required /></label>
                <label>Email Address<input type="email" value={registerData.email} onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })} placeholder="you@example.com" required /></label>
                <label>Create Password<input type="password" minLength="6" value={registerData.password} onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })} placeholder="At least 6 characters" required /></label>
                <button className="auth-button" type="submit">Create Account <span>→</span></button>
              </form>
            )}

            <div className="auth-divider"><span>OR</span></div>
            <p className="new-user">{isLogin ? "Don't have an account?" : "Already have an account?"} <button onClick={() => goTo(isLogin ? "register" : "login")}>{isLogin ? "Create Account" : "Login"}</button></p>
          </div>
        </div>
      </div>
    );
  }

  if (page === "personalDetails") {
    return (
      <div className="dashboard-page">
        <nav className="dashboard-navbar">{brand}<div className="dashboard-user">Hi, {user?.name}</div><div className="dashboard-nav-links"><button className="nav-link-button" onClick={() => setPage("dashboard")}>Dashboard</button>{predictionResult && <button className="nav-link-button" onClick={() => setPage("risk")}>Risk</button>}<button className="nav-link-button" onClick={() => setPage("monthlyForm")}>Update Symptoms</button><button className="logout-btn" onClick={handleLogout}>Logout</button></div></nav>
        <div className="personal-container">
          <div className="monthly-header"><span className="section-label">PERSONAL INFORMATION</span><h1>Tell us about yourself</h1><p>These details are entered once. Your menstrual symptoms will be recorded separately for five months.</p></div>
          {message && <div className="error-message">{message}</div>}
          <form className="personal-card" onSubmit={handlePersonalSubmit}>
            <div className="personal-icon">👤</div><h2>Basic Information</h2><p className="card-description">Please enter your basic information before starting monthly tracking.</p>
            <div className="personal-grid">
              <div className="input-group"><label>Age<input type="number" min="18" max="100" value={personalData.age} onChange={(e) => setPersonalData({ ...personalData, age: e.target.value })} placeholder="Enter your age" required /></label></div>
              <div className="input-group"><label>Height (cm)<input type="number" min="100" max="220" value={personalData.height} onChange={(e) => setPersonalData({ ...personalData, height: e.target.value })} placeholder="Example: 160" required /></label></div>
              <div className="input-group"><label>Weight (kg)<input type="number" step="0.1" min="20" max="200" value={personalData.weight} onChange={(e) => setPersonalData({ ...personalData, weight: e.target.value })} placeholder="Example: 55" required /></label></div>
            </div>
            {bmiPreview && <div className="info-note"><strong>BMI:</strong> {bmiPreview.toFixed(1)} will be calculated automatically from height and weight.</div>}
            <div className="info-note"><strong>Next:</strong> You will enter six menstrual and symptom features for five months.</div>
            <button type="submit" className="auth-button">Continue to Month 1 <span>→</span></button>
          </form>
        </div>
      </div>
    );
  }

  if (page === "monthlyForm") {
    const month = monthlyData[currentMonth];
    return (
      <div className="dashboard-page">
        <nav className="dashboard-navbar">{brand}<div className="dashboard-user">Hi, {user?.name}</div><div className="dashboard-nav-links"><button className="nav-link-button" onClick={() => setPage("dashboard")}>Dashboard</button>{predictionResult && <button className="nav-link-button" onClick={() => setPage("risk")}>Risk</button>}<button className="nav-link-button" onClick={() => setPage("monthlyForm")}>Update Symptoms</button><button className="logout-btn" onClick={handleLogout}>Logout</button></div></nav>
        <div className="monthly-container">
          <div className="monthly-header"><span className="section-label">MONTHLY HEALTH TRACKING</span><h1>Month {currentMonth + 1}</h1><p>Enter your menstrual and symptom information for this month.</p></div>
          {message && <div className="error-message">{message}</div>}
          <div className="progress-section">
            <div className="progress-text"><span>Month {currentMonth + 1} of {MONTH_COUNT}</span><span>{currentMonth === 4 ? "Final Month" : "Continue tracking"}</span></div>
            <div className="progress-bar"><div style={{ width: `${((currentMonth + 1) / MONTH_COUNT) * 100}%` }} /></div>
            <div className="month-indicators">{[1, 2, 3, 4, 5].map((number) => <div key={number} className={number <= currentMonth + 1 ? "month-dot active" : "month-dot"}>{number}</div>)}</div>
          </div>

          <form className="monthly-card" onSubmit={currentMonth === 4 ? analyzeRisk : handleNextMonth}>
            <div className="card-heading"><div className="month-badge">{currentMonth + 1}</div><div><h2>Month {currentMonth + 1} Details</h2><p>Record your symptoms for this month.</p></div></div>
            <div className="form-grid">
              <div className="input-group"><label>Menstrual Pain Level<input type="number" min="0" max="10" step="1" value={month.menstrualPainLevel} onChange={(e) => updateMonth("menstrualPainLevel", e.target.value)} placeholder="0 - 10" required /></label><small>0 = No pain, 10 = Severe pain</small></div>
              <div className="input-group"><label>Pain Duration (days)<input type="number" min="1" max="31" step="1" value={month.painDuration} onChange={(e) => updateMonth("painDuration", e.target.value)} placeholder="Example: 4" required /></label></div>
              <div className="input-group"><label>Heavy Menstrual Bleeding<select value={month.heavyMenstrualBleeding} onChange={(e) => updateMonth("heavyMenstrualBleeding", e.target.value)} required><option value="">Select</option><option value="1">Yes</option><option value="0">No</option></select></label></div>
              <div className="input-group"><label>Menstrual Irregularity<select value={month.menstrualIrregularity} onChange={(e) => updateMonth("menstrualIrregularity", e.target.value)} required><option value="">Select</option><option value="1">Yes</option><option value="0">No</option></select></label></div>
              <div className="input-group"><label>Pelvic Pain Level<input type="number" min="0" max="10" step="1" value={month.pelvicPainLevel} onChange={(e) => updateMonth("pelvicPainLevel", e.target.value)} placeholder="0 - 10" required /></label><small>0 = No pain, 10 = Severe pain</small></div>
              <div className="input-group"><label>Infertility<select value={month.infertility} onChange={(e) => updateMonth("infertility", e.target.value)} required><option value="">Select</option><option value="1">Yes</option><option value="0">No</option></select></label></div>
            </div>
            <div className="form-actions">
              {currentMonth > 0 && <button type="button" className="back-button" onClick={handlePreviousMonth}>← Previous</button>}
              <button type="submit" className="auth-button next-button" disabled={loading}>{loading ? "Analyzing..." : currentMonth === 4 ? "Analyze My Risk →" : "Save & Continue →"}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }


  if (page === "risk") {
    const monthlyResults = Array.isArray(predictionResult?.monthly_results)
      ? predictionResult.monthly_results
      : [];

    const higherVotes = Number(predictionResult?.positive_votes ?? 0);
    const lowerVotes = Number(predictionResult?.negative_votes ?? 0);
    const averageRisk = Number(predictionResult?.average_risk ?? 0);
    const finalPrediction = predictionResult?.final_prediction || "Assessment Pending";
    const isHigh = finalPrediction === "Higher Risk";

    return (
      <div className="dashboard-page">
        <nav className="dashboard-navbar">
          {brand}
          <div className="dashboard-user">Hi, {user?.name}</div>
          <div className="dashboard-nav-links">
            <button className="nav-link-button" onClick={() => setPage("dashboard")}>Dashboard</button>
            <button className="nav-link-button" onClick={() => setPage("monthlyForm")}>Update Symptoms</button>
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </div>
        </nav>

        <div className="risk-page-container">
          <div className="risk-page-header">
            
            <h1>Risk Assessment</h1>
            
          </div>

          <div className={`final-risk-banner ${isHigh ? "high" : "low"}`}>
            <span>FINAL PREDICTION</span>
            <strong>{finalPrediction}</strong>
          </div>

          <div className="risk-stats-grid">
            <div className="risk-stat-card">
              <span>HIGHER-RISK VOTES</span>
              <strong>{higherVotes} / 5</strong>
            </div>
            <div className="risk-stat-card">
              <span>LOWER-RISK VOTES</span>
              <strong>{lowerVotes} / 5</strong>
            </div>
            <div className="risk-stat-card">
              <span>AVERAGE 5-MONTH RISK</span>
              <strong>{averageRisk.toFixed(2)}%</strong>
            </div>
            
          </div>

          <div className="prediction-card">
            <div className="table-heading">
              <div>
                <h2>Monthly Model Predictions</h2>
              
              </div>
            </div>

            <div className="result-grid">
              {monthlyResults.map((item) => {
                const high = item.prediction === "Higher Risk";
                return (
                  <div className="result-card" key={item.month}>
                    <h3>Month {item.month}</h3>
                    <div className="risk-number">
                      {Number(item.risk_percentage).toFixed(2)}%
                    </div>
                    <div className={`risk-label ${high ? "high" : "low"}`}>
                      {item.prediction}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="risk-actions">
            <button className="back-button" onClick={() => setPage("dashboard")}>
              ← Back to Dashboard
            </button>
            <button className="auth-button risk-action-button" onClick={() => setPage("monthlyForm")}>
              Update Symptoms →
            </button>
          </div>

          <p className="disclaimer">
            This is an ML-based early risk screening result and not a medical diagnosis.
            Please consult a qualified healthcare professional for medical evaluation.
          </p>
        </div>
      </div>
    );
  }

  if (page === "dashboard") {
    const monthlyResults = Array.isArray(predictionResult?.monthly_results) ? predictionResult.monthly_results : [];
    const higherVotes = Number(predictionResult?.positive_votes || 0);
    const lowerVotes = Number(predictionResult?.negative_votes || 0);
    const averageRisk = Number(predictionResult?.average_risk || 0);

    return (
      <div className="dashboard-page">
        <nav className="dashboard-navbar">{brand}<div className="dashboard-user">Hi, {user?.name}</div><div className="dashboard-nav-links"><button className="nav-link-button" onClick={() => setPage("dashboard")}>Dashboard</button>{predictionResult && <button className="nav-link-button" onClick={() => setPage("risk")}>Risk</button>}<button className="nav-link-button" onClick={() => setPage("monthlyForm")}>Update Symptoms</button><button className="logout-btn" onClick={handleLogout}>Logout</button></div></nav>
        <div className="dashboard-container">
          <div className="dashboard-welcome"><div><h1>Welcome back, {user?.name}</h1></div><div className="dashboard-actions"><button className="edit-data-button" onClick={() => setPage("risk")} disabled={!predictionResult}>View Risk Assessment</button><button className="new-assessment-button" onClick={startNewAssessment}>New Assessment</button></div></div>

          {message && <div className="error-message">{message}</div>}

          <div className="dashboard-summary">
            <div className="summary-card"><span>MONTHS TRACKED</span><strong>5</strong><p>Monthly records</p></div>
            <div className="summary-card"><span>ML STATUS</span><strong>{predictionResult ? "COMPLETE" : "READY"}</strong><p>LSTM risk analysis</p></div>
          </div>

          <div className="personal-summary-card">
            <div className="table-heading"><h2>Personal Information</h2></div>
            <div className="personal-summary-grid">
              <div><span>Age</span><strong>{personalData.age}</strong></div>
              <div><span>Height</span><strong>{personalData.height} cm</strong></div>
              <div><span>Weight</span><strong>{personalData.weight} kg</strong></div>
              <div><span>Calculated BMI</span><strong>{predictionResult ? Number(predictionResult.bmi).toFixed(1) : bmiPreview ? bmiPreview.toFixed(1) : "—"}</strong></div>
            </div>
          </div>

          <div className="data-table-card">
            <div className="table-heading"><div><h2>Monthly Health Records</h2><p>Your information recorded over five months.</p></div></div>
            <div className="table-wrapper">
              <table><thead><tr><th>Month</th><th>Menstrual Pain</th><th>Pain Duration</th><th>Heavy Bleeding</th><th>Irregularity</th><th>Pelvic Pain</th><th>Infertility</th></tr></thead>
                <tbody>{monthlyData.map((data, index) => <tr key={index}><td>Month {index + 1}</td><td>{data.menstrualPainLevel || "—"}</td><td>{data.painDuration ? `${data.painDuration} days` : "—"}</td><td>{data.heavyMenstrualBleeding === "1" ? "Yes" : data.heavyMenstrualBleeding === "0" ? "No" : "—"}</td><td>{data.menstrualIrregularity === "1" ? "Yes" : data.menstrualIrregularity === "0" ? "No" : "—"}</td><td>{data.pelvicPainLevel || "—"}</td><td>{data.infertility === "1" ? "Yes" : data.infertility === "0" ? "No" : "—"}</td></tr>)}</tbody>
              </table>
            </div>
          </div>

          {predictionResult ? (
            <div className="prediction-card">
              <h2>Your 5-Month Risk Results</h2>
              <div className="result-grid">
                {monthlyResults.map((item) => <div className="result-card" key={item.month}><h3>Month {item.month}</h3><div className="risk-number">{Number(item.risk_percentage).toFixed(2)}%</div><div className={item.prediction === "Higher Risk" ? "risk-label high" : "risk-label low"}>{item.prediction}</div></div>)}
              </div>
              <div className="final-result-box">
                <h3>Final Result — Majority Vote</h3>
                <div className="final-stats"><div><span>Higher-Risk Votes</span><strong>{higherVotes} / 5</strong></div><div><span>Lower-Risk Votes</span><strong>{lowerVotes} / 5</strong></div><div><span>Average 5-Month Risk</span><strong>{averageRisk.toFixed(2)}%</strong></div></div>
                <div className={predictionResult.final_prediction === "Higher Risk" ? "final-prediction high" : "final-prediction low"}><span>FINAL PREDICTION</span><strong>{predictionResult.final_prediction}</strong></div>
              </div>
              <p className="disclaimer">This is an ML-based risk screening result and is not a medical diagnosis. Please consult a qualified healthcare professional for medical evaluation.</p>
            </div>
          ) : (
            <div className="prediction-card"><span className="section-label">ML RISK ASSESSMENT</span><h2>Ready for Risk Analysis</h2><p>Your five-month data is saved. Complete all five months to send the sequence to the trained LSTM model.</p><div className="prediction-status">ML MODEL<strong>LSTM READY</strong></div></div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

export default App;
