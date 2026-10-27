"""Celery tasks for the notification mails about orders"""
from smtplib import SMTPAuthenticationError

from celery import shared_task
from flask_mail import Message
from flask import render_template

from webapp import mail, Config
from webapp.model.db import User, ObservationRequest, Observatory

# The tasks used to live in webapp/orders/routes.py. Their celery names are kept,
# so that tasks still queued during a deployment are found by the new worker.

def send_email(template, recipients, subject, order_id, approver_id, order_url, info):
    """Celery task: mail templated filled with supplied data.

    :param template: template to be used for the mail.
    :param recipients: list of recipients.
    :param subject: subject of the mail.
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
    observatory=Observatory.query.get(antrag.request_observatory_id)

    user_greeting = user.display_name()
    approver_greeting = approver.display_name()
    pu_greeting = pu.display_name()

    if Config.ENVIRONMENT != "PRODUCTION":
        ps = f"P.S.: diese Email wurde von {Config.ENVIRONMENT} verschickt."
    else:
        ps = ""

    msg = Message(subject,
                  sender=Config.MAIL_REPLYTO,
                  recipients=recipients)
    msg.body = render_template(template,
                                user_greeting=user_greeting,
                                approver_greeting=approver_greeting,
                                pu_greeting=pu_greeting,
                                order_id=order_id,
                                order_url=order_url,
                                request_date=request_date,
                                observatory=observatory.name,
                                info=info,
                                ps=ps)
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
               order_id,
               approver_id,
               order_url,
               info)

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
               order_id,
               approver_id,
               order_url,
               info)

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
    approver = User.query.get(approver_id)
    send_email('order_submitted_mail.txt',
               [user.email, approver.email],
               'Antrag eingereicht',
               order_id,
               None,
               order_url,
               None)

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
               None,
               order_url,
               None)

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
               order_id,
               approver_id,
               order_url,
               None)

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
               order_id,
               approver_id,
               order_url,
               None)
