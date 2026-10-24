# Routing: Wie eine URL zum Code findet

Diese Anleitung erklärt, wie Flask in diesem Projekt eine URL einer Python-Funktion
zuordnet, wo der Code dafür liegt und wie neue Seiten und Endpunkte eingebaut werden.

## Überblick

```
Browser: GET /orders/42/positions
   │
   ▼
Flask URL-Tabelle (app.url_map)
   │  Regel "/orders/<int:order_id>/positions"  →  Endpunkt "orders.show_order_positions"
   ▼
Blueprint "orders"  →  View-Funktion show_order_positions(order_id=42)
   │                   in webapp/orders/routes/order_positions.py
   ▼
render_template("order_positions.html", ...)  →  HTML-Antwort
```

Die Bausteine:

| Begriff | Bedeutung | Im Projekt |
|---|---|---|
| **Route** | Regel aus URL-Muster und HTTP-Methoden | `@orders.route("/orders/<int:order_id>/positions")` |
| **View-Funktion** | Funktion, die die Anfrage bearbeitet und eine Antwort liefert | `show_order_positions(order_id)` |
| **Endpunkt** | eindeutiger Name einer Route: `<blueprint>.<funktionsname>` | `orders.show_order_positions` |
| **Blueprint** | Sammlung zusammengehöriger Routes und Templates | `orders`, `main`, `users`, … |

## Blueprints im Projekt

Die App wird in `create_app()` ([webapp/__init__.py](../webapp/__init__.py)) erzeugt. Dort
werden alle Blueprints registriert:

| Blueprint | Definiert in | Routes in | Inhalt |
|---|---|---|---|
| `main` | `webapp/main/__init__.py` | `webapp/main/routes/` (Paket) | Startseite, Poweruser-/Approver-Seiten, FAQ, … |
| `users` | `webapp/users/__init__.py` | `webapp/users/routes.py` | Login, Registrierung, Konto, Passwort |
| `posts` | `webapp/posts/__init__.py` | `webapp/posts/routes.py` | Beiträge |
| `orders` | `webapp/orders/__init__.py` | `webapp/orders/routes/` (Paket) | Beobachtungsanträge, Kalender |
| `inout` | `webapp/inout/__init__.py` | `webapp/inout/routes.py` | Import/Export |
| `errors` | `webapp/errors/__init__.py` | `webapp/errors/handlers.py` | Fehlerseiten (403, 404, 500) |

Ein Blueprint besteht immer aus drei Schritten:

```python
# 1. erzeugen: webapp/orders/__init__.py
orders = Blueprint('orders', __name__, template_folder='templates')

# 2. Routes anhängen: webapp/orders/routes/*.py
@orders.route("/orders/show_calendar")
def show_calendar(): ...

# 3. registrieren: webapp/__init__.py, in create_app()
from webapp.orders.routes import orders
app.register_blueprint(orders)
```

### Aufbau von `orders`: ein Modul pro Seite

Der Blueprint `orders` ist nach Seiten bzw. Templates aufgeteilt:

```
webapp/orders/
├── __init__.py               Blueprint-Objekt "orders"
├── routes/
│   ├── __init__.py           importiert alle Module → registriert ihre Routes
│   ├── api.py                JSON-Endpunkte für das Javascript
│   ├── order_list.py         orders.html
│   ├── create_order.py       create_order.html
│   ├── edit_order_pos.py     edit_order_pos.html
│   ├── order_positions.py    order_positions.html, iCalendar-Download
│   ├── approval.py           Approver-/Poweruser-Aktionen ohne eigene Seite
│   ├── reject_order.py       reject_order.html
│   ├── calendar.py           calendar.html, _calendar.html
│   ├── obs_request_complete.py  obs_request_complete.html
│   └── status_flow.py        status_flow.html
├── mails.py                  Celery-Tasks für Benachrichtigungs-Mails
├── orderservices.py          Geschäftslogik (Kopieren, Löschen, Kalender, …)
├── orderform.py              WTForms-Formulare
├── constants.py              Status- und Rollen-Konstanten
└── templates/                Templates des Blueprints
```

Jedes Modul listet im Header seine Routes auf, zum Beispiel
[order_list.py](../webapp/orders/routes/order_list.py):

```python
"""Order overview of the current user.

Routes::

    GET   /orders                              show_orders()   -> orders.html
    POST  /orders/<int:order_id>/copy_order    copy_order()    -> redirect to /orders
    POST  /orders/<int:order_id>/delete_order  delete_order()  -> redirect to /orders
"""
```

### Aufbau von `main`: ein Modul pro Seite

Der Blueprint `main` ist genauso aufgeteilt:

```
webapp/main/
├── __init__.py               Blueprint-Objekt "main"
├── routes/
│   ├── __init__.py           importiert alle Module → registriert ihre Routes
│   ├── home.py               home.html, home_intern.html; Debug-Route /status
│   ├── poweruser.py          poweruser.html, Rückmeldung der Poweruser (HTMX)
│   ├── poweruser_history.py  poweruser_history.html
│   ├── approver.py           approver.html (Aktionen in orders/routes/approval.py)
│   ├── order_history.py      orders_history.html
│   ├── gast.py               gast.html, Benutzer freischalten
│   ├── fg_request.py         create_obs_request.html, aufnahme_zeile.html (/add-row)
│   ├── service_request.py    create_service.html
│   ├── request_georg.py      create_request_georg.html
│   ├── faq.py                faq.html
│   ├── about.py              about.html
│   └── impressum.py          impressum.html
└── templates/                Templates des Blueprints
```

Es ist egal, auf wie viele Dateien die Routes verteilt sind. Alle hängen am selben
Blueprint-Objekt, die Endpunktnamen bleiben `orders.<funktionsname>`.

### Modul und Paket: alte und neue Variante

In Python ist ein **Modul** eine einzelne `.py`-Datei. Ein **Paket** ist ein Verzeichnis mit
einer `__init__.py`, das weitere Module enthält. Der Importpfad folgt dem Dateipfad:

| | Alte Variante | Neue Variante |
|---|---|---|
| Datei(en) | `webapp/orders/routes.py` | `webapp/orders/routes/__init__.py`, `…/order_list.py`, `…/calendar.py`, … |
| Art | ein Modul | ein Paket mit neun Modulen |
| Importpfad | `webapp.orders.routes` | `webapp.orders.routes` (das Paket) und `webapp.orders.routes.order_list`, … |
| Inhalt | alle 19 Routes und die 4 Mail-Tasks in einer Datei mit 1200 Zeilen | pro Seite ein Modul mit 60–400 Zeilen; die Mail-Tasks in `webapp/orders/mails.py` |

`import webapp.orders.routes` funktioniert in beiden Varianten. Bei einem Paket führt Python
dabei die `__init__.py` aus. Die neue `__init__.py` importiert alle Module und stellt das
Blueprint-Objekt `orders` bereit. Von außen sieht das Paket deshalb aus wie das alte Modul.

#### Auswirkungen im Code

**Unverändert bleiben:**

- `from webapp.orders.routes import orders` in `create_app()`
- alle URLs, HTTP-Methoden und Endpunktnamen (`orders.show_calendar`, …)
- alle `url_for()`-Aufrufe in Python und Templates

**Anders ist:**

1. **Jedes Modul hat einen eigenen Namensraum.** In der alten Datei war alles, was oben
   importiert wurde, in jeder Funktion verfügbar. Jetzt muss jedes Modul selbst importieren,
   was es braucht:
   ```python
   # webapp/orders/routes/order_positions.py
   from webapp.errors.handlers import error_404   # früher über "from webapp.errors.handlers import *"
   ```
   Fehlt ein Import, merkt man das erst, wenn die Funktion aufgerufen wird: `NameError` und
   Status 500. Nach einer Änderung deshalb jede betroffene Seite einmal aufrufen.

2. **Funktionen liegen unter einem neuen Importpfad.** Wer früher etwas direkt aus
   `routes.py` importiert hat, muss den Pfad anpassen:
   ```python
   # alt
   from webapp.orders.routes import send_approve_email
   # neu
   from webapp.orders.mails import send_approve_email
   ```
   Das gilt auch für View-Funktionen, z. B. in Tests:
   `from webapp.orders.routes.calendar import show_calendar`.

3. **Routes entstehen erst durch den Import.** Der Decorator `@orders.route` läuft, wenn
   Python das Modul lädt. In der alten Variante wurde die eine Datei immer geladen. Jetzt
   lädt die `__init__.py` jedes Modul ausdrücklich. Ein neues Modul, das dort fehlt, wird nie
   geladen, und seine URLs ergeben 404.

4. **Modulnamen werden zu Attributen des Pakets.** Nach `from webapp.orders.routes import calendar`
   ist `webapp.orders.routes.calendar` das Modul. Ein Modul namens `orders.py` würde deshalb
   das Blueprint-Objekt `webapp.orders.routes.orders` überschreiben, und
   `app.register_blueprint()` bekäme ein Modul statt eines Blueprints.

5. **Celery-Task-Namen hängen am Modulpfad.** `@shared_task` benennt einen Task nach Modul und
   Funktion. Ohne festen Namen hieße `send_approve_email` nach dem Umzug
   `webapp.orders.mails.send_approve_email`. Tasks, die beim Deployment noch in Redis warten,
   fände der neue Worker dann nicht mehr. Deshalb steht der alte Name fest im Code:
   ```python
   @shared_task(name="webapp.orders.routes.send_approve_email")
   def send_approve_email(order_id, approver_id, order_url, info): ...
   ```

6. **Hilfsfunktionen nicht zwischen Route-Modulen teilen.** In einer Datei konnte jede
   Funktion jede andere aufrufen. Braucht jetzt mehr als ein Modul dieselbe Logik, gehört sie
   nach `orderservices.py`. Gegenseitige Imports zwischen Route-Modulen führen schnell zu
   Zirkel-Importen.

7. **Fehlermeldungen und Logs nennen das genaue Modul**, z. B.
   `File "webapp/orders/routes/edit_order_pos.py", line 120`. Damit sieht man sofort, zu
   welcher Seite ein Fehler gehört.

8. **Git-Historie:** Für Git sind die neuen Dateien neu, `git log` auf einem Modul beginnt mit
   dem Refactoring. Die ursprüngliche Herkunft jeder Zeile zeigt
   `git blame -C -C webapp/orders/routes/<modul>.py`.

`routes.py` und das Verzeichnis `routes/` dürfen nicht nebeneinander existieren. Python würde
nur eines davon laden.

## So wird eine URL zugeordnet

### URL-Muster und Parameter

Variable Teile der URL stehen in spitzen Klammern. Ein Konverter wie `int` prüft und wandelt
den Wert um. Der Wert kommt als gleichnamiger Funktionsparameter an:

```python
@orders.route("/orders/<int:order_id>/positions", methods=["GET"])
@login_required
def show_order_positions(order_id):      # /orders/42/positions → order_id = 42 (int)
    ...
```

`/orders/abc/positions` passt nicht auf `<int:…>` und ergibt direkt einen 404.
Weitere Konverter sind `string` (Standard), `float`, `path` und `uuid`.

Parameter, die **nicht** im Pfad stehen, kommen als Query-String oder Formularfeld:

```python
# GET /orders/show_calendar?year=2026&month=10
year = request.args.get("year", default=datetime.now().year, type=int)

# POST mit Formular, z. B. <button name="action" value="save_order">
action = request.form.get("action")

# POST mit JSON-Body aus fetch()
data = request.get_json()
```

### HTTP-Methoden

Ohne `methods` akzeptiert eine Route nur `GET`. Eine URL darf für verschiedene Methoden
unterschiedliche Funktionen haben:

```python
@orders.route("/orders/user_preference", methods=["GET"])     # lesen
def get_user_preference(): ...

@orders.route("/orders/user_preference", methods=["POST"])    # speichern
def set_user_preference(): ...
```

Eine Funktion kann auch beide Methoden bedienen und unterscheidet dann selbst, wie
`edit_order_pos()` mit `if request.method == "GET": ...`.

### Endpunkte und `url_for()`

URLs werden **nie** von Hand zusammengesetzt, sondern über den Endpunktnamen erzeugt. So
bleiben Links gültig, wenn sich ein URL-Muster ändert.

In Python:

```python
return redirect(url_for("orders.edit_order_pos", order_id=order_head.id))
order_url = url_for("orders.show_order_positions", order_id=order_id, _external=True)  # absolute URL, z. B. für Mails
```

In Templates:

```html
<a href="{{ url_for('orders.show_order_positions', order_id=order.id) }}">Anzeigen</a>
<a href="{{ url_for('orders.download_reservation_ical', order_id=order.id) }}">Kalender (.ics)</a>
```

Der Endpunktname ist `<blueprint-name>.<funktionsname>`. **Eine View-Funktion umzubenennen
ändert also ihren Endpunkt**, und alle `url_for()`-Aufrufe darauf müssen angepasst werden.

### Zugriffsschutz mit Decorators

Die Decorators stehen in dieser Reihenfolge unter `@….route`:

```python
@orders.route("/orders/<int:order_id>/copy_order", methods=["POST"])
@login_required                 # nicht angemeldet → Umleitung zum Login
@role_required("user")          # Rolle fehlt → Umleitung zur Startseite (admin darf immer)
def copy_order(order_id):
    order = ObservationRequest.query.get_or_404(order_id)   # existiert nicht → 404
    if order.user_id != current_user.id:
        abort(403)                                          # fremder Antrag → 403
    ...
```

`@….route` muss **ganz oben** stehen. Flask registriert die Funktion, die es in diesem
Moment bekommt. Steht `@login_required` darüber, wird die ungeschützte Funktion registriert.

Rollen prüfen nur, *wer* etwas darf. Ob der Benutzer *diesen* Antrag bearbeiten darf
(Eigentümer, Status), muss die Funktion selbst prüfen.

## Antworttypen mit Beispielen

| Antwort | Beispiel | Code |
|---|---|---|
| HTML-Seite | `show_order_positions()` | `return render_template("order_positions.html", order=...)` |
| Umleitung nach Aktion | `copy_order()` | `flash(message, "success"); return redirect("/orders")` |
| HTML-Fragment (HTMX) | `approver_assign_poweruser()` | `return f'<span id="pu-assign-slot-{order_id}">…</span>'` |
| Partial je nach Anfrage | `show_calendar()` | `"_calendar.html" if request.headers.get("HX-Request") else "calendar.html"` |
| JSON | `get_filtersets()` | `return jsonify([{"id": f.id, "name": f.name} for f in filtersets])` |
| Datei-Download | `download_reservation_ical()` | `return Response(cal.to_ical(), mimetype="text/calendar", headers={...})` |
| Fehler | `delete_order()` | `abort(403)` → Fehlerseite aus `webapp/errors/` |

Nach einem erfolgreichen POST wird immer umgeleitet (Post/Redirect/Get). So schickt ein
Neuladen der Seite das Formular nicht ein zweites Mal ab.

## Code zu einer URL finden

1. **Alle Routes auflisten**, mit Endpunkt und Methoden:
   ```bash
   flask --app app.py routes
   ```
   Der Endpunkt nennt Blueprint und Funktion, z. B. `orders.show_calendar` →
   Funktion `show_calendar` im Blueprint `orders`.

2. **Funktion suchen:**
   ```bash
   grep -rn "def show_calendar" webapp/
   ```

3. Bei `orders` und `main` zeigt die **Header-Tabelle** jedes Moduls in `webapp/<blueprint>/routes/`, welche
   URLs dort bearbeitet werden.

Umgekehrt findet `grep -rn "orders.show_calendar" webapp/` alle Stellen, die auf eine Route
verlinken.

## Erweiterungen implementieren

### Neue Seite im Blueprint `orders`

Beispiel: eine Statistikseite unter `/orders/statistics`.

1. **Modul anlegen:** `webapp/orders/routes/statistics.py`
   ```python
   """Statistics of the observed objects.

   Routes::

       GET  /orders/statistics  show_statistics()  -> statistics.html
   """
   from flask import render_template
   from flask_login import login_required

   from webapp.orders import orders  # blueprint object
   from webapp.orders.orderservices import statistics_service
   from webapp.users.utils import role_required


   @orders.route("/orders/statistics", methods=["GET"])
   @login_required
   @role_required("user")
   def show_statistics():
       """Show how often each object was observed.

       :return: rendered ``statistics.html``.
       """
       stats = statistics_service()
       return render_template("statistics.html", title="Statistik", stats=stats)
   ```

2. **Modul registrieren** in [webapp/orders/routes/__init__.py](../webapp/orders/routes/__init__.py):
   ```python
   from webapp.orders.routes import (
       ...
       obs_request_complete,
       statistics,
   )
   ```
   Ohne diesen Import wird die Datei nie geladen, und die Route existiert nicht. Flask meldet
   dann nur 404, keinen Fehler.

3. **Template anlegen:** `webapp/orders/templates/statistics.html`, abgeleitet von
   `layout.html`:
   ```html
   {% extends "layout.html" %}
   {% block content %}
     ...
   {% endblock content %}
   ```

4. **Verlinken** mit `url_for('orders.show_statistics')`, z. B. in der Navigation in
   `webapp/templates/layout.html`.

5. **Prüfen:** `flask --app app.py routes | grep statistics`

### Neuer Endpunkt in einem bestehenden Modul

Gehört die Route zu einer bestehenden Seite, z. B. ein weiterer Button auf `orders.html`,
kommt sie in dasselbe Modul (hier `order_list.py`). Die Header-Tabelle bekommt eine Zeile
dazu.

### Neuer Blueprint

Für einen neuen, eigenständigen Bereich, z. B. `reports`:

1. `webapp/reports/__init__.py`:
   ```python
   from flask import Blueprint

   reports = Blueprint('reports', __name__, template_folder='templates')
   ```
2. `webapp/reports/routes.py` mit `@reports.route(...)`. Bei mehreren Seiten gleich als Paket
   `routes/` wie bei `orders`.
3. In `create_app()` in [webapp/__init__.py](../webapp/__init__.py) im `with app.app_context()`-Block:
   ```python
   from webapp.reports.routes import reports
   app.register_blueprint(reports)
   ```
   Optional mit `url_prefix="/reports"`. Dann schreibt man in den Routes nur noch den Rest
   der URL, z. B. `@reports.route("/monthly")` → `/reports/monthly`.

### Regeln

- **Ein Modul pro Seite bzw. Template.** Aktionen ohne eigene Seite kommen in das Modul der
  Seite, von der sie aufgerufen werden, oder werden nach Rolle gebündelt (wie `approval.py`).
- **Kein Modul darf so heißen wie der Blueprint** (z. B. `orders.py` in `orders/routes/`,
  `main.py` in `main/routes/`).
  Es würde das Blueprint-Objekt im Paket überdecken, und `register_blueprint()` schlägt fehl.
- **Routes schlank halten.** Datenbanklogik, die mehr als ein paar Zeilen hat oder an mehreren
  Stellen gebraucht wird, gehört nach `orderservices.py`. Route-Module importieren nicht
  voneinander, sonst drohen Zirkel-Importe.
- **Explizite Imports**, kein `from … import *`. Dann sieht man, was ein Modul benutzt.
- **Endpunktnamen sind öffentlich.** Funktionen nicht umbenennen, ohne alle `url_for()`-Aufrufe
  in Python und Templates mitzuändern.
- **Zugriff immer prüfen:** `@login_required`, passende `@role_required(...)` und in der
  Funktion Eigentümer und Status.
- **CSRF:** `CSRFProtect` ist aktiv, jeder POST braucht ein Token.
  - Formulare: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` oder
    `{{ form.hidden_tag() }}` bei WTForms.
  - HTMX-Anfragen bekommen das Token automatisch als Header `X-CSRFToken` (siehe
    `htmx:configRequest` in `layout.html`).
  - Bei `fetch()` den Header selbst setzen:
    `headers: {"X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content}`
- **Templates eindeutig benennen.** Flask legt die Template-Ordner aller Blueprints in einen
  gemeinsamen Namensraum. Zwei Blueprints mit je einer `index.html` stören sich gegenseitig:
  Es gewinnt die zuerst registrierte.
- **Langsame Arbeit in den Hintergrund.** Mails und andere langsame Aufgaben als Celery-Task
  (`@shared_task`) schreiben, z. B. in `mails.py`, und mit `.delay(...)` aufrufen. Nur IDs
  übergeben, keine Datenbankobjekte. Einen bestehenden Task nach dem Verschieben mit
  `@shared_task(name="<alter Name>")` unter seinem alten Namen behalten.
- **Dokumentieren:** Header-Tabelle im Modul aktualisieren und der Funktion einen
  Sphinx-Docstring geben (`:param:`, `:return:`, `:raises:`).
