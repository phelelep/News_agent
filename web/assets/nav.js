// Menu « spotlight » : un faisceau glisse sous la barre et oscille vers l'icône choisie, qui s'allume.
// Les pages sont des fichiers séparés : la position du faisceau est mémorisée pour que le mouvement continue d'une page à l'autre.
(function () {
  const nav = document.querySelector(".site-header nav");
  if (!nav) return;
  const spot = nav.querySelector(".spot");
  const links = Array.from(nav.querySelectorAll("a"));
  if (!spot || !links.length) return;

  const KEY = "news-agent-nav-index";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const found = links.findIndex((link) => link.hasAttribute("aria-current"));
  const active = found === -1 ? 0 : found;
  let current = active;

  function targetX(index) {
    const link = links[index];
    return link.offsetLeft + link.offsetWidth / 2 - spot.offsetWidth / 2;
  }

  function currentX() {
    return spot.getBoundingClientRect().left + spot.offsetWidth / 2 - nav.getBoundingClientRect().left - spot.offsetWidth / 2;
  }

  function light(index) {
    links.forEach((link, i) => link.classList.toggle("lit", i === index));
  }

  function place(index) {
    spot.style.transform = `translateX(${targetX(index)}px)`;
    current = index;
    light(index);
  }

  function move(index) {
    if (index === current) return;
    const from = currentX();
    const to = targetX(index);
    current = index;
    links.forEach((link) => link.classList.remove("lit"));
    spot.style.transform = `translateX(${to}px)`;
    if (reduce || !spot.animate) {
      light(index);
      return;
    }
    const tilt = Math.max(-30, Math.min(30, (to - from) * 0.4));
    spot.animate(
      [
        { transform: `translateX(${from}px) rotate(0deg)`, offset: 0 },
        { transform: `translateX(${from + (to - from) * 0.6}px) rotate(${tilt}deg)`, offset: 0.45 },
        { transform: `translateX(${to}px) rotate(${-tilt * 0.4}deg)`, offset: 0.78 },
        { transform: `translateX(${to}px) rotate(0deg)`, offset: 1 },
      ],
      { duration: 800, easing: "cubic-bezier(.3,.7,.3,1)" }
    );
    window.setTimeout(function () {
      if (current === index) light(index);
    }, 480);
  }

  function remember() {
    try {
      sessionStorage.setItem(KEY, String(current));
    } catch (error) {
      // Stockage bloqué : le faisceau repartira simplement de l'icône active.
    }
  }

  function previous() {
    try {
      const value = sessionStorage.getItem(KEY);
      return value === null ? -1 : Number(value);
    } catch (error) {
      return -1;
    }
  }

  const from = previous();
  if (from >= 0 && from < links.length && from !== active) {
    place(from);
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        move(active);
      });
    });
  } else {
    place(active);
  }

  links.forEach(function (link, index) {
    link.addEventListener("mouseenter", function () { move(index); });
    link.addEventListener("focus", function () { move(index); });
    link.addEventListener("click", remember);
  });
  nav.addEventListener("mouseleave", function () { move(active); });
  nav.addEventListener("focusout", function (event) {
    if (!nav.contains(event.relatedTarget)) move(active);
  });
  window.addEventListener("pagehide", remember);
  window.addEventListener("resize", function () { place(current); });
})();
