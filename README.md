Vorschlag für eine Webapplikation für die VdS-Remotesternwarte(n).

Gewünschte Funktionen (noch nicht im Detail besprochen/beschlossen):

* Login mit üblichen Funktionen wie z.B. Password Reset
* Rollen für Antragsteller, Betreuer und Genehmiger
* Ablauf Steuerung (Antrag -> Genehmigt -> Betreuer zugeordnet -> Durchgeführt -> Dokumentiert)
* Kalender - freie Termine, Prioritäten, ggf. neuen Termin, Folgetermin, nächster freien Termin mit/ohne Randbedingung wie z.B. Mond, Zeitraum
* Email Erinnerungen
* Ankündigungen / Infos

Das konkrete [Pflichtenheft](docs/pflichtenheft.md) befindet sich noch im Aufbau.

Grundlage dieser Software ist das Schulungsmaterial von [Corey Schafer](https://github.com/CoreyMSchafer/code_snippets/tree/master/Python/Flask_Blog) zu seiner [YouTube Flask Tutorial](https://www.youtube.com/@coreyms/playlists).

Python kann man hier lernen:
* https://docs.python.org/3/tutorial/
* https://wiki.python.org/moin/BeginnersGuide/Programmers



# Entwicklungsumgebung einrichten

Zunächst sollte die aktuelle Version von Python installiert sein (Version 3.12.4). Das in der Regel ebenfalls vorhandene Python 2.x.x kann man ignorieren und man sollte es auch nicht aus dem System entfernen. Download von Python von: [www.python.org](https://www.python.org/downloads/release/python-3124/).

Um zum Source Code beitragen zu können, muss man zunächst einen Github Account anlegen, seinen public SSH key in github hinterlegen und das Repository in Github "Forken". Dadurch erhält man einen eigenen Arbeitsbereich bei Github, in dem man den Sourcecode munter anpassen und Änderungen später per "Pull Request" in das Haupt-Repository einfügen kann.

Hier ein paar Links dazu:
* [Gtihub Account anlegen](https://github.com/signup)
* [SSH Key anlegen, falls noch nicht vorhanden](https://docs.github.com/de/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
* [Public SSH key in github hinterlegen](https://docs.github.com/de/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
* [Fork erstellen](https://docs.github.com/de/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)

Wahrscheinlich brauchst du auch eine kleine Einführung in Git:
* [Tutorial](https://git-scm.com/docs/gittutorial)
* [Git Buch](https://git-scm.com/book/de/v2)

Die folgende Anleitung setzt voraus, dass du einen solchen Fork bereits angelegt hast.

## Anleitung für MacOS

Nachdem man dieses Repository 'geforked' hat, kann man seine Version in ein lokales Verzeichnis clonen (bitte `GITHUBUSER` durch euren github User ersetzen!):

```
  $ cd work
  $ python --version
  Python 2.7.15
  $ python3 --version
  Python 3.12.4
  $ git clone git@github.com:GITHUBUSER/vds-sternwarte.git
  $ cd vds-sternwarte
  $ python3 -m venv venv
  $ source venv/bin/activate
  (venv) $ pip3 install --upgrade pip
  (venv) $ pip3 install -r requirements.txt
```

Mit dem Befehl `source venv/bin/activate` begibt man sich in das Python Environment der Applikation. Man sieht das im Prompt (oder so ähnlich):

```bash
(venv) $
```

**WICHTIG:**
Alle `python3` und `pip3` müssen immer in diesem Environment ausgeführt werden. Falls ihr den Prompt nicht mehr seht, einfach erneut `cd vds-sternwarte` und `source venv/bin/activate` ausführen!

Dann weiter mit den folgenden Schritten [Datenbank initialisieren](#datenbank-initialisieren).

## Anleitung für Windows

Fork (Name Repository unverändert) erstellen wie s.o.

```
>git clone https://github.com/GITHUBUSER/vds-sternwarte.git
>cd vds-sternwarte
>python -m venv venv
(venv)...>venv\Scripts\activate
(venv)...>python.exe -m pip install --upgrade pip
(venv)...>pip install -r requirements.txt
(venv)...>pip list
```

Update pip nur wenn nötig (pip list zeigt eine entsprechende Meldung). Danach weiter in VSCode, die PowerShell zeigt allerdings kein "(venv)" im Prompt. Am besten mit pip list testen, dass das venv tatsächlich aktiviert ist. Dann weiter mit den folgenden Schritten [Datenbank initialisieren](#datenbank-initialisieren).

## Anleitung für Linux

Die Anleitung für Linux ist ähnlich der bereits o. g. Anleitung für MacOS.

Voraussetzung ist dabei, dass git, github und pyphon bereits installiert sind.

cd savefolder
mkdir workspace
cd workspace
git clone git@github.com:GITHUBUSER/vds-sternwarte.git
cd vds-sternwarte
# Neue Datei erstellen oder vorhandene bearbeiten ... danach muss diese Online gestellt werden
git add filename
git commit -m "Kommentar"
# Übergabe der eigenen bearbeiteten / erstellten Datei an ursprünglichen Ersteller
git push origin 

Dann weiter mit den folgenden Schritten [Datenbank initialisieren](#datenbank-initialisieren).

## Datenbank initialisieren

Konfiguration anpassen: die Datei config.json-dist nach config.json kopieren und ggf. entsprechend der eigenen Wünsche anpassen.

Datenbank initialisieren (eine leere Datenbank anlegen)

```
  (venv) $ python3 init-db.py
```

Anschliessend kann der Development Server lokal gestartet werden:

```
  (venv) $ python3 app.py
```

Der Server ist dann mit diesem Link erreichbar: http://localhost:5000/


## Update

Hat sich der Code geändert, muss man ihn mit git aktualisieren:

```
  (venv) $ git pull --ff-only
```

Eventuell muss man dann auch die requirements updaten
```
  (venv) $ pip install --upgrade -r requirements.txt
```

Auch die Datenbank muss u.U. dem neuen Code angepasst werden:

```
  (venv) $ flask db upgrade
```

Hat man python aktualisiert oder funktioniert der Update der Requirements nicht, kann man das Verzeichnis venv löschen und die Installation wiederholen (aber ohne sein git Verzeichnis komplett zu löschen):

```
  $ cd vds-sternwarte
  $ python3 -m venv venv
  $ source venv/bin/activate
  (venv) $ pip3 install --upgrade pip
  (venv) $ pip3 install -r requirements.txt
```

Ist die lokale Entwicklungs-Datenbank (Sqlite) kaputt, muss man sie löschen und neu initialisieren. In der Produktion sollte man das natürlich verhindern, indem man vorher Backups erstellt.

## Änderungen einreichen (Pull Request, kurz: PR)

Hat man seinen eigenen Github Fork erstellt und lokal einen clone (ausgecheckt), dann kann man Änderungen mit einem PR "einreichen". 

Hat man Änderungen gemacht, kann man diese mit folgenden Befehl auflisten

```
  (venv) $ git status
```

Es empfiehlt sich in einem eigenen "Branch" zu arbeiten, aber es ist kein Muss. Wer will kann mit der [git flow Erweiterung installieren](https://skoch.github.io/Git-Workflow/) und damit arbeiten. Die [Anleitung von Atlassian](https://www.atlassian.com/de/git/tutorials/comparing-workflows/gitflow-workflow) ist ganz gut.

Nachdem man lokal einen 'git commit' gemacht hat, kann man diesen in sein eigenes Repository mit 'git push' hochladen. Dann auf github.com einen 'Pull Request' (PR) einreichen. In der Regel werde ich eine Korrektur vorschlagen oder ihr habt selbst noch etwas "vergessen". Ihr könnt dann den Commit lokal noch ergänzen. Mit `git push --force-with-lease` könnt ihr diese Ergänzungen hochladen. Sie sind dann automatisch im Pull Request inkludiert.

Erklärungen zu diesem `--force-with-lease` findet man [hier](https://blog.adamspiers.org/2015/03/24/why-and-how-to-correctly-amend-github-pull-requests/).

## Flask Befehl

Flask wird mit einem Befehl ausgeliefert, der für die Fehlersuche nützlich ist. Es wird wie folgt verwendet:

```
$ flask routes
INFO: User admin already exists - reset password and email
Endpoint             Methods    Rule
-------------------  ---------  --------------------------
main.about           GET        /about
main.home            GET        /home
main.home            GET        /
posts.delete_post    POST       /post/<int:post_id>/delete
...
```

Man sieht eine Liste von URL's und den dafür zuständigen Methoden. Z.B. 'main.abort' ist im Modul `main` mit der Methode `about()` realisiert. 

Noch nützlicher ist die Shell Funktion:

```
$ flask shell
INFO: User admin already exists - reset password and email
Python 3.12.4 (v3.12.4:8e8a4baf65, Jun  6 2024, 17:33:18) [Clang 13.0.0 (clang-1300.0.29.30)] on darwin
App: webapp
Instance: /Users/ppe/work/vds-sternwarte/instance
>>> User.query.get(1)
User('admin', 'admin@example.org', 'default.jpg')
>>> 
```

## Datenbank Änderungen und Migrationen

Die Datenbank Struktur wird sich während der Entwicklung immer wieder verändern. Hat man z.B. im Code weitere Datenbank Element hinzugefügt (Spalten/Tabellen), dann muss man ein Migrationsskript erzeugen und mit der Änderung einchecken. Ausserdem muss man die lokale Datenbank auch anpassen, indem man dieses Skript ausführt. Das geht wie folgt:

Stand der Datenbank aktualiseren (zur Sicherheit)
```
$ flask db upgrade
```
Migrationsscript erzeugen:
```
$ flask db migrate -m "Sinnvolle/knappe Beschreibung"
```
Das erzegute Skript anwenden:
```
$ flask db upgrade
```

Weitere technische Informationen zur Migration findet man [in der Flask Migrate Dokumentation](https://flask-migrate.readthedocs.io/en/latest/index.html). Benötigt wird insbesondere `flask db migrate` um Änderunngen an der Struktur automatisiert zu erkennen.

Wichtig ist, dass nicht mehrere Anpassung gleichzeitig passieren, deshalb sollten alle Änderungen **vorher** mit Peter abgesprochen werden.
