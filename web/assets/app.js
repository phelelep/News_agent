// Boutons « Générer les rumeurs » et « Add to watchlist » : lancent le workflow GitHub qui appelle la routine.
// La clé de la routine reste dans les secrets du dépôt ; ce fichier n'en contient aucune.
(function () {
  const REPO = "phelelep/News_agent";
  const STORAGE_KEY = "news-agent-github-token";

  const button = document.getElementById("rumor-button");
  const status = document.getElementById("rumor-status");
  const forget = document.getElementById("rumor-forget") || { hidden: true };
  if (!document.getElementById("rumor-dialog")) return;
  const dialog = document.getElementById("rumor-dialog");
  const input = document.getElementById("rumor-token");

  function readToken() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "";
    } catch (error) {
      return "";
    }
  }

  function saveToken(token) {
    try {
      localStorage.setItem(STORAGE_KEY, token);
    } catch (error) {
      // Stockage bloqué : le token sert pour ce clic, il sera redemandé au prochain.
    }
  }

  function clearToken() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      // Rien à effacer.
    }
    forget.hidden = true;
    if (status) status.textContent = "Token oublié sur cet appareil.";
  }

  // Action en attente de token : { workflow, inputs, button, status }.
  let pending = null;

  async function launch(token, job) {
    job.button.disabled = true;
    job.status.textContent = "Lancement en cours…";
    try {
      const response = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${job.workflow}/dispatches`,
        {
          method: "POST",
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${token}`,
            "X-GitHub-Api-Version": "2022-11-28",
          },
          body: JSON.stringify({ ref: "main", inputs: job.inputs }),
        }
      );
      if (response.status === 204) {
        saveToken(token);
        forget.hidden = false;
        job.status.textContent = job.success;
        if (job.done) job.done();
      } else if (response.status === 401) {
        clearToken();
        job.status.textContent = "Token refusé par GitHub. Vérifie-le puis réessaie.";
      } else if (response.status === 403 || response.status === 404) {
        job.status.textContent = "Ce token n'a pas le droit de lancer le workflow (Actions : Read and write).";
        forget.hidden = false;
      } else {
        job.status.textContent = `GitHub a répondu ${response.status}. Réessaie dans un moment.`;
      }
    } catch (error) {
      job.status.textContent = "GitHub est injoignable. Vérifie ta connexion.";
    } finally {
      job.button.disabled = false;
    }
  }

  function run(job) {
    const token = readToken();
    if (token) {
      launch(token, job);
    } else {
      pending = job;
      input.value = "";
      dialog.showModal();
    }
  }

  if (button) {
    button.addEventListener("click", function () {
      run({
        workflow: "rumeurs.yml",
        inputs: {},
        button: button,
        status: status,
        success: "C'est lancé. Les rumeurs arriveront sur le site d'ici quelques minutes.",
      });
    });
  }

  const form = document.getElementById("theme-form");
  if (form) {
    const themeInput = document.getElementById("theme-input");
    const themeStatus = document.getElementById("theme-status");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const theme = themeInput.value.trim();
      if (!/^[\p{L}\p{N}_-]{2,40}$/u.test(theme)) {
        themeStatus.textContent = "Un seul mot, sans espace (lettres, chiffres, tiret).";
        return;
      }
      run({
        workflow: "watchlist.yml",
        inputs: { theme: theme },
        button: form.querySelector("button"),
        status: themeStatus,
        success: `« ${theme} » est en cours d'ajout. Le site sera à jour dans une minute ou deux.`,
        done: function () {
          themeInput.value = "";
        },
      });
    });
  }

  document.getElementById("rumor-confirm").addEventListener("click", function () {
    const token = input.value.trim();
    if (!token || !pending) return;
    const job = pending;
    pending = null;
    dialog.close();
    input.value = "";
    launch(token, job);
  });

  document.getElementById("rumor-cancel").addEventListener("click", function () {
    pending = null;
    input.value = "";
    dialog.close();
  });

  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") document.getElementById("rumor-confirm").click();
  });

  if (forget.addEventListener) forget.addEventListener("click", clearToken);
  forget.hidden = !readToken();
})();
