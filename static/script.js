document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".fade-in").forEach((el, i) => {
    el.style.animationDelay = `${i * 0.08}s`;
  });
});