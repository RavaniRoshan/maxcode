(() => {
  const root = document.documentElement;
  const key = "maxcode-theme";
  const saved = localStorage.getItem(key);
  if (saved === "light" || saved === "dark") root.dataset.theme = saved;

  const toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    const current = () => root.dataset.theme ||
      (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    const paint = () => {
      const next = current() === "dark" ? "light" : "dark";
      toggle.textContent = next === "dark" ? "dark" : "light";
      toggle.setAttribute("aria-label", `Switch to ${next} theme`);
    };
    paint();
    toggle.addEventListener("click", () => {
      const next = current() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      localStorage.setItem(key, next);
      paint();
    });
  }

  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.querySelector(button.dataset.copy);
      if (!target) return;
      try {
        await navigator.clipboard.writeText(target.innerText.trim());
        const old = button.textContent;
        button.textContent = "copied";
        setTimeout(() => { button.textContent = old; }, 1400);
      } catch {
        button.textContent = "select";
      }
    });
  });
})();
