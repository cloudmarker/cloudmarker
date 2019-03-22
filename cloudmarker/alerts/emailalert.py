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

    def __init__(self, host, port, subject, to, sender, body):
        """Create an instance of :class:`EmailAlert` plugin.

        Arguments:
            host (string): Server hostname for SMTP.
            port (int): Server port for SMTP.
            subject (string): Subject line for email.
            to (list): List of recipients (string).
            sender (string): From field for email.
            body (string): Email body.

        """
        self.host = host
        self.port = port
        self.subject = subject
        self.to = to
        self.sender = sender
        self.body = body
        self.stringbuffer = []

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
            self.stringbuffer.append(repr(value))

    def done(self):
        """Perform final cleanup tasks.

        This method is called after all records have been written. In
        this example implementation, we properly terminate the JSON
        array in the email body.

        """
        message = MIMEMultipart()
        message['Date'] = email.utils.formatdate(localtime=True)
        message['Subject'] = self.subject
        message['From'] = self.sender
        message['To'] = email.utils.COMMASPACE.join(self.to)

        # Incase if the buffer is empty then the default message will be sent
        if self.stringbuffer:
            self.body = ''.join(self.stringbuffer)
        message.attach(MIMEText(self.body))

        smtp_connection = smtplib.SMTP(host=self.host, port=self.port)
        try:
            smtp_connection.sendmail(self.sender, self.to, message.as_string())
        except smtplib.SMTPException as e:
            _log.error('Failed to send email: %s', e)
        finally:
            smtp_connection.quit()
