"""Email alert plugin."""


import email
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define module-level logger.
_log = logging.getLogger(__name__)


class EmailAlert:
    """A plugin to send email notification for anomalies found."""

    def __init__(self, host, port, subject, to, sender, body, use_ssl=True,
                 username=None, password=None):
        """Create an instance of :class:`EmailAlert` plugin.

        Arguments:
            host (str): Server hostname for SMTP.
            port (int): Server port for SMTP.
            subject (str): Subject line for email.
            to (list): List of recipients (str).
            sender (str): From field for email.
            body (str): Email body.
            use_ssl (bool): Is SSL connection required
            username (str): username of email account
            password (str): password of email account
        """
        self._host = host
        self._port = port
        self._subject = subject
        self._to = to
        self._sender = sender
        self._body = body
        self._stringbuffer = []
        self._use_ssl = use_ssl
        self._username = username
        self._password = password

    def write(self, record):
        """Write JSON records to the file system.

        This method is called once for every ``record`` read from a
        cloud. In this example implementation of a alert, we simply
        send the ``record`` in JSON format via email to the recipient.
        The records keeps appending to a stringbuffer which then is
        written in the email body

        Arguments:
            record (dict): Data to send via email.
        """
        for _, value in record.items():
            self._stringbuffer.append(repr(value))

    def done(self):
        """Perform final cleanup tasks.

        This method is called after all records have been written. In
        this example implementation, we properly terminate the JSON
        array in the email body.

        The connection is made based whether the SMTP or SMTP_SSL is
        required which is determined by ``use_ssl`` param. The SMTP
        login process is conducted if ``username`` param is provided.

        """
        message = MIMEMultipart()
        message['Date'] = email.utils.formatdate(localtime=True)
        message['Subject'] = self._subject
        message['From'] = self._sender
        message['To'] = email.utils.COMMASPACE.join(self._to)

        # Incase if the buffer is empty then the default message will be sent
        if self._stringbuffer:
            self._body = ''.join(self._stringbuffer)
        message.attach(MIMEText(self._body))

        smtp = self._prepare_smtp_session()
        try:
            smtp.sendmail(self._sender, self._to, message.as_string())
        except smtplib.SMTPException as e:
            _log.error('Failed to send email: %s', e)
        finally:
            smtp.quit()

    def _prepare_smtp_session(self):
        """Return SMTP connection object.

        Create a SMTP connection based on whether the SSL param.
        If SSL connection is required (for eg: in case of gmail) then
        method will return a SMTP_SSL connection. In other cases if the
        authentication is not required or SMTP_SSL connection is not
        required then a plain SMTP connection object is returned.
        For gmail follow the steps given below even to work for 2 factor
        authentication
        1. Log-in into Gmail with your account
        2. Navigate to https://security.google.com/settings/security/
        apppasswords
        3. In 'select app' choose 'custom', give it an arbitrary name and
        press generate
        4. It will give you 16 chars token.
        5. Use that token as password for login
        6. Host is smtp.gmail.com and port is 465

        """
        if self._use_ssl:
            smtp = smtplib.SMTP_SSL(host=self._host, port=self._port)
            smtp.set_debuglevel(True)
        else:
            smtp = smtplib.SMTP(host=self._host, port=self._port)
            smtp.set_debuglevel(True)
            smtp.starttls()

        if self._username:
            smtp.login(self._username, self._password)
        return smtp
