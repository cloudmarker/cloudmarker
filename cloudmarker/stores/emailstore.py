from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from smtplib import SMTP, SMTPException, SMTP_SSL
import logging

""" Report email notification for anomalies """

# Define module-level logger.
_log = logging.getLogger(__name__)

class EmailStore():

    def __init__(self, host, port, subject, to, sender, body, isSSLRequired, username=None, password=None):
        self.host = host
        self.port = port
        self.subject = subject
        self.to = to
        self.sender = sender
        self.body = body
        self.username = username
        self.password = password
        self.stringbuffer = []
        self.isSSLRequired = isSSLRequired

    def write(self, record):
        """Write JSON records to the file system.

        This method is called once for every ``record`` read from a
        cloud. In this example implementation of a store, we simply
        send the ``record`` in JSON format via email to the recipient.

        The records keeps appending to a stringbuffer which then is
        written in the email body

        Arguments:
            record (dict): Data to send via email.

        """
        for key, value in record.items():
            self.stringbuffer.append(repr(value))

    def done(self):
        """Perform final task of sending email.

        This method is called after all records have been written in the
        stringbuffer. In this example implementation, we create a
        MIMEMultipart object and assigns all the parameters required
        for email to it from the config.

        """
        message = MIMEMultipart()
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = self.subject
        message['From'] = self.sender
        message['To'] = COMMASPACE.join(self.to)

        #Incase if the buffer is empty then the default message will be sent
        if self.stringbuffer:
            self.body = ''.join(self.stringbuffer)
        message.attach(MIMEText(self.body))

        #Connect to smtp host and send email
        smtpConnection = self.getConnection(self.isSSLRequired)
        try:
            smtpConnection.sendmail(self.sender, self.to, message.as_string())
        except SMTPException as e:
            _log.error('Failed to send email; error: {}: {}'
                       .format(type(e).__name__, e))
        finally:
            smtpConnection.quit()

    def getConnection(self, isSSLRequired):

        """Create a SMTP connection based on whether the SSL param.

        If SSL connection is required (for eg: in case of gmail) then
        method will return a SMTP_SSL connection. In other cases if the
        authentication is not required or SMTP_SSL connection is not
        required then a plain SMTP connection object is returned.

        # For gmail follow the steps given below even to work for 2 factor authentication
        # 1. Log-in into Gmail with your account
        # 2. Navigate to https://security.google.com/settings/security/apppasswords
        # 3. In 'select app' choose 'custom', give it an arbitrary name and press generate
        # 4. It will give you 16 chars token.
        # 5. Use that token as password for login
        # 6. Host is smtp.gmail.com and port is 465

        """

        #In case no authentication is required then no need to login
        if self.isSSLRequired:

            smtpConnection = SMTP_SSL(host=self.host, port=self.port)
            smtpConnection.set_debuglevel(False)

            #identity yourself to esmtp server using ehlo. This call is required
            #or else it would throw error: SMTPSenderRefused: (503, b'5.5.1 EHLO/HELO first.
            smtpConnection.ehlo()
            smtpConnection.connect(self.host, self.port)

            #an ehlo call is required just after the connect method and just before login
            #just to identity yourself. If not called it would throw a SMTPSenderRefused error
            #Failed to send email; error: SMTPSenderRefused: (503, b'5.5.1 EHLO/HELO first.
            smtpConnection.ehlo()
            smtpConnection.login(self.username, self.password)
            return smtpConnection
        else:
            return SMTP(host=self.host, port=self.port)
