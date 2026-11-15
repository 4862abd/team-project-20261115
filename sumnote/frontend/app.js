const API_BASE_URL = (window.SUMNOTE_API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/+$/, "");

const views = {
  upload: document.querySelector("#upload-view"),
  processing: document.querySelector("#processing-view"),
  error: document.querySelector("#error-view"),
  results: document.querySelector("#results-view"),
};
const uploadForm = document.querySelector("#upload-form");
const dropArea = document.querySelector("#drop-area");
const dropTitle = document.querySelector("#drop-title");
const fileInput = document.querySelector("#document-file");
const selectedFile = document.querySelector("#selected-file");
const validateUploadButton = document.querySelector("#validate-upload-button");
const uploadMessage = document.querySelector("#upload-message");
const uploadedCard = document.querySelector("#uploaded-card");
const uploadDocumentInfo = document.querySelector("#upload-document-info");
const uploadValidationNote = document.querySelector("#upload-validation-note");
const summarizeButton = document.querySelector("#summarize-button");
const processingFilename = document.querySelector("#processing-filename");
const cancelProcessingButton = document.querySelector("#cancel-processing-button");
const errorReason = document.querySelector("#error-reason");
const retryProcessingButton = document.querySelector("#retry-processing-button");
const returnHomeButton = document.querySelector("#return-home-button");
const resultTitle = document.querySelector("#result-title");
const documentMeta = document.querySelector("#document-meta");
const resultStatus = document.querySelector("#result-status");
const resultStatusMessage = document.querySelector("#result-status-message");
const verificationNote = document.querySelector("#verification-note");
const statKeypoints = document.querySelector("#stat-keypoints");
const statTopics = document.querySelector("#stat-topics");
const statReviews = document.querySelector("#stat-reviews");
const pageSectionLabel = document.querySelector("#page-section-label");
const pageCounter = document.querySelector("#page-counter");
const pageContent = document.querySelector("#page-content");
const previousPageButton = document.querySelector("#previous-page");
const nextPageButton = document.querySelector("#next-page");
const newUploadButton = document.querySelector("#new-upload-button");
const downloadPdfButton = document.querySelector("#download-pdf");
const downloadXlsxButton = document.querySelector("#download-xlsx");
const downloadMessage = document.querySelector("#download-message");

const SPREADSHEET_EXTENSIONS = new Set([".xlsx", ".xls", ".csv"]);
const PAGE_TEXT_LIMIT = 300;
let currentFile = null;
let uploadValidation = null;
let currentResult = null;
let currentTab = "summary";
let pages = [];
let pageIndex = 0;
let activeController = null;
let isValidatingUpload = false;

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "없음";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "없음";
  return String(value);
}

function splitText(value, limit = PAGE_TEXT_LIMIT) {
  const text = displayValue(value);
  if (text.length <= limit) return [text];

  const pieces = [];
  let remaining = text;
  while (remaining.length > limit) {
    let splitAt = remaining.lastIndexOf(" ", limit);
    if (splitAt < Math.floor(limit * 0.55)) splitAt = limit;
    pieces.push(remaining.slice(0, splitAt).trim());
    remaining = remaining.slice(splitAt).trim();
  }
  if (remaining) pieces.push(remaining);
  return pieces;
}

function showView(name) {
  document.body.dataset.screen = name;
  for (const [viewName, element] of Object.entries(views)) {
    element.hidden = viewName !== name;
  }
}

function setMessage(element, message, kind = "error") {
  element.textContent = message;
  element.dataset.kind = kind;
  element.hidden = !message;
}

async function readErrorMessage(response) {
  const payload = await response.json().catch(() => ({}));
  return payload.error?.message || payload.detail || `요청이 실패했습니다 (HTTP ${response.status}).`;
}

function clearUploadValidation() {
  uploadValidation = null;
  uploadedCard.hidden = true;
  summarizeButton.disabled = true;
  setMessage(uploadMessage, "");
}

function showSelectedFile(file) {
  if (isValidatingUpload) return;
  currentFile = file || null;
  clearUploadValidation();
  if (!file) {
    selectedFile.textContent = "";
    selectedFile.hidden = true;
    validateUploadButton.disabled = true;
    dropTitle.textContent = "파일을 끌어 놓거나 찾아보세요";
    return;
  }

  selectedFile.textContent = `${file.name} · ${formatBytes(file.size)}`;
  selectedFile.hidden = false;
  validateUploadButton.disabled = false;
  dropTitle.textContent = "선택한 문서를 확인해 주세요";
}

function renderUploadInfo(data) {
  const fields = [
    ["파일명", data.filename],
    ["문서 형식", `${data.format} (${data.extension})`],
    ["파일 크기", formatBytes(data.size_bytes)],
    ["형식 확인", "확장자 확인 완료"],
  ];
  uploadDocumentInfo.replaceChildren();
  for (const [label, value] of fields) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = displayValue(value);
    uploadDocumentInfo.append(term, description);
  }
  uploadValidationNote.textContent = "지원 확장자와 10MB 제한을 통과했습니다. 파일 읽기, PDF 페이지 수, Excel 시트 수는 요약 처리 단계에서 추가 확인합니다.";
  uploadedCard.hidden = false;
  summarizeButton.disabled = false;
}

async function validateUpload() {
  if (!currentFile || isValidatingUpload) return;
  const fileToValidate = currentFile;
  isValidatingUpload = true;
  clearUploadValidation();
  validateUploadButton.disabled = true;
  fileInput.disabled = true;
  validateUploadButton.textContent = "업로드 형식 확인 중…";
  setMessage(uploadMessage, "파일을 서버에 전달해 지원 형식과 크기를 확인하고 있습니다.", "info");

  try {
    const query = new URLSearchParams({ filename: fileToValidate.name });
    const response = await fetch(apiUrl(`/documents/validate?${query}`), {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: fileToValidate,
    });
    if (!response.ok) throw new Error(await readErrorMessage(response));

    const validation = await response.json();
    if (currentFile !== fileToValidate) return;
    uploadValidation = validation;
    renderUploadInfo(uploadValidation);
    setMessage(uploadMessage, "업로드와 형식 확인이 완료되었습니다. 문서 요약을 시작할 수 있습니다.", "success");
  } catch (error) {
    uploadValidation = null;
    uploadedCard.hidden = true;
    summarizeButton.disabled = true;
    setMessage(uploadMessage, error.message || "업로드를 확인하지 못했습니다. 서버 연결과 파일을 확인해 주세요.");
  } finally {
    isValidatingUpload = false;
    fileInput.disabled = false;
    validateUploadButton.disabled = !currentFile;
    validateUploadButton.textContent = "업로드 및 형식 확인";
  }
}

function addTextPages(target, { section, title, text, kicker = "요약" }) {
  const parts = splitText(text);
  parts.forEach((part, index) => {
    target.push({ section, title: index ? `${title} (계속)` : title, text: part, kicker });
  });
}

function evidenceEntries(result) {
  const entries = [];
  for (const point of result.summary?.key_points ?? []) {
    for (const evidence of point.evidence ?? []) entries.push({ title: point.title, evidence });
  }
  for (const fact of result.summary?.important_facts ?? []) {
    for (const evidence of fact.evidence ?? []) entries.push({ title: fact.label, evidence });
  }
  for (const item of result.verification?.items ?? []) {
    for (const evidence of item.evidence ?? []) entries.push({ title: `검토 항목: ${item.issue}`, evidence });
  }
  return entries;
}

function createPages(result, tab) {
  const output = [];
  const summary = result.summary ?? {};

  if (tab === "summary") {
    addTextPages(output, { section: "한 줄 요약", title: "한 줄 요약", text: summary.one_line_summary });
    addTextPages(output, { section: "문서 개요", title: "문서 개요", text: summary.overview });
    addTextPages(output, { section: "주제", title: "주제", text: summary.topics });
    addTextPages(output, { section: "키워드", title: "키워드", text: summary.keywords });

    const points = [...(summary.key_points ?? [])].sort((left, right) => {
      const rank = { 높음: 0, 중간: 1, 낮음: 2 };
      return (rank[left.importance] ?? 1) - (rank[right.importance] ?? 1);
    });
    for (const point of points) {
      addTextPages(output, {
        section: `${displayValue(point.level)} · 중요도 ${displayValue(point.importance)}`,
        title: point.title,
        text: point.content,
        kicker: "핵심 내용",
      });
    }
    for (const fact of summary.important_facts ?? []) {
      addTextPages(output, {
        section: `핵심 정보 · ${displayValue(fact.importance)}`,
        title: fact.label,
        text: fact.value,
        kicker: "인물·기관·날짜·수치·조건",
      });
    }
    addTextPages(output, { section: "결론 또는 핵심 메시지", title: "결론 또는 핵심 메시지", text: summary.conclusion });
  } else if (tab === "evidence") {
    const entries = evidenceEntries(result);
    if (!entries.length) {
      addTextPages(output, { section: "원문 근거", title: "원문 근거", text: "없음", kicker: "근거" });
    }
    for (const entry of entries) {
      const quoteParts = splitText(entry.evidence.quote || "없음", 280);
      quoteParts.forEach((quote, index) => {
        output.push({
          section: "원문 근거",
          title: `${displayValue(entry.title)}${index ? " (계속)" : ""}`,
          quote,
          location: displayValue(entry.evidence.location),
          kicker: "원문 발췌",
        });
      });
    }
  } else {
    const verification = result.verification ?? {};
    if (!verification.generated) {
      addTextPages(output, {
        section: "검증 상태",
        title: "검증 결과 없음",
        text: "요약은 생성되었지만 검증 결과가 생성되지 않았습니다. 원문과 요약을 직접 확인해 주세요.",
        kicker: "검토 항목",
      });
    } else if (!(verification.items ?? []).length) {
      addTextPages(output, { section: "검토 항목", title: "검토 항목", text: "없음", kicker: "검토 결과" });
    } else {
      for (const item of verification.items) {
        const issueParts = splitText(`${displayValue(item.issue)}\n검토 이유: ${displayValue(item.reason)}`, 140);
        const evidences = item.evidence?.length ? item.evidence : [{ quote: "없음", location: "없음" }];
        const firstEvidence = evidences[0];
        const quoteParts = splitText(firstEvidence.quote, 140);
        const count = Math.max(issueParts.length, quoteParts.length);
        for (let index = 0; index < count; index += 1) {
          const evidence = evidences[Math.min(index, evidences.length - 1)];
          output.push({
            section: `[${displayValue(item.importance)}] ${displayValue(item.category)}`,
            title: `${displayValue(item.category)} 검토 후보`,
            text: issueParts[index] ?? `${displayValue(item.issue)} (계속)`,
            quote: quoteParts[index] ?? displayValue(evidence.quote),
            location: displayValue(evidence.location),
            kicker: "사람이 확인할 검토 후보",
          });
        }
        for (const evidence of evidences.slice(1)) {
          for (const quote of splitText(evidence.quote, 140)) {
            output.push({
              section: `[${displayValue(item.importance)}] ${displayValue(item.category)}`,
              title: `${displayValue(item.category)} 검토 후보`,
              text: `검토 이유: ${displayValue(item.reason)}`,
              quote,
              location: displayValue(evidence.location),
              kicker: "사람이 확인할 검토 후보",
            });
          }
        }
      }
    }
  }

  return output.length ? output : [{ section: "결과", title: "없음", text: "없음", kicker: "결과" }];
}

function renderCurrentPage() {
  const page = pages[pageIndex];
  if (!page) return;
  pageSectionLabel.textContent = page.section;
  pageCounter.textContent = `${pageIndex + 1} / ${pages.length}`;
  pageContent.replaceChildren();

  const kicker = document.createElement("p");
  kicker.className = "page-kicker";
  kicker.textContent = page.kicker;
  const title = document.createElement("h2");
  title.className = "page-title";
  title.textContent = page.title;
  pageContent.append(kicker, title);

  if (page.text) {
    const body = document.createElement("p");
    body.className = "page-text";
    body.textContent = page.text;
    pageContent.append(body);
  }
  if (page.quote) {
    const quote = document.createElement("blockquote");
    quote.className = "evidence-quote";
    quote.textContent = page.quote;
    const location = document.createElement("p");
    location.className = "evidence-location";
    location.textContent = `원문 위치: ${page.location || "없음"}`;
    pageContent.append(quote, location);
  }

  previousPageButton.disabled = pageIndex === 0;
  nextPageButton.disabled = pageIndex >= pages.length - 1;
}

function setTab(tab) {
  currentTab = tab;
  pageIndex = 0;
  pages = createPages(currentResult, currentTab);
  document.querySelectorAll(".tab-button").forEach((button) => {
    const active = button.dataset.tab === currentTab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  renderCurrentPage();
}

function displayResult(result) {
  currentResult = result;
  const documentInfo = result.document ?? {};
  resultTitle.textContent = result.summary?.title || documentInfo.filename || "문서 결과";

  const metadata = [
    documentInfo.filename || "없음",
    `${documentInfo.format || "없음"} ${documentInfo.extension || ""}`.trim(),
    formatBytes(Number(documentInfo.size_bytes ?? 0)),
  ];
  if (documentInfo.page_count !== null && documentInfo.page_count !== undefined) metadata.push(`${documentInfo.page_count}페이지`);
  if (documentInfo.sheet_count !== null && documentInfo.sheet_count !== undefined) metadata.push(`${documentInfo.sheet_count}개 시트`);
  documentMeta.textContent = metadata.join(" · ");

  const statusLabels = {
    completed: "완료",
    needs_review: "일부 근거 확인 필요",
    failed: "실패",
    no_result: "결과 없음",
  };
  resultStatus.textContent = statusLabels[result.status] || "결과 확인 필요";
  resultStatus.dataset.status = result.status || "needs_review";
  resultStatusMessage.textContent = result.status_message || "없음";
  verificationNote.hidden = Boolean(result.verification?.generated);
  statKeypoints.textContent = String(result.summary?.key_points?.length ?? 0);
  statTopics.textContent = String((result.summary?.topics?.length ?? 0) + (result.summary?.keywords?.length ?? 0));
  statReviews.textContent = result.verification?.generated ? String(result.verification?.items?.length ?? 0) : "미생성";

  const extension = (documentInfo.extension || "").toLowerCase();
  downloadXlsxButton.hidden = !SPREADSHEET_EXTENSIONS.has(extension);
  showView("results");
  setTab("summary");
}

function showProcessingError(message) {
  errorReason.textContent = message || "문서 처리에 실패했습니다. 파일과 설정을 확인해 주세요.";
  retryProcessingButton.hidden = !currentFile;
  showView("error");
}

async function processDocument() {
  if (!currentFile || !uploadValidation) return;
  showView("processing");
  processingFilename.textContent = `${currentFile.name} · ${formatBytes(currentFile.size)}`;
  activeController = new AbortController();

  try {
    const query = new URLSearchParams({ filename: currentFile.name });
    const response = await fetch(apiUrl(`/documents/process?${query}`), {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: currentFile,
      signal: activeController.signal,
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new Error(payload?.error?.message || payload?.detail || `처리 요청이 실패했습니다 (HTTP ${response.status}).`);
    if (!payload?.document || !payload?.status) throw new Error("서버에서 결과 형식을 확인할 수 없습니다.");
    if (["failed", "no_result"].includes(payload.status)) {
      showProcessingError(payload.status_message);
      return;
    }
    displayResult(payload);
  } catch (error) {
    if (error.name === "AbortError") {
      showProcessingError("요약 요청을 취소했습니다. 첫 화면에서 다른 문서를 선택하거나 다시 시작할 수 있습니다.");
    } else {
      showProcessingError(error.message || "서버에 연결할 수 없습니다. 백엔드 서버와 API 설정을 확인해 주세요.");
    }
  } finally {
    activeController = null;
  }
}

function filenameForDownload(extension) {
  const originalName = currentResult?.document?.filename || currentFile?.name || "sumnote_result";
  const stem = originalName.replace(/\.[^.]+$/, "") || "sumnote_result";
  return `${stem}_summary${extension}`;
}

async function downloadResult(kind) {
  if (!currentResult) return;
  const isPdf = kind === "pdf";
  const extension = isPdf ? ".pdf" : ".xlsx";
  const endpoint = isPdf ? "/documents/download/pdf" : "/documents/download/xlsx";
  const button = isPdf ? downloadPdfButton : downloadXlsxButton;
  button.disabled = true;
  downloadMessage.hidden = true;

  try {
    const response = await fetch(apiUrl(endpoint), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentResult),
    });
    if (!response.ok) throw new Error(await readErrorMessage(response));
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filenameForDownload(extension);
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    downloadMessage.textContent = `${filenameForDownload(extension)} 다운로드를 시작했습니다.`;
    downloadMessage.dataset.kind = "success";
  } catch (error) {
    downloadMessage.textContent = `${error.message} 원인을 확인한 뒤 다시 다운로드할 수 있습니다.`;
    downloadMessage.dataset.kind = "error";
  } finally {
    downloadMessage.hidden = false;
    button.disabled = false;
  }
}

function returnHome() {
  activeController?.abort();
  currentFile = null;
  uploadValidation = null;
  currentResult = null;
  fileInput.value = "";
  selectedFile.textContent = "";
  selectedFile.hidden = true;
  validateUploadButton.disabled = true;
  summarizeButton.disabled = true;
  uploadedCard.hidden = true;
  downloadMessage.hidden = true;
  setMessage(uploadMessage, "");
  showView("upload");
}

fileInput.addEventListener("change", () => showSelectedFile(fileInput.files?.[0] ?? null));

for (const eventName of ["dragenter", "dragover"]) {
  dropArea.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropArea.classList.add("is-dragging");
  });
}
for (const eventName of ["dragleave", "drop"]) {
  dropArea.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropArea.classList.remove("is-dragging");
  });
}
dropArea.addEventListener("drop", (event) => {
  if (isValidatingUpload) return;
  const file = event.dataTransfer?.files?.[0];
  if (file) showSelectedFile(file);
});

uploadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  validateUpload();
});
summarizeButton.addEventListener("click", processDocument);
cancelProcessingButton.addEventListener("click", () => activeController?.abort());
retryProcessingButton.addEventListener("click", processDocument);
returnHomeButton.addEventListener("click", returnHome);
newUploadButton.addEventListener("click", returnHome);
document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => setTab(button.dataset.tab));
});
previousPageButton.addEventListener("click", () => {
  if (pageIndex > 0) {
    pageIndex -= 1;
    renderCurrentPage();
  }
});
nextPageButton.addEventListener("click", () => {
  if (pageIndex < pages.length - 1) {
    pageIndex += 1;
    renderCurrentPage();
  }
});
downloadPdfButton.addEventListener("click", () => downloadResult("pdf"));
downloadXlsxButton.addEventListener("click", () => downloadResult("xlsx"));
