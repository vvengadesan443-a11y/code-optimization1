const sourceCode = document.getElementById("sourceCode");
const optimizeBtn = document.getElementById("optimizeBtn");
const originalOutput = document.getElementById("originalOutput");
const optimizedOutput = document.getElementById("optimizedOutput");
const stepsList = document.getElementById("stepsList");
const message = document.getElementById("message");

document.getElementById("loadExample").addEventListener("click", () => {
  sourceCode.value = "t1 = a + b\nt2 = a + b\nt3 = t2 * 1\nt4 = 3 * 4\nresult = t3 + t4";
  message.textContent = "";
});
optimizeBtn.addEventListener("click", runOptimization);
document.getElementById("copyBtn").addEventListener("click", async () => {
  const text = optimizedOutput.textContent;
  try {
    await navigator.clipboard.writeText(text);
    document.getElementById("copyBtn").textContent = "Copied ✓";
    setTimeout(() => document.getElementById("copyBtn").textContent = "Copy output", 1400);
  } catch {
    message.textContent = "Clipboard permission is unavailable. Select and copy the output manually.";
  }
});

async function runOptimization() {
  message.textContent = "";
  const code = sourceCode.value;
  const techniques = [];
  if (document.getElementById("dag").checked) techniques.push("dag");
  if (document.getElementById("peephole").checked) techniques.push("peephole");
  if (!techniques.length) {
    message.textContent = "Select at least one optimization technique.";
    return;
  }
  optimizeBtn.disabled = true;
  optimizeBtn.innerHTML = "<span>…</span> Optimizing <span class='button-arrow'>↻</span>";
  try {
    const response = await fetch("/api/optimize", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({code, techniques})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Optimization request failed.");
    originalOutput.textContent = data.original || "(empty)";
    optimizedOutput.textContent = data.optimized || "(no output)";
    document.getElementById("inputLines").textContent = data.summary.input_lines;
    document.getElementById("outputLines").textContent = data.summary.output_lines;
    document.getElementById("stepCount").textContent = data.summary.optimizations;
    document.getElementById("resultTag").textContent = "OPTIMIZATION COMPLETE";
    renderSteps(data.steps || []);
    if (data.warnings && data.warnings.length) {
      message.textContent = data.warnings.join(" ");
    }
  } catch (error) {
    message.textContent = error.message + " Make sure the Flask backend is running.";
  } finally {
    optimizeBtn.disabled = false;
    optimizeBtn.innerHTML = "<span>✦</span> Optimize code <span class='button-arrow'>→</span>";
  }
}

function renderSteps(steps) {
  stepsList.replaceChildren();
  if (!steps.length) {
    const p = document.createElement("p");
    p.className = "empty-state";
    p.textContent = "No applicable optimization found for this input.";
    stepsList.appendChild(p);
    return;
  }
  steps.forEach((step, index) => {
    const card = document.createElement("article");
    card.className = "step";
    const top = document.createElement("div");
    top.className = "step-top";
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = step.technique;
    const number = document.createElement("span");
    number.style.cssText = "font:10px var(--mono);color:#7f8da6";
    number.textContent = `STEP ${String(index + 1).padStart(2, "0")}`;
    top.append(pill, number);
    const detail = document.createElement("p");
    detail.textContent = step.detail;
    const before = document.createElement("code");
    before.textContent = "Before: " + step.before;
    const after = document.createElement("code");
    after.textContent = "After:  " + step.after;
    card.append(top, detail, before, after);
    stepsList.appendChild(card);
  });
}
