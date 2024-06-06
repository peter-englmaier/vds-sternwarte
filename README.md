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


# Entwicklungsumgebung einrichten

## Anleitung für MacOS

Nachdem man dieses Repository 'geforked' hat, kann man seine Version in ein lokales Verzeichnis clonen (bitte `GITHUBUSER` durch euren github User ersetzen!):

```
  $ cd work
  $ git clone vds-sternwarte ppe$ git clone git@github.com:GITHUBUSER/vds-sternwarte.git
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
Alle `python3` und `pip3` müssen in diesem Environment ausgeführt werden. Falls ihr den Prompt nicht mehr seht, einfach erneut `cd vds-sternwarte` und `source venv/bin/activate` ausführen!


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

## Änderungen einreichen (Pull Request, kurz: PR)

TODO

