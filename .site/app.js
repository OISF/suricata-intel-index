const themeKey = "suricata-rule-index-theme";
const themeToggle = document.getElementById("themeToggle");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

syncThemeToggle();

themeToggle.addEventListener("click", () => {
  const nextTheme = currentTheme() === "dark" ? "light" : "dark";
  saveTheme(nextTheme);
  applyTheme(nextTheme);
});

systemTheme.addEventListener("change", () => {
  if (!savedTheme()) {
    applyTheme(systemTheme.matches ? "dark" : "light");
  }
});

function savedTheme() {
  try {
    return localStorage.getItem(themeKey);
  } catch {
    return null;
  }
}

function saveTheme(theme) {
  try {
    localStorage.setItem(themeKey, theme);
  } catch {
    // Keep the theme for this page when storage is unavailable.
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  syncThemeToggle();
}

function currentTheme() {
  return document.documentElement.dataset.theme ||
    (systemTheme.matches ? "dark" : "light");
}

function syncThemeToggle() {
  const nextTheme = currentTheme() === "dark" ? "light" : "dark";
  const label = `Switch to ${nextTheme} mode`;
  themeToggle.setAttribute("aria-label", label);
  themeToggle.title = label;
}
