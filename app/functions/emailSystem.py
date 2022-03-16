from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import re
from app.functions.commReport import communication_report
from app.functions.error import InputError
import smtplib
from app.functions import ublExtractor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import sys

mail = smtplib.SMTP(host= os.environ.get('SMTP_HOST'), port=os.environ.get('SMTP_PORT'))
def SMTP_connect():
    mail.starttls()
    mail.login(os.environ.get('SMTP_USERNAME'), os.environ.get('SMTP_PASSWORD'))

def validate_email(email):
    email_regex = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
    return (re.fullmatch(email_regex,email))

def send_email(xml: str, timer_start: datetime):
    """
    Sends UBL invoice to the first ``cac:AccountingCustomerParty`` entry 
    in said UBL.

    Parameters
    ----------
    xml : string
        an `XML` formatted with ``PEPPOL BIS Billing 3.0 standard``

    Returns
    Comm report, email_adress_sent
    -------
    """
    error_codes = []
    
    contacts = ublExtractor.customerContact(xml)

    # check xml exists
    if (xml == None or xml == ''):
        error_codes.append(1)

    # check size of xml
    if (sys.getsizeof(xml) > 10485760):
        error_codes.append(2)
    
    if not validate_email(contacts["cust_email"]):
        error_codes.append(3)

    if error_codes:
        raise InputError(description=communication_report(error_codes, timer_start))

    #create email
    msg = MIMEMultipart()
    msg['Subject'] = (f'Invoice from {contacts["bill_name"]}')
    msg['From'] = (f'{contacts["bill_email"]}')
    msg['To'] = (f'{contacts["cust_email"]}')
    message = f"""
        <html>
            <head></head>
            <body>
                <p>Hello {contacts["cust_name"]},<br>
                    Attached is your invoice.<br>
                    Kind regards,<br>
                    {contacts["bill_name"]} <br>
                    {contacts["bill_email"]}.
                </p>
            </body>
        </html>
    """

    body = MIMEText(message,'HTML')
    msg.attach(body)
    msg.attach(MIMEApplication(xml, Name='invoice.xml'))
    
    return send_mail(contacts, msg, error_codes, timer_start, False)


def send_mail(contacts, msg, error_codes, timer_start: datetime, recall:bool):
    try:
        mail.sendmail(msg['From'], msg['To'], msg.as_string())
        
    except smtplib.SMTPSenderRefused:
        if not recall:
            SMTP_connect()
            send_mail(contacts, msg, error_codes, timer_start, True)

    except smtplib.SMTPHeloError:
        error_codes.append(4)
    except smtplib.SMTPRecipientsRefused:
        error_codes.append(5)
    
    return communication_report(error_codes, timer_start), contacts["cust_email"]

def exit():
    mail.quit()



SMTP_connect()