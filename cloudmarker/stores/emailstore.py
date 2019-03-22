from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE, formatdate
from smtplib import SMTP, SMTPException
import logging

""" Report email notification for anomalies """

# Define module-level logger.
_log = logging.getLogger(__name__)

class EmailStore():

    def __init__(self, host, port, subject, to, sender, body):
        self.host = host
        self.port = port
        self.subject = subject
        self.to = to
        self.sender = sender
        self.body = body

    def write(self, record):
        """Write JSON records to the file system.

        This method is called once for every ``record`` read from a
        cloud. In this example implementation of a store, we simply
        write the ``record`` in JSON format to a file. The list of
        records is maintained as JSON array in the file. The origin
        worker name in ``record['com']['origin_worker']`` is used to
        determine the filename.

        The records are written to a ``.tmp`` file because we don't want
        to delete the existing complete and useful ``.json`` file
        prematurely.

        Note that other implementations of a store may choose to buffer
        the records in memory instead of writing each record to the
        store immediately. They may then flush the buffer to the store
        based on certain conditions such as buffer size, time interval,
        etc.

        Arguments:
            record (dict): Data to send via email.

        """

    def done(self):
        """Perform final cleanup tasks.

        This method is called after all records have been written. In
        this example implementation, we properly terminate the JSON
        array in the .tmp file. Then we rename the .tmp file to .json
        file.

        Note that other implementations of a store may perform tasks
        like closing a connection to a remote store or flushing any
        remaining records in a buffer.

        """
        message = MIMEMultipart()
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = self.subject
        message['From'] = self.sender
        message['To'] = COMMASPACE.join(self.to)

        #Connect to smtp host and send email
        smtpConnection = SMTP(host=self.host, port=self.port)
        try:
            # identify ourselves to smtp gmail client
            mailserver.ehlo()
            # secure our email with tls encryption
            mailserver.starttls()
            smtpConnection.sendmail(self.sender, self.to, message.as_string())
        except SMTPException as e:
            _log.error('Failed to send email; error: {}: {}'
                       .format(type(e).__name__, e))
        finally:
            smtpConnection.quit()
