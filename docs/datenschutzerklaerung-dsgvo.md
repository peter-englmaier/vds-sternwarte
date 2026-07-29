# Datenschutzerklärung für die Webanwendung „VdS Sternwarte“ (Entwurf)

Entwurf nach Codeprüfung, Stand: 29. Juli 2026  
Quellcodebasis: `peter-englmaier/vds-sternwarte`, Commit `9ee278e` vom 27. Juli 2026  

**Hinweis zur Verwendung:** Dieser Text ist ein technischer, am Quellcode ausgerichteter Entwurf für eine Datenschutzerklärung nach DSGVO. Er ersetzt keine anwaltliche Prüfung. Vor Veröffentlichung müssen insbesondere Verantwortlicher, Datenschutzkontakt, tatsächlicher Hosting-Anbieter, tatsächlicher Mailanbieter, Auftragsverarbeitungsverträge und Löschfristen ergänzt bzw. bestätigt werden.

## 1. Verantwortlicher

Verantwortlich für die Datenverarbeitung im Rahmen dieser Webanwendung ist:

**[Name des Verantwortlichen / Verein / Fachgruppe eintragen]**  
**[Anschrift eintragen]**  
**[E-Mail-Adresse eintragen]**  
**[Telefon, falls gewünscht, eintragen]**

Soweit die Webanwendung im Auftrag oder in organisatorischer Verantwortung der Vereinigung der Sternfreunde e. V. betrieben wird, ist dies hier eindeutig zu benennen. Die Anwendung verweist im Quellcode zusätzlich auf die allgemeine Datenschutzerklärung der Vereinigung der Sternfreunde e. V. unter:

https://sternfreunde.de/datenschutzerklaerung/

Diese Datenschutzerklärung beschreibt ergänzend die im Quellcode der Webanwendung erkennbaren Verarbeitungsvorgänge.

## 2. Datenschutzkontakt

Für Datenschutzfragen, Auskunftsersuchen, Berichtigung, Löschung oder sonstige Betroffenenrechte wenden Sie sich bitte an:

**[Datenschutzkontakt eintragen]**  
**[E-Mail-Adresse eintragen]**

Falls ein Datenschutzbeauftragter benannt ist:

**[Name und Kontaktdaten des Datenschutzbeauftragten eintragen]**

## 3. Zweck der Anwendung

Die Webanwendung „VdS Sternwarte“ dient der Verwaltung von Beobachtungsanträgen, Terminen, Reservierungen, Poweruser-Rückmeldungen, Genehmigungen, Ablehnungen, Benutzerkonten und administrativen Stammdaten für die Nutzung einer Remote-Sternwarte.

Dabei werden personenbezogene Daten verarbeitet, soweit dies für Registrierung, Anmeldung, Rollen- und Rechteverwaltung, Antragstellung, Terminabstimmung, Kommunikation, Administration, Fehleranalyse und Sicherheit erforderlich ist.

## 4. Zugriff auf die Website und Serverprotokolle

Beim Aufruf der Webanwendung verarbeitet der Server technisch notwendige Zugriffsdaten. Dazu können insbesondere gehören:

- IP-Adresse oder über Proxy weitergeleitete IP-Adresse,
- Datum und Uhrzeit des Zugriffs,
- aufgerufene URL, HTTP-Methode und Antwortstatus,
- Browser- und Geräteinformationen, soweit sie im User-Agent übermittelt werden,
- Referrer, falls vom Browser übermittelt,
- Proxy-Header wie `X-Forwarded-For`, `X-Forwarded-Host`, `X-Forwarded-Proto` und `X-Forwarded-Port`, soweit die produktive Installation diese verwendet,
- technische Fehler- und Konsolenmeldungen.

Der Quellcode nutzt für den Produktivstart `waitress` und `paste.translogger`. Welche Protokolldaten tatsächlich dauerhaft gespeichert werden, hängt von der Server- und Proxykonfiguration des Betreibers ab.

Zwecke der Verarbeitung sind die Auslieferung der Website, die technische Stabilität, Missbrauchserkennung, Fehlersuche und IT-Sicherheit. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Das berechtigte Interesse liegt im sicheren und störungsfreien Betrieb der Webanwendung. Soweit gesetzliche Aufbewahrungs- oder Nachweispflichten bestehen, kann Art. 6 Abs. 1 lit. c DSGVO hinzutreten.

**Speicherdauer:** Im Quellcode ist keine feste Löschfrist für Serverprotokolle hinterlegt. Der Betreiber sollte eine konkrete Frist festlegen, zum Beispiel 7 bis 30 Tage für normale Zugriffslogs, längere Speicherung nur bei sicherheitsrelevanten Vorfällen.

## 5. Registrierung und Benutzerkonto

Für die Registrierung und Verwaltung eines Benutzerkontos verarbeitet die Anwendung insbesondere:

- Benutzername,
- E-Mail-Adresse,
- Vorname und Nachname,
- VdS-Mitgliedsnummer,
- Passwort in gehashter Form,
- Profilbild-Dateiname und optional hochgeladenes Profilbild,
- Benutzergruppen und Rollen,
- Benutzereinstellungen, derzeit insbesondere der Expertenmodus,
- Zeitstempel `last_login`, wobei der Code diesen Wert beim Anlegen setzt; eine laufende Aktualisierung beim Login wurde in der geprüften Version nicht eindeutig festgestellt.

Die Passwörter werden nicht im Klartext gespeichert, sondern mit `bcrypt` gehasht. Passwort-Reset-Links werden über ein zeitlich begrenztes Token erzeugt.

Zweck der Verarbeitung ist die Einrichtung und Absicherung des Benutzerkontos, die Prüfung der Zugangsberechtigung, die Rollen- und Rechteverwaltung und die Zuordnung von Anträgen zu Nutzern. Rechtsgrundlage ist je nach Betreiberkonstellation Art. 6 Abs. 1 lit. b DSGVO, wenn die Nutzung Teil eines Mitgliedschafts- oder Nutzungsverhältnisses ist, und ergänzend Art. 6 Abs. 1 lit. f DSGVO für sichere Authentifizierung und Rechteverwaltung.

Die VdS-Mitgliedsnummer wird zur Zuordnung bzw. Prüfung der Mitgliedschaft verarbeitet. Im Registrierungsformular wird auf `easyverein.com` verwiesen, damit Nutzer ihre Mitgliedsnummer nachschlagen können. Die Anwendung selbst ruft EasyVerein nach dem geprüften Code nicht automatisch im Hintergrund auf.

## 6. Anmeldung, Sitzung und Cookies

Die Anwendung nutzt eine serverseitige Anmeldung mit Flask-Login. Für angemeldete Sitzungen setzt der Browser technisch notwendige Cookies. Diese Cookies dienen dazu, den Loginzustand und die sichere Nutzung der Anwendung zu ermöglichen.

Im Code ist für Sitzungscookies konfiguriert:

- `HttpOnly`: aktiviert,
- `SameSite=Lax`: aktiviert,
- `Secure`: in der geprüften Version auf `False`, damit lokale Tests ohne HTTPS funktionieren.

Für den Produktivbetrieb über HTTPS sollte der Betreiber `Secure` aktivieren, damit Sitzungscookies nur über HTTPS übertragen werden.

Beim Login kann die Option „An mich erinnern“ gewählt werden. Dann kann ein dauerhaftes Remember-Me-Cookie gesetzt werden, damit der Nutzer über die reine Browsersitzung hinaus angemeldet bleibt.

Rechtsgrundlage für notwendige Session-Cookies ist Art. 6 Abs. 1 lit. f DSGVO sowie für das Speichern oder Auslesen auf dem Endgerät § 25 Abs. 2 Nr. 2 TDDDG, soweit die Speicherung für den ausdrücklich gewünschten Dienst erforderlich ist. Für optionale Komfortfunktionen wie „An mich erinnern“ sollte der Betreiber den optionalen Charakter klar darstellen.

## 7. Browser-Speicher für Darstellung

Die Anwendung speichert die gewählte Darstellung für helles, dunkles oder automatisches Farbschema im Browser-`localStorage` unter dem Schlüssel `theme`. Außerdem kann die Systemeinstellung des Browsers für den bevorzugten Farbmodus ausgewertet werden.

Diese Information dient ausschließlich der Darstellung der Oberfläche im Browser. Nach dem geprüften Code wird daraus kein Trackingprofil erstellt und keine externe Analyse übertragen.

## 8. Profilbilder

Nutzer können im Kontobereich ein Profilbild hochladen. Der Code erlaubt Bilddateien mit den Endungen `jpg` und `png`, erzeugt daraus ein verkleinertes Bild mit 125 x 125 Pixeln und speichert es unter einem zufällig erzeugten Dateinamen im Verzeichnis `webapp/static/profile_pics/`.

Profilbilder können anderen Nutzern dort angezeigt werden, wo Autoren- oder Benutzerinformationen ausgegeben werden. Rechtsgrundlage ist Art. 6 Abs. 1 lit. a DSGVO, soweit das Profilbild freiwillig hochgeladen wird, oder Art. 6 Abs. 1 lit. f DSGVO für die nutzerbezogene Darstellung innerhalb der Anwendung. Der Betreiber sollte eine einfache Möglichkeit zur Entfernung oder Ersetzung des Profilbilds bereitstellen.

## 9. Beobachtungsanträge und Terminsystem

Bei der Erstellung, Bearbeitung und Bearbeitung durch Poweruser oder Administratoren verarbeitet die Anwendung insbesondere:

- Antragsteller bzw. Beteiligte,
- zugeordnetes Benutzerkonto,
- Erstellungsdatum,
- gewünschtes Beobachtungsdatum,
- Observatorium,
- Antragstyp, zum Beispiel Beobachtung, Führung oder Wartung,
- gewünschter Poweruser,
- Freitext-Anmerkungen,
- Status des Antrags,
- Teleskop, Filterset und Objektart,
- Objektname und Zielkoordinaten,
- Belichtungsanzahl, Belichtungszeit, Startzeit, Gain, Offset, Dither, Fokus und Mosaikangabe,
- Reservierungsstatus, Reservierungsablauf und Buchungsstatus.

Astronomische Objekt- und Koordinatendaten sind für sich genommen regelmäßig keine personenbezogenen Daten. Sie werden aber personenbezogen, wenn sie mit einem Benutzerkonto, einem Antrag, einer E-Mail-Adresse, einem Poweruser oder einem Termin verknüpft werden.

Zwecke der Verarbeitung sind Terminplanung, fachliche Prüfung, Durchführung und Dokumentation der Beobachtung sowie Vermeidung von Doppelbelegungen oder Mehrfachbeobachtungen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO, wenn die Verarbeitung zur Durchführung eines Nutzungs- oder Mitgliedschaftsverhältnisses erforderlich ist, und ergänzend Art. 6 Abs. 1 lit. f DSGVO für Organisation, Nachvollziehbarkeit und sicheren Betrieb der Sternwarte.

## 10. Poweruser, Approver und Administratoren

Die Anwendung unterscheidet normale Benutzer, Poweruser, Approver und Administratoren über Gruppen und Rollen. Je nach Rolle können zusätzliche Daten sichtbar oder bearbeitbar sein.

Poweruser können Rückmeldungen zu Beobachtungsanträgen abgeben. Gespeichert werden dabei:

- Beobachtungsantrag,
- Poweruser-Benutzerkonto,
- Verfügbarkeit, zum Beispiel möglich, vielleicht möglich oder nicht möglich,
- Zeitstempel der Rückmeldung.

Approver und Administratoren können Anträge prüfen, Poweruser zuweisen, Anträge genehmigen oder ablehnen und Ablehnungsgründe erfassen. Dabei können Namen, E-Mail-Adressen, Antragsdaten, Freitexte und Statusinformationen für diese Rollen sichtbar werden.

Administratoren können zusätzlich Benutzer, Gruppen, Rollen, Stammdaten, Anträge, Positionen, Systemparameter, Beobachtungshistorie und weitere Tabellen über Flask-Admin verwalten. Die Adminansichten erlauben nach dem geprüften Code auch Exportfunktionen.

Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO für die Durchführung der Sternwartennutzung und Art. 6 Abs. 1 lit. f DSGVO für Organisation, Rechteverwaltung, Qualitätssicherung und Sicherheit.

## 11. Beiträge und öffentliche bzw. interne Anzeige

Die Anwendung enthält ein Beitragsmodul. Beiträge speichern mindestens:

- Titel,
- Inhalt,
- Veröffentlichungszeitpunkt,
- zugeordnetes Benutzerkonto als Autor.

Je nach Seitendarstellung können Benutzername, Anzeigename und Profilbild zusammen mit Beiträgen angezeigt werden. Nutzer sollten daher keine personenbezogenen Daten Dritter in Beiträge oder Freitextfelder eintragen, wenn dies nicht erforderlich ist.

## 12. E-Mail-Kommunikation

Die Anwendung versendet E-Mails über Flask-Mail. Die konkreten SMTP-Zugangsdaten werden aus der Betreiberkonfiguration gelesen. In der Beispielkonfiguration ist als Mailserver `smtp.googlemail.com` eingetragen; der tatsächliche Produktivserver kann davon abweichen.

Die Anwendung versendet insbesondere:

- E-Mails zum Zurücksetzen des Passworts,
- Genehmigungs-E-Mails für Anträge an Antragsteller, Approver und zugewiesenen Poweruser,
- Ablehnungs-E-Mails an Antragsteller und Approver,
- in Nicht-Produktionsumgebungen teilweise Kopien oder Zusatzinformationen an die Admin-E-Mail-Adresse.

E-Mails können Namen, E-Mail-Adressen, Antragsnummern, Beobachtungsdatum, Link zum Antrag, Poweruser-Namen und Ablehnungsgründe enthalten. Für den Mailversand können diese Daten an den SMTP-Anbieter übertragen werden.

Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO für vertrags- bzw. nutzungsbezogene Kommunikation und Art. 6 Abs. 1 lit. f DSGVO für organisatorische und sicherheitsbezogene Benachrichtigungen.

Der Betreiber muss den tatsächlich eingesetzten Mailanbieter benennen und prüfen, ob mit diesem ein Auftragsverarbeitungsvertrag erforderlich ist. Bei Anbietern außerhalb des Europäischen Wirtschaftsraums sind geeignete Garantien für Drittlandübermittlungen anzugeben.

## 13. Externe Dienste, eingebundene Inhalte und Links

Nach der Quellcodeprüfung sind Bootstrap, Bootstrap Icons, htmx und jQuery lokal in der Anwendung eingebunden. Ein CDN-Aufruf für diese Bibliotheken wurde nicht festgestellt.

Folgende externe Bezüge sind im Code erkennbar:

- Direkt eingebundenes Logo von `sternfreunde.de`: Die Kopfzeile lädt ein Bild von `https://sternfreunde.de/wp-content/uploads/2021/12/REMOTE-STERNWARTEN-FG-LOGO.jpg`. Beim Laden dieses Bildes können technisch notwendige Zugriffsdaten wie IP-Adresse, Browserinformationen, Zeitpunkt und Referrer an `sternfreunde.de` übertragen werden.
- Link zur allgemeinen VdS-Website und zur Fachgruppe Remote Sternwarten.
- Link zur allgemeinen VdS-Datenschutzerklärung.
- Link zu EasyVerein für die VdS-Mitgliedsnummer.
- Links zu Nextcloud-Unterlagen und einem Nextcloud-Formular für Statistik bzw. Dokumentation.
- Nennung bzw. Link zu einer Groups.io-Adresse für Antragsfragen.
- Link zu GitHub für Quellcode und Commitanzeige.
- In Genehmigungs-E-Mails wird ein Jitsi-Link unter `https://jitsi.decoit.de/VdS-Sternwarte` genannt.

Soweit diese Dienste nur verlinkt sind, werden Daten grundsätzlich erst dann an den jeweiligen Anbieter übertragen, wenn der Nutzer den Link aufruft oder die externe Seite nutzt. Eine Ausnahme ist das eingebundene Logo, weil es bereits beim Laden der Seite vom externen Server abgerufen wird.

Der Betreiber sollte prüfen, ob das Logo lokal ausgeliefert werden kann, um eine unnötige Drittanfrage zu vermeiden.

## 14. Hintergrunddienste, Redis und Celery

Die Anwendung nutzt Celery für Hintergrundaufgaben, insbesondere für E-Mailversand und das regelmäßige Ablaufenlassen von Reservierungen. Die Beispielkonfiguration verwendet Redis unter `redis://localhost:6379` als Broker und Result-Backend.

Wenn Redis lokal auf demselben Server betrieben wird, verbleiben die hierfür erforderlichen technischen Aufgabendaten im Verantwortungsbereich des Betreibers. Wird Redis als externer oder gemanagter Dienst betrieben, muss der Betreiber diesen Dienst als Empfänger bzw. Auftragsverarbeiter benennen und vertraglich absichern.

## 15. Datenbankexport, Import und Sicherungen

Administratoren können nach dem geprüften Code einen vollständigen JSON-Export der Datenbank erzeugen. Dieser Export umfasst zahlreiche Tabellen, darunter Benutzer, Benutzerpräferenzen, Gruppen, Rollen, Beiträge, Poweruser, Beobachtungsanträge, Positionen, Historien, Systemparameter, Katalogmetadaten und Katalogdaten.

Der Export verwendet eine generische Tabellenkonvertierung. In der geprüften Version werden dabei grundsätzlich alle Spalten eines Datensatzes ausgegeben. Dadurch können auch sensible technische Daten wie Passwort-Hashes im Export enthalten sein.

Solche Exporte und Sicherungen sind besonders zu schützen. Sie dürfen nur von berechtigten Administratoren erzeugt werden, müssen verschlüsselt oder anderweitig angemessen gesichert gespeichert werden und sind nach Wegfall des Zwecks zu löschen. Zugriffe auf Exporte sollten protokolliert und organisatorisch beschränkt werden.

## 16. Speicherdauer und Löschung

Der Quellcode enthält keine umfassende automatische Löschlogik für Benutzerkonten, Anträge, Beiträge, Logs, Beobachtungshistorie oder Admin-Exporte. Reservierungen können über Hintergrundaufgaben ablaufen, die eigentlichen Antrags- und Historiendaten bleiben jedoch grundsätzlich in der Datenbank, bis sie administrativ gelöscht oder durch Import/Exportprozesse verändert werden.

Der Betreiber muss daher konkrete Lösch- und Aufbewahrungsfristen festlegen. Empfohlen wird eine Fristentabelle, zum Beispiel:

- Serverlogs: kurze technische Frist, etwa 7 bis 30 Tage, soweit kein Sicherheitsvorfall vorliegt.
- Benutzerkonten: Löschung oder Anonymisierung nach Ende der Nutzungsberechtigung und Ablauf erforderlicher Nachweisfristen.
- Beobachtungsanträge: Löschung oder Anonymisierung nach Abschluss der Beobachtung und Ablauf organisatorisch benötigter Dokumentationsfristen.
- Ablehnungsgründe und Freitexte: möglichst kurze Aufbewahrung, soweit sie nicht für Rückfragen erforderlich sind.
- Admin-Exporte und Backups: besonders kurze operative Fristen, dokumentierte Speicherung, Zugriffsbeschränkung und sichere Löschung.
- Beobachtungshistorie und Statistik: soweit möglich anonymisiert oder pseudonymisiert führen, wenn die langfristige fachliche Statistik ohne Personenbezug auskommt.

Bis zur Festlegung solcher Fristen sollte die Datenschutzerklärung offen sagen, dass personenbezogene Daten gelöscht werden, sobald sie für die genannten Zwecke nicht mehr erforderlich sind und keine gesetzlichen oder berechtigten Aufbewahrungsgründe entgegenstehen.

## 17. Empfänger und Kategorien von Empfängern

Personenbezogene Daten können je nach Rolle und Vorgang folgenden Empfängern oder Empfängerkategorien offengelegt werden:

- berechtigte Administratoren,
- Approver bzw. fachliche Prüfer,
- zugewiesene Poweruser,
- der jeweilige Antragsteller,
- Hosting- oder Serverdienstleister,
- Mailanbieter,
- Betreiber eines gegebenenfalls externen Redis- oder Hintergrunddienstes,
- Empfänger von E-Mails im Rahmen der Antragskommunikation,
- externe Anbieter, wenn Nutzer verlinkte Dienste aufrufen oder wenn externe Inhalte wie das Logo geladen werden,
- Behörden oder Dritte, soweit eine rechtliche Verpflichtung besteht.

Eine Weitergabe zu Werbezwecken ist im geprüften Code nicht erkennbar.

## 18. Drittlandübermittlungen

Der geprüfte Code erzwingt keine bestimmte Drittlandübermittlung. Drittlandübermittlungen können jedoch je nach tatsächlicher Betreiberkonfiguration entstehen, insbesondere wenn der Mailanbieter, Hosting-Anbieter, GitHub, EasyVerein, Groups.io, Jitsi oder sonstige verlinkte Dienste außerhalb des Europäischen Wirtschaftsraums personenbezogene Daten verarbeiten.

Der Betreiber muss die tatsächlichen Anbieter prüfen und gegebenenfalls die Rechtsgrundlage für Drittlandübermittlungen benennen, etwa Angemessenheitsbeschluss, EU-Standardvertragsklauseln oder andere geeignete Garantien nach Art. 44 ff. DSGVO.

## 19. Pflicht zur Bereitstellung von Daten

Für die Registrierung und Nutzung der Antragsfunktionen sind bestimmte Daten erforderlich, insbesondere Benutzername, E-Mail-Adresse, Passwort, Name, gegebenenfalls VdS-Mitgliedsnummer sowie die für den Antrag erforderlichen Termins- und Beobachtungsdaten. Ohne diese Daten kann die Anwendung nicht oder nur eingeschränkt genutzt werden.

Optionale Angaben wie Profilbild, Wunsch-Poweruser oder zusätzliche Freitext-Anmerkungen sind nur erforderlich, wenn der jeweilige Nutzer diese Funktion nutzen möchte.

## 20. Automatisierte Entscheidungen und Profiling

Eine ausschließlich automatisierte Entscheidung im Sinne von Art. 22 DSGVO oder ein Profiling zu Werbe- oder Scoringzwecken ist im geprüften Code nicht erkennbar.

Automatisiert verarbeitet werden technische Status- und Reservierungsvorgänge, zum Beispiel das Ablaufenlassen von Reservierungen. Fachliche Entscheidungen über Genehmigung, Ablehnung oder Poweruser-Zuordnung erfolgen nach dem geprüften Code durch berechtigte Nutzerrollen.

## 21. Sicherheit

Die Anwendung nutzt Rollen und Gruppen zur Zugriffsbeschränkung. Passwörter werden gehasht gespeichert. Sitzungscookies sind als `HttpOnly` und `SameSite=Lax` konfiguriert. Formulare verwenden Flask-WTF und damit grundsätzlich CSRF-Schutz, soweit dieser nicht in untergeordneten Formularen bewusst deaktiviert wurde.

Für den Produktivbetrieb sollte der Betreiber insbesondere sicherstellen:

- Betrieb ausschließlich über HTTPS,
- Aktivierung sicherer Cookies mit `SESSION_COOKIE_SECURE=True`,
- sichere Geheimnisse und keine Beispielwerte wie `changeme`,
- aktuelle Sicherheitsupdates,
- Zugriffsbeschränkung für Adminbereich, Exporte und Backups,
- Protokollierung administrativer Zugriffe auf Exporte,
- definierte Löschfristen,
- Auftragsverarbeitungsverträge mit Hosting-, Mail- und sonstigen Dienstleistern,
- Prüfung, ob externe Inhalte lokal ausgeliefert werden können.

## 22. Rechte der betroffenen Personen

Betroffene Personen haben nach Maßgabe der DSGVO insbesondere folgende Rechte:

- Recht auf Auskunft nach Art. 15 DSGVO,
- Recht auf Berichtigung nach Art. 16 DSGVO,
- Recht auf Löschung nach Art. 17 DSGVO,
- Recht auf Einschränkung der Verarbeitung nach Art. 18 DSGVO,
- Recht auf Datenübertragbarkeit nach Art. 20 DSGVO, soweit die Voraussetzungen vorliegen,
- Recht auf Widerspruch nach Art. 21 DSGVO,
- Recht auf Widerruf einer Einwilligung nach Art. 7 Abs. 3 DSGVO, soweit die Verarbeitung auf Einwilligung beruht.

Zur Ausübung der Rechte genügt eine Mitteilung an den oben genannten Datenschutzkontakt. Der Betreiber kann eine Identitätsprüfung verlangen, wenn begründete Zweifel an der Identität der anfragenden Person bestehen.

Außerdem besteht ein Beschwerderecht bei einer Datenschutzaufsichtsbehörde nach Art. 77 DSGVO. Zuständig ist in der Regel die Aufsichtsbehörde am Sitz des Verantwortlichen oder am Wohnort der betroffenen Person.

## 23. Änderungen dieser Datenschutzerklärung

Diese Datenschutzerklärung sollte angepasst werden, wenn sich Funktionen, Rollen, Empfänger, Dienstleister, Speicherfristen oder Rechtsgrundlagen ändern. Besonders zu prüfen sind Änderungen an Mailversand, Hosting, externen Inhalten, Admin-Exporten, Backups, Statistikfunktionen und Benutzerrollen.

## 24. Quellen

- Datenschutz-Grundverordnung, Verordnung (EU) 2016/679, EUR-Lex: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- BfDI, Informationspflichten nach Art. 13 und 14 DSGVO: https://www.bfdi.bund.de/DE/Buerger/Inhalte/Allgemein/Datenschutz/Informationspflichten.html
- EDPB, Rechte betroffener Personen und Transparenzhinweise: https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en
- EDPB / Artikel-29-Gruppe, Guidelines on transparency under Regulation 2016/679: https://www.edpb.europa.eu/documents/guideline/article-29-working-party-guidelines-on-transparency-under-regulation-2016679_en
- § 25 TDDDG, Schutz der Privatsphäre bei Endeinrichtungen: https://www.gesetze-im-internet.de/ttdsg/__25.html

---

# Anhang für Betreiber und Entwickler: aus dem Quellcode abgeleitete Verarbeitung

Dieser Anhang ist nicht zwingend als öffentlicher Teil der Datenschutzerklärung gedacht. Er dokumentiert, welche Codefunde zu den obigen Passagen geführt haben.

## Geprüfte Codebasis

- Repository: `https://github.com/peter-englmaier/vds-sternwarte`
- Commit: `9ee278e`
- Zeitpunkt der lokalen Prüfung: 29. Juli 2026, 21:31 bis 21:35 Uhr MESZ

## Datenbankmodelle mit Personenbezug

- `webapp/model/db.py`: `User` speichert Benutzername, E-Mail, Profilbilddateiname, Passwort-Hash, Nachname, Vorname, VdS-Nummer, Loginzeitstempel, Gruppen und Präferenzen.
- `webapp/model/db.py`: `UserPreferences` speichert nutzerbezogene Schlüssel-Wert-Einstellungen, unter anderem den Expertenmodus.
- `webapp/model/db.py`: `Post` speichert Beiträge mit Autorbezug.
- `webapp/model/db.py`: `Poweruser` speichert Name, E-Mail, Mobiltelefon, Telefon, Einweisungs- und Statusdaten.
- `webapp/model/db.py`: `ObservationRequest` speichert Antragsteller, Nutzer-ID, Erstellungsdatum, Wunschtermin, Observatorium, Antragstyp, Poweruser-Wunsch, Freitext, Status.
- `webapp/model/db.py`: `ObservationRequestPosition` speichert Beobachtungspositionen mit Objekt, Koordinaten, Teleskop, Filter, Belichtungs- und Mosaikdaten.
- `webapp/model/db.py`: `ObservationRequestLog` speichert antragsbezogene Protokolle mit Zeitstempel und Text.
- `webapp/model/db.py`: `PoweruserMeldung` speichert Rückmeldungen von Powerusern zu Anträgen.
- `webapp/model/db.py`: `ObservatoryReservation` speichert Terminreservierungen.
- `webapp/model/db.py`: `ObservationHistory` enthält historische Beobachtungsdaten mit Feldern wie `Bildersteller` und `Observer`.

## Registrierung, Login und Profil

- `webapp/users/forms.py`: Registrierungsformular mit Benutzername, E-Mail, Vorname, Nachname, VdS-Mitgliedsnummer, Passwort und Passwortwiederholung.
- `webapp/users/routes.py`: Registrierung speichert einen bcrypt-Hash des Passworts und ordnet neue Nutzer der Guest-Gruppe zu.
- `webapp/users/routes.py`: Login akzeptiert E-Mail oder Benutzername und optional „An mich erinnern“.
- `webapp/users/routes.py` und `webapp/users/utils.py`: Profilbild-Upload erzeugt ein verkleinertes Bild im statischen Profilbildverzeichnis.
- `webapp/users/utils.py`: Passwort-Reset erzeugt ein Token und versendet E-Mail.

## Anträge, Rollen und E-Mail

- `webapp/orders/orderform.py`: Antragsformular mit Datum, Beteiligten, Observatorium, Wunsch-Poweruser, Typ und Anmerkungen; Positionsformular mit Objekt- und Belichtungsdaten.
- `webapp/orders/routes.py`: Anträge können durch Rollen `user`, `poweruser` und `approver` bearbeitet werden; Admins erhalten über `role_required` ebenfalls Zugriff.
- `webapp/orders/routes.py`: Genehmigungs-E-Mails gehen an Antragsteller, Approver und Poweruser und enthalten Antrag, Datum, Link, Poweruser und externe Hinweise auf Jitsi und Nextcloud.
- `webapp/orders/routes.py`: Ablehnungs-E-Mails gehen an Antragsteller und Approver und enthalten Ablehnungsgrund.

## Administration und Export

- `webapp/admin/utils.py`: Generische Adminansichten erlauben Erstellen, Bearbeiten, Löschen, Detailansicht und Export; Zugriff nur für Adminrolle.
- `webapp/inout/routes.py`: Adminroute `/inout/export` exportiert alle Tabellen generisch als `database_export.json`.
- `webapp/inout/routes.py`: `record_to_dict` exportiert grundsätzlich alle Spalten eines Modells; dadurch können in vollständigen JSON-Exporten auch Passwort-Hashes enthalten sein.
- `webapp/inout/routes.py`: Adminroute `/inout/import` importiert JSON-Daten wieder in die Datenbank.

## Technik, Cookies und externe Bezüge

- `webapp/__init__.py`: Sitzungscookies mit `HttpOnly`, `SameSite=Lax`, `Secure=False`; Celery-Konfiguration mit Redis-Broker und periodischer Reservierungsaufgabe.
- `prod.py`: Produktivserver über Waitress und `TransLogger`, mögliche Access-Logs und Proxy-Header.
- `config.json-dist`: Beispielkonfiguration für SQLite-Datenbank, SMTP-Mailserver, Adminnutzer, Celery/Redis und Reservierungsfristen.
- `webapp/static/darkmode.js`: Speicherung der Theme-Auswahl im `localStorage`.
- `webapp/templates/layout.html`: extern eingebundenes Logo von `sternfreunde.de`.
- `webapp/main/templates/about.html`: Link zur VdS-Datenschutzerklärung, VdS-Websites und GitHub.
- `webapp/main/templates/faq.html`: Links zu Nextcloud-Unterlagen und Groups.io-Kontaktadresse.
- `webapp/users/templates/register.html`: Link zu EasyVerein für die Mitgliedsnummer.

## Offene Punkte vor Veröffentlichung

1. Verantwortlichen und Datenschutzkontakt verbindlich eintragen.
2. Tatsächlichen Hostinganbieter und Serverstandort bestimmen.
3. Tatsächlichen SMTP-Anbieter bestimmen; Beispielkonfiguration nennt Googlemail, das muss nicht produktiv gelten.
4. Auftragsverarbeitungsverträge für Hosting, Mail, Redis/Queue, Backup und sonstige Dienstleister prüfen.
5. Drittlandübermittlungen prüfen, insbesondere bei Mailanbieter, GitHub, EasyVerein, Groups.io, Jitsi und externen Bildern.
6. Lösch- und Aufbewahrungsfristen verbindlich festlegen.
7. Produktivkonfiguration für HTTPS und sichere Cookies prüfen.
8. Entscheiden, ob das externe Logo lokal gehostet wird.
9. Admin-Exporte absichern, verschlüsseln, protokollieren und fristgerecht löschen.
10. Prüfen, ob Profilbilder und Freitextfelder eine einfache Lösch- oder Korrekturmöglichkeit benötigen.
