#!/usr/bin/env python3
"""Génère le site statique dans web/_site à partir de reports/ et watchlist.md."""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SITE = WEB / "_site"
REPORTS = ROOT / "reports"

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
]
def asset_version():
    """Empreinte des fichiers du site : l'URL change quand ils changent, le cache du navigateur est contourné."""
    digest = hashlib.sha1()
    for file in sorted((WEB / "assets").glob("*")):
        digest.update(file.read_bytes())
    return digest.hexdigest()[:10]


ASSET_VERSION = asset_version()
REPORT_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RUMOR_NAME = re.compile(r"^rumeurs_(\d{4})(\d{2})(\d{2})$", re.I)
CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src https://api.github.com; base-uri 'none'; form-action 'none'"
)


def fr_date(iso):
    year, month, day = iso.split("-")
    return f"{int(day)} {MONTHS_FR[int(month) - 1]} {year}"


def plain(text):
    """Retire la syntaxe Markdown d'un extrait."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[*_`]", "", text).strip()


def excerpt(text, limit):
    text = plain(text)
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-") + "…"


def safe_url(match):
    """Les contenus viennent du web : seuls http(s) et les liens relatifs passent."""
    attribute, url = match.group(1), match.group(2)
    decoded = re.sub(r"[\x00-\x20]", "", html.unescape(url)).lower()
    scheme = re.match(r"^([a-z][a-z0-9+.\-]*):", decoded)
    if scheme and scheme.group(1) not in ("http", "https"):
        return f'{attribute}="#"'
    return match.group(0)


def change_cell(match):
    """Colore une variation en pourcentage ; la flèche évite de dépendre de la seule couleur."""
    attributes, value = match.group(1), match.group(2)
    number = float(value.replace("−", "-").replace(",", "."))
    if number == 0:
        return match.group(0)
    css, arrow = ("up", "▲") if number > 0 else ("down", "▼")
    return f'<td{attributes} class="{css}">{arrow} {value} %</td>'


def render(source):
    converter = markdown.Markdown(extensions=["tables", "sane_lists"])
    # Le HTML brut des fichiers Markdown est affiché comme du texte, jamais interprété.
    converter.preprocessors.deregister("html_block")
    converter.inlinePatterns.deregister("html")
    body = converter.convert(source)
    body = re.sub(r'\b(href|src)="([^"]*)"', safe_url, body)
    body = re.sub(r'href="(?!https?:)([^"#]*)\.md(#[^"]*)?"', r'href="\1.html\2"', body)
    body = body.replace('<a href="http', '<a rel="noopener noreferrer" href="http')
    body = re.sub(
        r" · Impact (\d+)/10</h3>",
        lambda m: f' <span class="impact{" impact-high" if int(m.group(1)) >= 7 else ""}">'
        f"{m.group(1)}/10</span></h3>",
        body,
    )
    body = re.sub(r"<td([^>]*)>\s*([+\-−]\d+(?:[.,]\d+)?)\s*%\s*</td>", change_cell, body)
    return body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )


ICONS = {
    "home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v10h13V10"/><path d="M10 20v-5.5h4V20"/>',
    "reports": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 16h6"/>',
    "agenda": '<rect x="3" y="5" width="18" height="16" rx="1.5"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "rumors": '<circle cx="12" cy="12" r="1.8"/><path d="M8.2 8.2a5.4 5.4 0 0 0 0 7.6M15.8 8.2a5.4 5.4 0 0 1 0 7.6M5.4 5.4a9.4 9.4 0 0 0 0 13.2M18.6 5.4a9.4 9.4 0 0 1 0 13.2"/>',
}


def page(title, body, prefix, active=""):
    links = [
        ("index.html", "Aujourd'hui", "home"),
        ("rapports.html", "Rapports", "reports"),
        ("agenda.html", "Agenda", "agenda"),
        ("rumeurs.html", "Rumeurs", "rumors"),
    ]
    nav = '<span class="spot" aria-hidden="true"></span>' + "".join(
        f'<a href="{prefix}{href}" title="{html.escape(label)}"{" aria-current=page" if key == active else ""}>'
        f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[key]}</svg>'
        f'<span class="sr">{html.escape(label)}</span></a>'
        for href, label, key in links
    )
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#000000">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/style.css?v={ASSET_VERSION}">
<script src="{prefix}assets/app.js?v={ASSET_VERSION}" defer></script>
<script src="{prefix}assets/nav.js?v={ASSET_VERSION}" defer></script>
</head>
<body>
<header class="site-header">
<div class="bar">
<a class="brand" href="{prefix}index.html">News Agent</a>
<nav aria-label="Navigation principale">{nav}</nav>
</div>
</header>
<main>
{body}
</main>
<footer class="site-footer">Veille générée automatiquement. Rumeurs non vérifiées, rien ici n'est un conseil en investissement.</footer>
</body>
</html>
"""


def write(path, content):
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def load_reports():
    reports = []
    for file in REPORTS.glob("*/*.md"):
        if REPORT_NAME.match(file.stem):
            source = file.read_text(encoding="utf-8")
            reports.append({"date": file.stem, "month": file.parent.name, "source": source})
    return sorted(reports, key=lambda r: r["date"], reverse=True)


def section(source, title):
    match = re.search(rf"^## {title}\s*$(.*?)(?=^## |^---\s*$|\Z)", source, re.M | re.S)
    return match.group(1).strip() if match else ""


def events(source):
    found = re.findall(r"^### (.+?) · Impact (\d+)/10\s*$", source, re.M)
    return sorted(((plain(t), int(n)) for t, n in found), key=lambda e: -e[1])


def upcoming(month, limit=6):
    agenda = REPORTS / month / "Agenda.md"
    if not agenda.exists():
        return []
    rows = []
    for line in agenda.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[4].startswith("à venir"):
            rows.append(cells)
    return rows[:limit]


def load_quotes():
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "cours.py"), "--json"],
            capture_output=True, encoding="utf-8", timeout=120, check=True,
        )
        return json.loads(result.stdout)["cours"]
    except (subprocess.SubprocessError, ValueError, KeyError) as error:
        print(f"Cours indisponibles : {error}", file=sys.stderr)
        return []


def quotes_block(quotes):
    if not quotes:
        return '<p class="muted">Cours indisponibles pour le moment.</p>'
    rows = ""
    for q in quotes:
        direction = "up" if q["variation"] > 0 else "down" if q["variation"] < 0 else ""
        arrow = {"up": "▲ ", "down": "▼ ", "": ""}[direction]
        price = f"{q['prix']:,.2f}".replace(",", " ").replace(".", ",")
        change = f"{q['variation']:+.2f}".replace(".", ",")
        rows += (
            f'<tr><th scope="row" title="{html.escape(q["nom"])}">{html.escape(q["ticker"])}</th>'
            f'<td>{price}</td><td class="{direction}">{arrow}{change} %</td></tr>'
        )
    latest = fr_date(max(q["date"] for q in quotes))
    return (
        '<div class="table-wrap"><table class="quotes"><thead><tr><th scope="col">Ticker</th>'
        '<th scope="col">USD</th><th scope="col">Var.</th></tr></thead>'
        f'<tbody>{rows}</tbody></table></div><p class="muted">Dernière clôture connue, au {latest}. '
        "Crypto : variation sur 24 h.</p>"
    )


def theme_form():
    return r"""<form class="theme-form" id="theme-form" autocomplete="off">
<label for="theme-input">Ajouter un thème à la watchlist</label>
<div class="theme-row">
<input id="theme-input" name="theme" type="text" required minlength="2" maxlength="100"
 placeholder="un mot ou une phrase" spellcheck="false">
<button type="submit" class="button">Add to watchlist</button>
</div>
<p id="theme-status" class="muted" role="status"></p>
<button type="button" id="rumor-forget" class="link-button" hidden>Oublier le token de cet appareil</button>
</form>"""


def token_dialog():
    return """<dialog id="rumor-dialog" aria-labelledby="rumor-dialog-title">
<h2 id="rumor-dialog-title">Token GitHub</h2>
<p>Colle ton token GitHub limité à ce dépôt. Il reste dans ce navigateur et sert uniquement à lancer les workflows.</p>
<label for="rumor-token">Token</label>
<input id="rumor-token" type="password" autocomplete="off" spellcheck="false">
<div class="dialog-actions">
<button type="button" id="rumor-cancel" class="link-button">Annuler</button>
<button type="button" id="rumor-confirm" class="button">Valider</button>
</div>
</dialog>"""


def watchlist_themes():
    text = (ROOT / "watchlist.md").read_text(encoding="utf-8")
    match = re.search(r"^## Thèmes suivis\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return ""
    words = re.findall(r"^- (.+)$", match.group(1), re.M)
    chips = "".join(f"<li>{html.escape(w)}</li>" for w in words)
    return f'<ul class="themes" aria-label="Thèmes suivis">{chips}</ul>' if chips else ""


def build_home(reports, quotes):
    latest = reports[0]
    brief = render(section(latest["source"], "En bref"))
    top = "".join(
        f'<li><span class="impact{" impact-high" if n >= 7 else ""}">{n}/10</span> {html.escape(t)}</li>'
        for t, n in events(latest["source"])[:5]
    )
    report_url = f'reports/{latest["month"]}/{latest["date"]}.html'
    calendar = "".join(
        f"<li><strong>{html.escape(excerpt(c[0], 34))}</strong> · {html.escape(plain(c[1]))}"
        f"<span>{html.escape(excerpt(c[2], 96))}</span></li>"
        for c in upcoming(latest["month"])
    )
    body = f"""<div class="home">
<section class="lead" aria-labelledby="lead-title">
<p class="kicker">Veille du {fr_date(latest["date"])}</p>
<h1 id="lead-title">En bref</h1>
<div class="brief">{brief}</div>
{f'<h2>Les faits du jour</h2><ul class="top-events">{top}</ul>' if top else ""}
<p><a class="button" href="{report_url}">Lire le rapport complet</a></p>
</section>
<aside class="side">
<section aria-labelledby="side-rumors"><h2 id="side-rumors">Rumeurs</h2><p><a href="rumeurs.html">Voir les rumeurs</a></p></section>
<section aria-labelledby="side-themes"><h2 id="side-themes">Thèmes</h2>{watchlist_themes()}{theme_form()}</section>
<section aria-labelledby="side-agenda"><h2 id="side-agenda">À venir</h2><ul class="calendar">{calendar}</ul><p><a href="agenda.html">Tout l'agenda</a></p></section>
<section aria-labelledby="side-quotes"><h2 id="side-quotes">Cours</h2>{quotes_block(quotes)}</section>
</aside>
</div>
{token_dialog()}"""
    write("index.html", page("News Agent", body, "", "home"))


def build_reports(reports):
    for index, report in enumerate(reports):
        newer = reports[index - 1] if index else None
        older = reports[index + 1] if index + 1 < len(reports) else None

        def link(other, label):
            if not other:
                return "<span></span>"
            return f'<a href="../{other["month"]}/{other["date"]}.html">{label}</a>'

        pager = f'<nav class="pager" aria-label="Rapports voisins">{link(older, "← Veille précédente")}{link(newer, "Veille suivante →")}</nav>'
        body = f'<article class="prose">{render(report["source"])}</article>{pager}'
        write(f'reports/{report["month"]}/{report["date"]}.html',
              page(f'Veille du {fr_date(report["date"])}', body, "../../", "reports"))

    groups = {}
    for report in reports:
        groups.setdefault(report["date"][:7], []).append(report)
    body = '<h1>Rapports</h1>'
    for key, items in groups.items():
        year, month = key.split("-")
        body += f'<section class="archive"><h2>{MONTHS_FR[int(month) - 1].capitalize()} {year}</h2><ul>'
        for report in items:
            brief = excerpt(section(report["source"], "En bref"), 150)
            body += (
                f'<li><a href="reports/{report["month"]}/{report["date"]}.html">{fr_date(report["date"])}</a>'
                f"<span>{html.escape(brief)}</span></li>"
            )
        body += "</ul></section>"
    write("rapports.html", page("Rapports", body, "", "reports"))


def build_agendas(reports):
    folders = {}
    for report in reports:
        folders.setdefault(report["month"], report["date"])
    for file in REPORTS.glob("*/Agenda.md"):
        folders.setdefault(file.parent.name, "9999")
    agendas = [m for m in sorted(folders, key=folders.get, reverse=True) if (REPORTS / m / "Agenda.md").exists()]

    for month in agendas:
        tabs = "".join(
            f'<a href="../{m}/Agenda.html"{" aria-current=page" if m == month else ""}>{m}</a>'
            for m in agendas
        )
        source = (REPORTS / month / "Agenda.md").read_text(encoding="utf-8")
        body = f'<nav class="tabs" aria-label="Mois">{tabs}</nav><article class="prose wide">{render(source)}</article>'
        write(f"reports/{month}/Agenda.html", page(f"Agenda {month}", body, "../../", "agenda"))

    current = reports[0]["month"]
    target = current if current in agendas else agendas[0]
    redirect = f'<p>Agenda du mois : <a href="reports/{target}/Agenda.html">{target}</a></p>'
    write("agenda.html", page("Agenda", redirect, "", "agenda").replace(
        "<title>", f'<meta http-equiv="refresh" content="0; url=reports/{target}/Agenda.html"><title>', 1))


def rumor_files():
    found = []
    for file in REPORTS.glob("*/*.md"):
        daily = RUMOR_NAME.match(file.stem)
        if daily:
            found.append(("-".join(daily.groups()), file))
        elif file.stem.lower() == "rumeurs":
            dates = [p.stem for p in file.parent.glob("*.md") if REPORT_NAME.match(p.stem)]
            found.append((max(dates, default="0000"), file))
    return sorted(found, key=lambda item: item[0], reverse=True)


LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
PROBA = re.compile(r"\((\d+(?:[.,]\d+)?)\s*%")
END = re.compile(r"résolution\s+([\d/\-]+)")
LEVEL = re.compile(r"niveau\s+([1-8])\s*/\s*8", re.I)
TEXT_END = re.compile(r"\s+\(\d+(?:[.,]\d+)?\s*%|\s+—\s+|\s+·\s+")
LEVEL_EMOJIS = {"🟡": 1, "🟢": 2, "🔵": 3, "🔴": 4, "🩷": 5, "🟣": 6, "🟪": 7, "⚫": 8}
LEVEL_NAMES = ["Jaune", "Vert", "Bleu", "Rouge", "Rose", "Violet", "Violet foncé", "Noir"]


def sources_html(links):
    items = "".join(
        f'<a rel="noopener noreferrer" href="{html.escape(url)}">{html.escape(plain(label))}</a>'
        for label, url in links
    )
    return f'<span class="sources">{items}</span>' if items else "—"


def parse_rumor(line):
    """Lecture tolérante d'une ligne de rumeur ; None si ce n'est pas une rumeur."""
    if not line.startswith("- "):
        return None
    body = line[2:]
    proba, end, level = PROBA.search(body), END.search(body), LEVEL.search(body)
    level_number = int(level.group(1)) if level else next(
        (n for emoji, n in LEVEL_EMOJIS.items() if emoji in body), 0
    )
    lowered = body.lower()
    links = LINK.findall(body)
    if "non confirmée" in lowered:
        confirmed = False
    elif "recoupée" in lowered:
        confirmed = True
    elif level_number:
        # Sans mention explicite : recoupée si un média autre que Polymarket est cité.
        confirmed = any("polymarket.com" not in url for _, url in links)
    else:
        confirmed = None
    if not (proba or level_number or confirmed is not None):
        return None
    return {
        "text": plain(TEXT_END.split(body)[0]),
        "proba": proba.group(1) if proba else "",
        "end": end.group(1) if end else "",
        "level": level_number,
        "confirmed": confirmed,
        "links": links,
    }


def rumor_row(rumor):
    level = rumor["level"]
    if level:
        name = LEVEL_NAMES[level - 1]
        badge = f'<span class="level lvl-{level}" title="Niveau {level}/8 : {name}">{level}</span>'
    else:
        badge = '<span class="level lvl-0" title="Niveau non renseigné">—</span>'
    if rumor["proba"]:
        value = float(rumor["proba"].replace(",", "."))
        shown = f'{rumor["proba"]} %'
        proba = f'<meter min="0" max="100" value="{value}">{shown}</meter> <strong>{shown}</strong>'
    else:
        proba = "—"
    status = {True: ("confirmed", "Recoupée"), False: ("unconfirmed", "Non confirmée")}.get(
        rumor["confirmed"], ("", "—")
    )
    status_html = f'<span class="badge {status[0]}">{status[1]}</span>' if status[0] else "—"
    return (
        f'<tr><td data-label="Rumeur" class="rumor-text"><div class="rumor-line">{badge}<span>{html.escape(rumor["text"])}</span></div></td>'
        f'<td data-label="Probabilité" class="proba">{proba}</td>'
        f'<td data-label="Résolution">{html.escape(rumor["end"] or "—")}</td>'
        f'<td data-label="Statut">{status_html}</td>'
        f'<td data-label="Sources">{sources_html(rumor["links"])}</td></tr>'
    )


def rumor_day(date, lines):
    rows, notes = "", ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        rumor = parse_rumor(line)
        if rumor:
            rows += rumor_row(rumor)
        else:
            notes += f"<li>{html.escape(plain(line[2:] if line.startswith('- ') else line))}</li>"
    table = (
        '<div class="table-wrap"><table class="rumors"><thead><tr>'
        '<th scope="col">Rumeur</th><th scope="col">Probabilité</th><th scope="col">Résolution</th>'
        f'<th scope="col">Statut</th><th scope="col">Sources</th></tr></thead><tbody>{rows}</tbody></table></div>'
        if rows else ""
    )
    count = rows.count("<tr>")
    badge = f'<span class="count">{count} rumeur{"s" if count > 1 else ""}</span>' if count else ""
    extra = f'<ul class="notes">{notes}</ul>' if notes else ""
    return f'<section class="rumor-day"><h2>{fr_date(date)} {badge}</h2>{table}{extra}</section>'


def build_rumors():
    blocks = ""
    for _, file in rumor_files():
        text = file.read_text(encoding="utf-8")
        for date, content in re.findall(r"^## (\d{4}-\d{2}-\d{2})\s*$(.*?)(?=^## |\Z)", text, re.M | re.S):
            blocks += rumor_day(date, content.splitlines())
    if not blocks:
        blocks = '<p class="muted">Aucune rumeur générée pour le moment.</p>'
    body = (
        '<h1>Rumeurs</h1><p class="muted">Mises à jour automatiquement. '
        "Les probabilités viennent de Polymarket : ce sont des avis de marché, pas des faits. "
        "Le chiffre coloré devant chaque rumeur est son niveau de 1 à 8, selon l'importance et la probabilité.</p>"
        + blocks
    )
    write("rumeurs.html", page("Rumeurs", body, "", "rumors"))


def main():
    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(WEB / "assets", SITE / "assets")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    reports = load_reports()
    if not reports:
        sys.exit("Aucun rapport trouvé dans reports/.")
    build_home(reports, load_quotes())
    build_reports(reports)
    build_agendas(reports)
    build_rumors()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"{len(reports)} rapports générés dans {SITE} ({stamp})")


if __name__ == "__main__":
    main()
