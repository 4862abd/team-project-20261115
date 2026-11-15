const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#document-file");
const selectedFile = document.querySelector("#selected-file");
const submitButton = document.querySelector("#submit-button");
const statusMessage = document.querySelector("#status-message");
const resultCard = document.querySelector("#result-card");
const resultDetails = document.querySelector("#result-details");

function formatBytes(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function showError(message) {
  statusMessage.textContent = message;
  statusMessage.dataset.kind = "error";
  statusMessage.hidden = false;
  resultCard.hidden = true;
}

function showResult(result) {
  const rows = [
    ["파일명", result.filename],
    ["확인 형식", `${result.format} (${result.extension})`],
    ["파일 크기", `${formatBytes(result.size_bytes)} / ${formatBytes(result.max_size_bytes)}`],
    ["확인 방식", "파일 확장자만 확인"],
    ["저장 여부", result.stored ? "저장됨" : "저장하지 않음"],
  ];

  resultDetails.replaceChildren();
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    resultDetails.append(term, description);
  }

  statusMessage.hidden = true;
  resultCard.hidden = false;
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  submitButton.disabled = !file;
  resultCard.hidden = true;
  statusMessage.hidden = true;

  if (file) {
    selectedFile.textContent = `${file.name} · ${formatBytes(file.size)}`;
    selectedFile.hidden = false;
  } else {
    selectedFile.textContent = "";
    selectedFile.hidden = true;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files?.[0];
  if (!file) {
    showError("먼저 확인할 파일을 선택해 주세요.");
    return;
  }

  submitButton.disabled = true;
  submitButton.textContent = "업로드 및 확인 중…";
  statusMessage.dataset.kind = "info";
  statusMessage.textContent = "파일 크기와 확장자를 확인하고 있습니다.";
  statusMessage.hidden = false;
  resultCard.hidden = true;

  try {
    const query = new URLSearchParams({ filename: file.name });
    const response = await fetch(`/api/documents/validate?${query}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: file,
    });
    const payload = await response.json();

    if (!response.ok) {
      const error = payload.error ?? payload.detail;
      showError(error?.message ?? "파일을 확인하지 못했습니다. 파일을 다시 선택해 주세요.");
      return;
    }

    showResult(payload);
  } catch {
    showError("서버에 연결할 수 없습니다. 서버 상태를 확인한 뒤 다시 시도해 주세요.");
  } finally {
    submitButton.disabled = !fileInput.files?.[0];
    submitButton.textContent = "업로드 및 형식 확인";
  }
});
