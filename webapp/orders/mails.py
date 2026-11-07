"""Celery tasks for the notification mails about orders"""
from smtplib import SMTPAuthenticationError

from celery import shared_task
from flask_mail import Message
from flask import render_template

from webapp import mail, Config
from webapp.model.db import User, ObservationRequest, Observatory

# The tasks used to live in webapp/orders/routes.py. Their celery names are kept,
# so that tasks still queued during a deployment are found by the new worker.

def send_email(template, recipients, subject, **tplvars):
    """Celery task: mail templated filled with supplied data.

    :param template: template to be used for the mail.
    :param recipients: list of recipients.
    :param subject: subject of the mail.
    :param order_id: id of the order (optional).
    :param approver_id: id of the approver (optional).
    :param **tplvars: additional named variables used in the template (optional).
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    order_id=tplvars.get('order_id', None)
    approver_id=tplvars.get('approver_id', None)
    if order_id:
        antrag = ObservationRequest.query.get(order_id)
        user = User.query.get(antrag.user_id)
        pu = User.query.get(antrag.request_poweruser_id)
        tplvars['request_date'] = antrag.request_date.strftime('%d.%m.%Y')
        tplvars['observatory'] = Observatory.query.get(antrag.request_observatory_id).name
        tplvars['user_greeting'] = user.display_name()
        tplvars['pu_greeting'] = pu.display_name()
    if approver_id:
        approver = User.query.get(approver_id)
        tplvars['approver_greeting'] = approver.display_name()
    if Config.ENVIRONMENT != "PRODUCTION":
        tplvars['ps'] = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."

    msg = Message(subject,
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = render_template(template, **tplvars)
    try:
        mail.send(msg)
    except SMTPAuthenticationError as exc:
        if exc.smtp_code == 454:
            print(exc)
            raise self.retry(exc=exc)
        else:
            raise exc

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
    send_email('order_approve_mail.txt',
               [user.email, approver.email, pu.email],
               'Antrag genehmigt',
               order_id=order_id,
               approver_id=approver_id,
               order_url=order_url,
               info=info)

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
    send_email('order_reject_mail.txt',
               [user.email, approver.email],
               'Antrag abgelehnt',
               order_id=order_id,
               approver_id=approver_id,
               order_url=order_url,
               info=info)

@shared_task(bind=True, name="webapp.orders.routes.send_submitted_email")
def send_submitted_email(self, order_id, order_url):
    """Celery task: mail that an order is rejected.

    Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param order_url: absolute link to the order.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    send_email('order_submitted_mail.txt',
               [user.email],
               'Antrag eingereicht',
               order_id=order_id,
               order_url=order_url)

@shared_task(bind=True, name="webapp.orders.routes.send_reservation_expired_email")
def send_reservation_expired_email(self, order_id, order_url):
    """Celery task: mail that an order is rejected.

    Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param order_url: absolute link to the order.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """
    antrag = ObservationRequest.query.get(order_id)
    user = User.query.get(antrag.user_id)
    send_email('reservation_expired_mail.txt',
               [user.email],
               'Antrag eingereicht',
               order_id,
               order_url=order_url)

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
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)
    send_email('order_received_mail.txt',
               [user.email, approver.email],
               'Antrag eingegangen',
               order_id=order_id,
               approver_id=approver_id,
               order_url=order_url)

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
    user = User.query.get(antrag.user_id)
    approver = User.query.get(approver_id)
    send_email('order_putime_mail.txt',
               [user.email, approver.email],
               'Antrag Poweruser Zeit genehmigt',
               order_id=order_id,
               approver_id=approver_id,
               order_url=order_url)

@shared_task(bind=True, name="webapp.orders.routes.send_welcome_email")
def send_welcome_email(self, user_id, approve_url):
    """Celery task: mail that the observation time of a poweruser is approved.

    Sent when the approver accepts an order of a poweruser.
    Recipients are the requester and the approver.

    :param order_id: id of the order.
    :param approver_id: id of the approver, who signs the mail.
    :param order_url: absolute link to the order.
    :raises SMTPAuthenticationError: if the mail server rejects the login.
    """

    user = User.query.get(user_id)
    username = user.display_name()

    send_email('user_registered_mail.txt',
               [user.email],
               'Willkommen im Antragsystem der VdS Remotesternwarten',
               user_greeting=username)

    approver_emails = []
    for approver in User.by_role('approver'):
        approver_emails.append(approver.email)

    if len(approver_emails) > 0:
        send_email('notify_approver_user_registered_mail.txt',
                   approver_emails,
                   f'Ein neuer User { username or "?"} hat sich registriert',
                   username=username, email=user.email, vds_number=user.vds_number, approve_url=approve_url)
