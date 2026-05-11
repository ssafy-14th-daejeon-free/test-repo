(function () {
  const root = document.querySelector("[data-editor]");
  if (!root) return;

  const textarea = root.querySelector("#id_content");
  const preview = root.querySelector("[data-preview]");
  const wordCount = root.querySelector("[data-word-count]");
  const toolbar = root.querySelector(".toolbar");
  if (!textarea || !preview || !wordCount || !toolbar) return;

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderMarkdownLite(value) {
    const lines = escapeHtml(value).split("\n");
    let inList = false;
    const html = [];
    for (const line of lines) {
      if (line.startsWith("## ")) {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
        html.push(`<h2>${line.slice(3)}</h2>`);
      } else if (line.startsWith("# ")) {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
        html.push(`<h1>${line.slice(2)}</h1>`);
      } else if (line.startsWith("- ")) {
        if (!inList) {
          html.push("<ul>");
          inList = true;
        }
        html.push(`<li>${line.slice(2)}</li>`);
      } else if (line.trim() === "") {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
      } else {
        if (inList) {
          html.push("</ul>");
          inList = false;
        }
        html.push(`<p>${line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")}</p>`);
      }
    }
    if (inList) html.push("</ul>");
    return html.join("");
  }

  function refresh() {
    const text = textarea.value;
    preview.innerHTML = renderMarkdownLite(text) || "<p class=\"muted\">Preview will appear here.</p>";
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    wordCount.textContent = `${words} words`;
  }

  function insertAtCursor(prefix, suffix) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = textarea.value.slice(start, end);
    const before = textarea.value.slice(0, start);
    const after = textarea.value.slice(end);
    textarea.value = `${before}${prefix}${selected}${suffix}${after}`;
    textarea.focus();
    textarea.selectionStart = start + prefix.length;
    textarea.selectionEnd = start + prefix.length + selected.length;
    refresh();
  }

  toolbar.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.wrap) {
      insertAtCursor(button.dataset.wrap, button.dataset.wrap);
    } else if (button.dataset.md) {
      insertAtCursor(button.dataset.md, "");
    }
  });

  textarea.addEventListener("input", refresh);
  refresh();
})();
