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

Um zum Source Code beitragen zu können, muss man zunächst einen Github Account anlegen, seinen public SSH key in github hinterlegen und das Repository in Github "Forken". Dadurch erhält man einen eigenen Arbeitsbereich bei Github, in dem man den Sourcecode munter anpassen und Änderungen später per "Pull Request" in das Haupt-Repository einfügen kann. Wahrscheinlich brauchst du dafür eine kleine Einführung in Git. Die folgende Anleitung setzt voraus, dass ein solcher Fork bereits angelegt wurde.

Zudem sollte die aktuelle Version von Python installiert sein (Version 3.12.4). Das in der Regel ebenfalls vorhandene Python 2.x.x kann man ignorieren und man sollte es auch nicht aus dem System verwenden. Download von Python von: [www.python.org](https://www.python.org/downloads/release/python-3124/).

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


Konfiguration anpassen: die Datei config.json-dist nach config.json kopieren und ggf. entsprechend der eigenen Wünsche anpassen.

Datenbank initialisieren (eine leere Datenbank anlegen)

```
  (venv) $ python3
  Python 3.7.5 (v3.7.5:5c02a39a0b, Oct 14 2019, 18:49:57)
  [Clang 6.0 (clang-600.0.57)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>> from webapp import create_app,db
  >>> app=create_app()
  >>> ctx=app.app_context()
  >>> ctx.push()
  >>> db.create_all()
  >>> ctx.pop()
  >>> exit()
```

Anschliessend kann der Development Server lokal gestartet werden

```
  (venv) $ python3 run.py
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

Hat man python aktualisiert oder funktioniert der Update der Requirements nicht, kann man das Verzeichnis venv löschen und die Installation wiederholen (aber ohne sein git Verzeichnis komplett zu löschen):

```
  $ cd vds-sternwarte
  $ python3 -m venv venv
  $ source venv/bin/activate
  (venv) $ pip3 install --upgrade pip
  (venv) $ pip3 install -r requirements.txt
```


## Änderungen einreichen (Pull Request, kurz: PR)

Hat man Änderungen gemacht, kann man diese mit folgenden Befehl auflisten

```
  (venv) $ git status
```


TODO

