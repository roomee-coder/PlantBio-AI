// ---- Backend API base URL ----
// Change this if your FastAPI server runs on a different host/port.
const API_BASE = "http://127.0.0.1:8000";

// ---- Tiny Markdown renderer for AI responses (bold, headings, lists, rules) ----
function escapeHtml(str){
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function inlineMarkdown(text){
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/__(.+?)__/g, '<strong>$1</strong>');
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  return text;
}

function renderMarkdown(raw){
  const lines = escapeHtml(raw).split('\n');
  let html = '';
  let inList = false;
  let listType = null;

  const closeList = () => {
    if(inList){ html += listType === 'ol' ? '</ol>' : '</ul>'; inList = false; listType = null; }
  };

  lines.forEach(line => {
    const trimmed = line.trim();
    let m;

    if(trimmed === ''){ closeList(); return; }
    if(/^-{3,}$/.test(trimmed)){ closeList(); html += '<hr>'; return; }
    if((m = trimmed.match(/^####\s+(.*)/))){ closeList(); html += `<h5>${inlineMarkdown(m[1])}</h5>`; return; }
    if((m = trimmed.match(/^###\s+(.*)/))){ closeList(); html += `<h4>${inlineMarkdown(m[1])}</h4>`; return; }
    if((m = trimmed.match(/^##\s+(.*)/))){ closeList(); html += `<h3>${inlineMarkdown(m[1])}</h3>`; return; }
    if((m = trimmed.match(/^#\s+(.*)/))){ closeList(); html += `<h2>${inlineMarkdown(m[1])}</h2>`; return; }
    if((m = trimmed.match(/^[*-]\s+(.*)/))){
      if(!inList || listType !== 'ul'){ closeList(); html += '<ul>'; inList = true; listType = 'ul'; }
      html += `<li>${inlineMarkdown(m[1])}</li>`;
      return;
    }
    if((m = trimmed.match(/^\d+\.\s+(.*)/))){
      if(!inList || listType !== 'ol'){ closeList(); html += '<ol>'; inList = true; listType = 'ol'; }
      html += `<li>${inlineMarkdown(m[1])}</li>`;
      return;
    }
    closeList();
    html += `<p>${inlineMarkdown(trimmed)}</p>`;
  });
  closeList();
  return html;
}

// ---- Medium / PGR stock-solution calculator ----
function calculate(){
  const stock = Number(document.getElementById('stock').value);
  const req = Number(document.getElementById('req').value);
  const vol = Number(document.getElementById('volume').value);
  const resultEl = document.getElementById('calcResult');

  if(!stock || stock <= 0 || req < 0 || vol < 0){
    resultEl.textContent = "Enter valid values.";
    return;
  }
  const ml = (req * vol) / (stock * 1000);
  resultEl.textContent = `Required stock volume: ${ml.toFixed(2)} mL`;
}

// ---- Real culture image analysis via the backend/Gemini vision model ----
let selectedImageFile = null; // tracks the currently chosen file for analysis

async function demoAnalysis(){
  const resultEl = document.getElementById('imageResult');
  if(!resultEl) return;

  if(!selectedImageFile){
    resultEl.textContent = "Choose an image first, then click Run analysis.";
    return;
  }

  resultEl.textContent = "Analyzing…";

  const formData = new FormData();
  formData.append('file', selectedImageFile);

  try {
    const res = await fetch(`${API_BASE}/analyze-image`, {
      method: 'POST',
      body: formData
    });

    if(!res.ok){
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server responded with ${res.status}`);
    }

    const data = await res.json();
    resultEl.innerHTML = `<b>AI analysis</b>${renderMarkdown(data.analysis)}`;
  } catch (err) {
    resultEl.textContent = `Could not analyze image — is the backend running and is GEMINI_API_KEY set? (${err.message})`;
  }
}

// ---- Preview an uploaded image in the upload box, and remember it for analysis ----
function handleImageUpload(event){
  const file = event.target.files[0];
  const uploadBox = document.getElementById('uploadBox');
  if(!file || !uploadBox) return;

  selectedImageFile = file;

  const reader = new FileReader();
  reader.onload = e => {
    uploadBox.innerHTML = `<img src="${e.target.result}" alt="Uploaded culture image" style="max-width:100%;border-radius:10px">`;
  };
  reader.readAsDataURL(file);
}

// ---- Clicking a sample prompt fills the question box; the real AI does the rest ----
function fillSampleQuestion(text){
  const box = document.getElementById('aiQuestion');
  if(!box) return;
  // strip the surrounding quotation marks from the sample prompt text
  box.value = text.replace(/^"|"$/g, '');
  askRealAI();
}

// ---- Ask the real backend-connected AI assistant ----
async function askRealAI(){
  const box = document.getElementById('aiQuestion');
  const answerBox = document.getElementById('aiAnswerBox');
  if(!box || !answerBox) return;

  const question = box.value.trim();
  if(!question){
    answerBox.innerHTML = `<strong>AI analysis</strong><p style="margin:8px 0 0">Type a question first.</p>`;
    return;
  }

  answerBox.innerHTML = `<strong>AI analysis</strong><p style="margin:8px 0 0">Thinking…</p>`;

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    if(!res.ok){
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server responded with ${res.status}`);
    }

    const data = await res.json();
    answerBox.innerHTML = `<strong>AI analysis</strong>${renderMarkdown(data.answer)}`;
  } catch (err) {
    answerBox.innerHTML = `
      <strong>AI analysis</strong>
      <p style="margin:8px 0 0">Could not reach the AI assistant — is the backend running and is GEMINI_API_KEY set? (${err.message})</p>
    `;
  }
}

// Wire up the sample prompts once the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const prompts = document.querySelectorAll('.prompt[data-sample]');
  prompts.forEach(el => {
    el.addEventListener('click', () => fillSampleQuestion(el.textContent));
  });

  const fileInput = document.getElementById('fileInput');
  if(fileInput){
    fileInput.addEventListener('change', handleImageUpload);
  }

  const recordForm = document.getElementById('recordForm');
  if(recordForm){
    recordForm.addEventListener('submit', handleRecordSubmit);
    loadRecords(); // populate the list on page load
  }

  const diseaseForm = document.getElementById('diseaseForm');
  if(diseaseForm){
    diseaseForm.addEventListener('submit', handleDiseaseSubmit);
    loadAllDiseases(); // populate the list on page load
  }

  if(document.getElementById('plantLibraryList')){
    loadPlantLibraryList(); // populate the saved-plants list on page load
  }
});

// ---- Research Lab: save a new culture record to the backend ----
async function handleRecordSubmit(event){
  event.preventDefault();
  const statusEl = document.getElementById('formStatus');

  const payload = {
    species: document.getElementById('f-species').value.trim(),
    explant_type: document.getElementById('f-explant').value.trim(),
    treatment: document.getElementById('f-treatment').value.trim() || null,
    shoots_per_explant: document.getElementById('f-shoots').value
      ? Number(document.getElementById('f-shoots').value) : null,
    contamination_status: document.getElementById('f-contamination').value || null,
    rooting_percent: document.getElementById('f-rooting').value
      ? Number(document.getElementById('f-rooting').value) : null,
    notes: document.getElementById('f-notes').value.trim() || null
  };

  statusEl.textContent = "Saving…";

  try {
    const res = await fetch(`${API_BASE}/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if(!res.ok) throw new Error(`Server responded with ${res.status}`);

    statusEl.textContent = "Saved!";
    event.target.reset();
    loadRecords(); // refresh the list to include the new record
  } catch (err) {
    statusEl.textContent = `Could not save record — is the backend running? (${err.message})`;
  }
}

// ---- Research Lab: fetch and render all saved records ----
async function loadRecords(){
  const listEl = document.getElementById('recordsList');
  if(!listEl) return;
  listEl.textContent = "Loading…";

  try {
    const res = await fetch(`${API_BASE}/records`);
    if(!res.ok) throw new Error(`Server responded with ${res.status}`);
    const records = await res.json();

    if(records.length === 0){
      listEl.textContent = "No records yet — add one on the left.";
      return;
    }

    listEl.innerHTML = records.map(r => `
      <div class="mini" style="margin-bottom:10px">
        <span>${r.species} — ${r.explant_type}</span>
        <b style="font-size:.95rem">
          ${r.treatment ? r.treatment + ' • ' : ''}
          ${r.shoots_per_explant != null ? r.shoots_per_explant + ' shoots • ' : ''}
          ${r.contamination_status ? r.contamination_status + ' contamination • ' : ''}
          ${r.rooting_percent != null ? r.rooting_percent + '% rooting' : ''}
        </b>
      </div>
    `).join('');
  } catch (err) {
    listEl.textContent = `Could not load records — is the backend running at ${API_BASE}? (${err.message})`;
  }
}

// ---- Plant Pathology: save a new disease record to the backend ----
async function handleDiseaseSubmit(event){
  event.preventDefault();
  const statusEl = document.getElementById('diseaseFormStatus');

  const payload = {
    name: document.getElementById('d-name').value.trim(),
    pathogen: document.getElementById('d-pathogen').value.trim() || null,
    pathogen_type: document.getElementById('d-pathogen-type').value || null,
    host_species: document.getElementById('d-host').value.trim() || null,
    symptoms: document.getElementById('d-symptoms').value.trim(),
    management: document.getElementById('d-management').value.trim() || null,
    notes: document.getElementById('d-notes').value.trim() || null
  };

  statusEl.textContent = "Saving…";

  try {
    const res = await fetch(`${API_BASE}/diseases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if(!res.ok) throw new Error(`Server responded with ${res.status}`);

    statusEl.textContent = "Saved!";
    event.target.reset();
    loadAllDiseases(); // refresh the list to include the new record
  } catch (err) {
    statusEl.textContent = `Could not save disease record — is the backend running? (${err.message})`;
  }
}

// ---- Plant Pathology: fetch and render disease records ----
function renderDiseases(diseases){
  const listEl = document.getElementById('diseasesList');
  if(!listEl) return;

  if(diseases.length === 0){
    listEl.textContent = "No matching records.";
    return;
  }

  listEl.innerHTML = diseases.map(d => `
    <div class="mini" style="margin-bottom:10px;text-align:left">
      <span>${d.name}${d.pathogen_type ? ' — ' + d.pathogen_type : ''}</span>
      <b style="font-size:.9rem;display:block;margin-top:4px">
        ${d.pathogen ? '<i>' + d.pathogen + '</i><br>' : ''}
        ${d.host_species ? 'Host: ' + d.host_species + '<br>' : ''}
        Symptoms: ${d.symptoms}
        ${d.management ? '<br>Management: ' + d.management : ''}
      </b>
    </div>
  `).join('');
}

async function loadAllDiseases(){
  const listEl = document.getElementById('diseasesList');
  if(!listEl) return;
  listEl.textContent = "Loading…";

  try {
    const res = await fetch(`${API_BASE}/diseases`);
    if(!res.ok) throw new Error(`Server responded with ${res.status}`);
    renderDiseases(await res.json());
  } catch (err) {
    listEl.textContent = `Could not load records — is the backend running at ${API_BASE}? (${err.message})`;
  }
}

async function searchDiseases(){
  const listEl = document.getElementById('diseasesList');
  const query = document.getElementById('symptomSearch').value.trim();
  if(!listEl) return;

  if(!query){
    loadAllDiseases();
    return;
  }

  listEl.textContent = "Searching…";

  try {
    const res = await fetch(`${API_BASE}/diseases?symptom=${encodeURIComponent(query)}`);
    if(!res.ok) throw new Error(`Server responded with ${res.status}`);
    renderDiseases(await res.json());
  } catch (err) {
    listEl.textContent = `Could not search records — is the backend running at ${API_BASE}? (${err.message})`;
  }
}


// ===========================================================================
// Pathology + AI integration
// ===========================================================================

// ---- Autofill the "New disease record" form using AI, from just a name ----
async function autofillDisease(){
  const nameInput = document.getElementById('d-name');
  const statusEl = document.getElementById('autofillStatus');
  const name = nameInput.value.trim();

  if(!name){
    statusEl.style.display = 'block';
    statusEl.textContent = "Enter a disease name first.";
    return;
  }

  statusEl.style.display = 'block';
  statusEl.textContent = "Asking AI for reference info…";

  try {
    const res = await fetch(`${API_BASE}/autofill-disease`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });

    if(!res.ok){
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server responded with ${res.status}`);
    }

    const data = await res.json();
    if(data.pathogen) document.getElementById('d-pathogen').value = data.pathogen;
    if(data.pathogen_type){
      const select = document.getElementById('d-pathogen-type');
      if([...select.options].some(o => o.value === data.pathogen_type)){
        select.value = data.pathogen_type;
      }
    }
    if(data.host_species) document.getElementById('d-host').value = data.host_species;
    if(data.symptoms) document.getElementById('d-symptoms').value = data.symptoms;
    if(data.management) document.getElementById('d-management').value = data.management;
    if(data.notes) document.getElementById('d-notes').value = data.notes;

    statusEl.textContent = "Filled in — review and edit before saving.";
  } catch (err) {
    statusEl.textContent = `Could not autofill — is the backend running and is GEMINI_API_KEY set? (${err.message})`;
  }
}

// ---- AI Diagnosis: symptoms → likely disease suggestions ----
async function runDiagnosis(){
  const resultEl = document.getElementById('diagnoseResult');
  const symptoms = document.getElementById('diagnoseSymptoms').value.trim();

  if(!symptoms){
    resultEl.innerHTML = `<strong>AI diagnosis</strong><p style="margin:8px 0 0">Describe the symptoms first.</p>`;
    return;
  }

  resultEl.innerHTML = `<strong>AI diagnosis</strong><p style="margin:8px 0 0">Analyzing…</p>`;

  try {
    const res = await fetch(`${API_BASE}/diagnose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptoms })
    });

    if(!res.ok){
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server responded with ${res.status}`);
    }

    const data = await res.json();
    let matchesHtml = '';
    if(data.matches && data.matches.length > 0){
      matchesHtml = `
        <hr style="border:none;border-top:1px solid var(--border);margin:14px 0">
        <b>Matched entries from your database</b>
        ${data.matches.map(m => `<div style="margin:6px 0;color:var(--muted)">— ${m.name}</div>`).join('')}
      `;
    }

    resultEl.innerHTML = `<strong>AI diagnosis</strong>${renderMarkdown(data.answer)}${matchesHtml}`;
  } catch (err) {
    resultEl.innerHTML = `
      <strong>AI diagnosis</strong>
      <p style="margin:8px 0 0">Could not run diagnosis — is the backend running and is GEMINI_API_KEY set? (${err.message})</p>
    `;
  }
}

// ===========================================================================
// Plant Library — AI-generated, database-cached species reference profiles
// ===========================================================================

const PLANT_PROFILE_CATEGORIES = [
  { key: 'taxonomy', label: 'Taxonomy & Classification' },
  { key: 'morphology', label: 'Morphology' },
  { key: 'anatomy', label: 'Anatomy' },
  { key: 'biochemistry', label: 'Biochemistry' },
  { key: 'molecular_biology', label: 'Molecular Biology' },
  { key: 'physiology', label: 'Physiology' },
  { key: 'economic_importance', label: 'Economic Importance' },
];

function renderPlantProfile(profile){
  const resultEl = document.getElementById('plantProfileResult');
  const sections = PLANT_PROFILE_CATEGORIES.map(cat => {
    const content = profile[cat.key];
    if(!content) return '';
    return `
      <div style="margin-bottom:18px">
        <h4 style="font-family:var(--font-display);color:var(--accent);margin-bottom:6px">${cat.label}</h4>
        ${renderMarkdown(content)}
      </div>
    `;
  }).join('');

  resultEl.innerHTML = `
    <h3 style="font-family:var(--font-display);margin-bottom:14px">${profile.name}</h3>
    ${sections}
  `;
}

async function searchPlantLibrary(){
  const resultEl = document.getElementById('plantProfileResult');
  const name = document.getElementById('plantSearchName').value.trim();

  if(!name){
    resultEl.textContent = "Enter a plant name first.";
    return;
  }

  resultEl.textContent = "Searching library / generating profile…";

  try {
    const res = await fetch(`${API_BASE}/plant-library/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });

    if(!res.ok){
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Server responded with ${res.status}`);
    }

    const profile = await res.json();
    renderPlantProfile(profile);
    loadPlantLibraryList(); // refresh the saved list in case this was a new entry
  } catch (err) {
    resultEl.textContent = `Could not search — is the backend running and is GEMINI_API_KEY set? (${err.message})`;
  }
}

async function loadPlantLibraryList(){
  const listEl = document.getElementById('plantLibraryList');
  if(!listEl) return;
  listEl.textContent = "Loading…";

  try {
    const res = await fetch(`${API_BASE}/plant-library`);
    if(!res.ok) throw new Error(`Server responded with ${res.status}`);
    const profiles = await res.json();

    if(profiles.length === 0){
      listEl.textContent = "No plants saved yet — search one above.";
      return;
    }

    listEl.innerHTML = profiles.map(p => `
      <button class="btn btn-outline" style="margin:4px 6px 4px 0" onclick="loadPlantById(${p.id})">${p.name}</button>
    `).join('');
  } catch (err) {
    listEl.textContent = `Could not load saved profiles — is the backend running? (${err.message})`;
  }
}

async function loadPlantById(id){
  const resultEl = document.getElementById('plantProfileResult');
  resultEl.textContent = "Loading…";

  try {
    const res = await fetch(`${API_BASE}/plant-library/${id}`);
    if(!res.ok) throw new Error(`Server responded with ${res.status}`);
    renderPlantProfile(await res.json());
    window.scrollTo({ top: document.getElementById('plantProfileResult').offsetTop - 100, behavior: 'smooth' });
  } catch (err) {
    resultEl.textContent = `Could not load profile — is the backend running? (${err.message})`;
  }
}