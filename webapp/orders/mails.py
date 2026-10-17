"""Celery tasks for the notification mails about orders"""
from smtplib import SMTPAuthenticationError

from celery import shared_task
from flask_mail import Message

from webapp import mail, Config
from webapp.model.db import User, ObservationRequest

# The tasks used to live in webapp/orders/routes.py. Their celery names are kept,
# so that tasks still queued during a deployment are found by the new worker.


@shared_task(bind=True, name="webapp.orders.routes.send_approve_email")
def send_approve_email(self, order_id, approver_id, order_url, info):
    """Celery task: mail that an order is approved and a poweruser is assigned.

    Recipients are the requester, the approver and the poweruser.

    :param order_id: id of the order.
    :param approver_id: id of the approver, who signs the mail.
    :param order_url: absolute link to the order.
    :param info: optional additional text, may be ``None``.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)
    pu = User.query.get(antrag.request_poweruser_id)
    request_date = antrag.request_date.strftime('%d.%m.%Y')

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()
    pu_greeting = pu.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."
    else:
        ps = ""

    recipients = [user.email, approver.email, pu.email]

    msg = Message('Antrag genehmigt',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},
    
die beantragte Beobachtung #{order_id} für den {request_date} wurde genehmigt.
Der Termin ist im Kalender entsprechend reserviert.

Deine Beobachtung wird betreut durch: PU {pu_greeting}
Link zum Antrag: {order_url}
{info or ""}
Wie geht es nun weiter?
- PU {pu_greeting} wird Dich kontaktieren. Für die Kommunikation setzen JITSI https://jitsi.decoit.de/VdS-Sternwarte ein. Dieses ist eine rein Webbrowser basiertende Anwendung und bedarf keiner weiteren Installation.
- Bitte bereite dich auf die Beobachtung  in dem Sinne vor, das alle Informationen zur Erstellung einer N.I.N.A Sequenz durch den PU möglich ist.
- Informiere dich über das Wetter vor Ort. Es ist nicht ausgeschlossen, das die Beobachtung aufgrund von instabilen Bedingungen nicht möglich ist.
- Wir erstellen eine Statistik über die beobachteten Objekte – auch um Mehrfachbeobachtungen zu minimieren. Daher trage bitte die durchgeführten Belichtungen hier ein: https://nextcloud.sternfreunde.de/index.php/f/104569.
- Bitte Feedback an G. Piehler mit Angabe des Grundes, wenn die Beobachtung **NICHT** durchgeführt werden konnte.. Bei Teilausführung wird kein entsprechendes Feedback benötigt. – Danke !

Bitte berücksichtige auch potenzielle allgemeine Bekanntmachungen.

Danke für die Beachtung und viel Erfolg.

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc



@shared_task(bind=True, name="webapp.orders.routes.send_reject_email")
def send_reject_email(self, order_id, approver_id, order_url, info):
    """Celery task: mail that an order is rejected.

    Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param approver_id: id of the approver, who signs the mail.
    :param order_url: absolute link to the order.
    :param info: explanation of the rejection, may be ``None``.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."
    else:
        ps = ""

    recipients = [user.email, approver.email]

    msg = Message('Antrag abgelehnt',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},

Dein Antrag mit der Nummer #{order_id} wurde leider abgelehnt. Gegebenenfalls ist unten eine Erläuterung zu finden.

Link zum Antrag: {order_url}

Erläuterung: {info or "keine"}

Wie geht es nun weiter?
- Falls eine Erläuterung vorhanden ist, bitte diese in einem neuen Antrag berücksichtigen.
- Gegebenenfalls Kontaktaufnahme via Email.

Sorry, Danke!

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc

#TODO
#@shared_task
#def send_submitted_email
#Vorschlag für Mail 1.:
# Hallo {user_greeting},
#
# die beantragte Beobachtung #{order_id} für den {request_date} ist eingegangen.
# Der Termin ist im Kalender entsprechend reserviert.
#
# Link zum Antrag: {order_url}
#
# Wie geht es nun weiter?
# - wir prüfen, ob der Antrag angenommen werden kann.
# - du wirst anschliessend entsprechend informiert.
#
# Danke für die Geduld!
#
# Gruss,
# {Sternwarte}  <<=== diese Mail ist automatisch, also gibts keinen Mensch als Absender

#TODO
#@shared_task
#def send_reservation_expired_email
#Hallo {user_greeting},
#
# der Reservierung für {request_date} von Beobachtung #{order_id} ist abgelaufen.
# Der Termin wurde im Kalender wieder freigegeben. Dadurch soll verhindert werden, dass verwaiste
# Anträge die Sternwarte blockieren. Bitte lösche Anträge, die du nicht einreichen wirst damit kein Termin
# blockiert wird.
#
# Link zum Antrag: {order_url}
#
# Du Termin kann von dir oder einem anderen Benutzer erneut
# reserviert werden - wer zuerst kommt, schnappt sich den Termin!
#
# Gruss,
# {Sternwarte}

@shared_task(bind=True, name="webapp.orders.routes.send_accept_email")
def send_accept_email(self, order_id, approver_id, order_url):
    """Celery task: mail that an order is provisionally accepted.

    Sent when the approver accepts the order of a regular user; a poweruser is
    assigned later. Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param approver_id: id of the approver, who signs the mail.
    :param order_url: absolute link to the order.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    request_date = antrag.request_date.strftime("%d.%m.%Y")
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."
    else:
        ps = ""

    recipients = [user.email, approver.email]

    msg = Message('Antrag eingegangen',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},
die beantragte Beobachtung #{order_id} für den {request_date} ist provisorisch angenommen.
Der Termin ist im Kalender entsprechend reserviert.

Link zum Antrag: {order_url}

Wie geht es nun weiter?
- wir suchen einen PU der die Beobachtung durchführen kann
- du wirst anschliessend entsprechend informiert.

Danke für die Geduld!

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc

@shared_task(bind=True, name="webapp.orders.routes.send_putime_email")
def send_putime_email(self, order_id, approver_id, order_url):
    """Celery task: mail that the observation time of a poweruser is approved.

    Sent when the approver accepts an order of a poweruser.
    Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param approver_id: id of the approver, who signs the mail.
    :param order_url: absolute link to the order.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    request_date = antrag.request_date.strftime("%d.%m.%Y")
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."
    else:
        ps = ""

    recipients = [user.email, approver.email]

    msg = Message('Antrag Poweruser Zeit genehmigt',
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = f'''\
Hallo {user_greeting},
deine Beobachtung #{order_id} für den {request_date} ist genehmigt.
Der Termin ist im Kalender entsprechend reserviert.

Link zum Antrag: {order_url}

Gruss, {approver_greeting}
{ps or ""}
'''
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc
