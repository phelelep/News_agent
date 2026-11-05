// Bouton « Générer les rumeurs » : lance le workflow GitHub qui appelle la routine.
// La clé de la routine reste dans les secrets du dépôt ; ce fichier n'en contient aucune.
(function () {
  const REPO = "phelelep/News_agent";
  const WORKFLOW = "rumeurs.yml";
  const STORAGE_KEY = "news-agent-github-token";

  const button = document.getElementById("rumor-button");
  if (!button) return;
  const status = document.getElementById("rumor-status");
  const forget = document.getElementById("rumor-forget");
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
    status.textContent = "Token oublié sur cet appareil.";
  }

  async function launch(token) {
    button.disabled = true;
    status.textContent = "Lancement en cours…";
    try {
      const response = await fetch(
        `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
        {
          method: "POST",
          headers: {
            Accept: "application/vnd.github+json",
            Authorization: `Bearer ${token}`,
            "X-GitHub-Api-Version": "2022-11-28",
          },
          body: JSON.stringify({ ref: "main" }),
        }
      );
      if (response.status === 204) {
        saveToken(token);
        forget.hidden = false;
        status.textContent = "C'est lancé. Les rumeurs arriveront sur le site d'ici quelques minutes.";
      } else if (response.status === 401) {
        clearToken();
        status.textContent = "Token refusé par GitHub. Vérifie-le puis réessaie.";
      } else if (response.status === 403 || response.status === 404) {
        status.textContent = "Ce token n'a pas le droit de lancer le workflow (Actions : Read and write).";
        forget.hidden = false;
      } else {
        status.textContent = `GitHub a répondu ${response.status}. Réessaie dans un moment.`;
      }
    } catch (error) {
      status.textContent = "GitHub est injoignable. Vérifie ta connexion.";
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", function () {
    const token = readToken();
    if (token) {
      launch(token);
    } else {
      input.value = "";
      dialog.showModal();
    }
  });

  document.getElementById("rumor-confirm").addEventListener("click", function () {
    const token = input.value.trim();
    if (!token) return;
    dialog.close();
    input.value = "";
    launch(token);
  });

  document.getElementById("rumor-cancel").addEventListener("click", function () {
    input.value = "";
    dialog.close();
  });

  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") document.getElementById("rumor-confirm").click();
  });

  forget.addEventListener("click", clearToken);
  forget.hidden = !readToken();
})();
