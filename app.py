from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import io
import PyPDF2

app = Flask(__name__)
app.secret_key = "intelliprep_secret"
CORS(app)

# ------------------ UI ------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>IntelliPrep AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

body {
 font-family: 'Poppins', sans-serif;
 background: linear-gradient(135deg, #0f172a, #1e3a8a);
 color: white;
 text-align: center;
 padding: 20px;
}

/* Container Card */
.container {
 max-width: 850px;
 margin: auto;
 background: rgba(30, 41, 59, 0.95);
 padding: 30px;
 border-radius: 20px;
 box-shadow: 0 10px 40px rgba(0,0,0,0.6);
 backdrop-filter: blur(10px);
}

/* Titles */
.title {
 font-size: 42px;
 font-weight: 600;
 margin-bottom: 10px;
}

.subtitle {
 color: #94a3b8;
 margin-bottom: 25px;
 font-size: 16px;
}

h2 {
 color: #38bdf8;
 margin-bottom: 15px;
}

/* Buttons */
button {
 padding: 12px 24px;
 margin: 10px;
 border-radius: 12px;
 border: none;
 background: linear-gradient(135deg, #3b82f6, #06b6d4);
 color: white;
 font-weight: 500;
 cursor: pointer;
 transition: all 0.3s ease;
}

button:hover {
 transform: translateY(-2px) scale(1.05);
 box-shadow: 0 5px 15px rgba(59,130,246,0.4);
}

/* Textarea */
textarea {
 width: 95%;
 height: 110px;
 border-radius: 12px;
 padding: 12px;
 margin: 10px;
 border: none;
 outline: none;
 font-size: 14px;
 background: #0f172a;
 color: white;
 box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
}

/* Dropdown */
select {
 padding: 10px;
 border-radius: 10px;
 border: none;
 margin: 10px;
 background: #0f172a;
 color: white;
}

/* Navigation Tabs */
.nav {
 margin-bottom: 20px;
}

/* Divider */
hr {
 border: none;
 height: 1px;
 background: rgba(255,255,255,0.1);
 margin: 20px 0;
}

/* Result text */
.result, p {
 margin-top: 10px;
 font-size: 15px;
}
</style>
</head>

<body>

<!-- LANDING PAGE -->
<div id="landing" class="container">
  <h1 class="title">🚀 IntelliPrep AI</h1>
  <p class="subtitle">AI-powered Interview & Resume Intelligence</p>

  <button onclick="openTab('interview')">🎯 Interview Prep</button>
  <button onclick="openTab('resume')">📄 Resume Checker</button>
</div>


<!-- MAIN APP -->
<div id="mainApp" class="container" style="display:none;">

  <!-- NAV -->
  <div class="nav">
    <button onclick="switchTab('interview')">Interview</button>
    <button onclick="switchTab('resume')">Resume</button>
    <button onclick="goHome()">🏠 Home</button>
  </div>

  <!-- INTERVIEW TAB -->
  <div id="interviewTab">

    <h2>Interview Evaluation</h2>

    <select id="question">
      <option>Why should we hire you?</option>
      <option>Describe a challenge you faced</option>
      <option>Tell me about yourself</option>
      <option>What are your strengths and weaknesses?</option>
      <option>Describe a leadership experience</option>
      <option>Where do you see yourself in 5 years?</option>
      <option>Tell me about a failure and what you learned</option>
      <option>Why do you want to join this company?</option>
      <option>Explain a project you worked on</option>
      <option>How do you handle pressure or deadlines?</option>
      <option>What motivates you to work hard?</option>
</select>
    

    <textarea id="ans" placeholder="Type or speak your answer..."></textarea>

    <br>
    <button onclick="startVoice()">🎤 Speak</button>
    <button onclick="evalAns()">Evaluate</button>

    <p id="res"></p>

    <canvas id="chart"></canvas>

  </div>


  <!-- RESUME TAB -->
  <div id="resumeTab" style="display:none;">

    <h2>Resume Analyzer</h2>

    <textarea id="resume" placeholder="Paste resume text..."></textarea>

    <br>
    <button onclick="analyzeText()">Analyze Text</button>

    <br><br>

    <input type="file" id="pdfFile">
    <button onclick="uploadPDF()">Upload PDF</button>

    <p id="res2"></p>

  </div>

</div>


<script>

//// ---------------- NEW TAB LOGIC ---------------- ////

function openTab(tab){
  document.getElementById("landing").style.display = "none";
  document.getElementById("mainApp").style.display = "block";
  switchTab(tab);
}

function switchTab(tab){
  document.getElementById("interviewTab").style.display = "none";
  document.getElementById("resumeTab").style.display = "none";

  if(tab === "interview"){
    document.getElementById("interviewTab").style.display = "block";
  } else {
    document.getElementById("resumeTab").style.display = "block";
  }
}

function goHome(){
  document.getElementById("landing").style.display = "block";
  document.getElementById("mainApp").style.display = "none";
}

//// ---------------- EXISTING FUNCTIONS (UNCHANGED) ---------------- ////

// Voice
function startVoice(){
 const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
 recognition.start();
 recognition.onresult = function(event){
   document.getElementById("ans").value = event.results[0][0].transcript;
 }
}

// Chart
let scores = [];
let chart;

function updateChart(score){
 scores.push(score);
 if(chart) chart.destroy();

 chart = new Chart(document.getElementById('chart'), {
   type: 'line',
   data: {
     labels: scores.map((_,i)=>"Attempt "+(i+1)),
     datasets: [{ label: 'Score', data: scores }]
   }
 });
}

async function evalAns(){
 let ans = document.getElementById('ans').value;

 // ✅ Prevent empty input
 if(!ans.trim()){
   alert("Please enter an answer first");
   return;
 }

 // ✅ Show loading (important for demo)
 document.getElementById('res').innerHTML = "⏳ Evaluating...";

 try {
   let res = await fetch('/eval',{
     method:'POST',
     headers:{'Content-Type':'application/json'},
     body:JSON.stringify({answer:ans})
   });

   let data = await res.json();

   document.getElementById('res').innerHTML =
   "<b>Score:</b> "+data.score+"/10 <br><b>Feedback:</b> "+data.feedback;

   updateChart(data.score);

 } catch (error) {
   document.getElementById('res').innerHTML = "❌ Error evaluating answer";
 }
}

async function analyzeText(){
 let txt = document.getElementById('resume').value;

 // ✅ Prevent empty input
 if(!txt.trim()){
   alert("Please paste resume text");
   return;
 }

 // ✅ Show loading
 document.getElementById('res2').innerHTML = "⏳ Analyzing...";

 try {
   let res = await fetch('/resume_text',{
     method:'POST',
     headers:{'Content-Type':'application/json'},
     body:JSON.stringify({text:txt})
   });

   let data = await res.json();

   document.getElementById('res2').innerHTML =
   "<b>Detected:</b> "+data.found.join(", ")+
   "<br><b>Role:</b> "+data.role+
   "<br><b>Recommended:</b> "+data.recommendations;

 } catch (error) {
   document.getElementById('res2').innerHTML = "❌ Error analyzing resume";
 }
}

// Resume PDF
async function uploadPDF(){
 let file=document.getElementById('pdfFile').files[0];
 let fd=new FormData();
 fd.append("file",file);

 let res=await fetch('/resume_pdf',{
  method:'POST',
  body:fd
 });

 let data=await res.json();

 document.getElementById('res2').innerHTML =
 "<b>Detected:</b> "+data.found+
 "<br><b>Role:</b> "+data.role+
 "<br><b>Recommended:</b> "+data.recommendations;
}


</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

# ------------------ Evaluation ------------------
@app.route('/eval', methods=['POST'])
def eval():
    ans = request.json.get("answer","").lower()
    score = 0
    feedback = []

    keywords = ["team","project","challenge","solution"]
    score += sum(1 for k in keywords if k in ans) * 2

    if len(ans) > 80:
        score += 2
    else:
        feedback.append("Answer too short")

    if "example" in ans or "because" in ans:
        score += 2
    else:
        feedback.append("Add examples")

    if not feedback:
        feedback.append("Excellent answer")

    return jsonify({"score": min(score,10), "feedback": ", ".join(feedback)})

# ------------------ Resume Logic ------------------
def analyze_resume_text(text):
    text = text.lower()

    roles = {
        "backend developer": ["node","java","python","flask"],
        "frontend developer": ["react","html","css"],
        "data scientist": ["machine learning","pandas"],
        "cloud engineer": ["aws","azure","cloud"]
    }

    detected = []
    for skills in roles.values():
        for s in skills:
            if s in text:
                detected.append(s)

    role = "general"
    for r, skills in roles.items():
        if any(s in detected for s in skills):
            role = r
            break

    rec = {
        "backend developer": ["API design","database","docker"],
        "frontend developer": ["UI/UX","responsive design"],
        "data scientist": ["deep learning","nlp"],
        "cloud engineer": ["kubernetes","devops"]
    }

    return detected, role, rec.get(role, ["python","projects"])

# ------------------ Resume TEXT ------------------
@app.route('/resume_text', methods=['POST'])
def resume_text():
    text = request.json.get("text","")
    found, role, rec = analyze_resume_text(text)
    return jsonify({"found": found, "role": role, "recommendations": rec})

# ------------------ Resume PDF ------------------
@app.route('/resume_pdf', methods=['POST'])
def resume_pdf():
    file = request.files['file']
    reader = PyPDF2.PdfReader(io.BytesIO(file.read()))

    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()

    found, role, rec = analyze_resume_text(text)
    return jsonify({"found": found, "role": role, "recommendations": rec})

if __name__ == "__main__":
    app.run()
