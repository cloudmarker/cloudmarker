"""Email alert plugin."""


import email
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define module-level logger.
_log = logging.getLogger(__name__)


class EmailAlert:
    """A plugin to send email alerts."""

    def __init__(self, from_addr, to_addrs,
                 subject='Cloudmarker Alert',
                 host='', port=0, use_ssl=True,
                 username=None, password=None):
        """Create an instance of :class:`EmailAlert` plugin.

        When ``use_ssl`` is ``True`` and ``host`` is not specified or
        specified as ``''``, the local host is used. When ``use_ssl`` is
        ``True`` and ``port`` is not specified or specified as ``0``,
        the standard SMTP-over-SSL, i.e., port 465, is used. See
        :class:`smtplib.SMTP_SSL` documentation for more details on
        this.

        When ``use_ssl`` is ``False`` and if ``host`` or ``port`` are not
        specified, i.e., if host or port are ``''`` and/or ``0``
        respectively, the OS default behavior is used. See
        :class:`smtplib.SMTP` documentation for more details on this.

        If ``username`` is not specified or specified as ``None``, no
        SMTP authentication is done. If ``username`` is specified and it
        is not ``None``, then SMTP authentication is done.

        Arguments:
            from_addr (str): Sender's email address.
            to_addrs (list): A list of :obj:`str` objects where each
                :obj:`str` object is a recipient's email address.
            host (str): SMTP host.
            port (int): SMTP port.
            use_ssl (bool): Use SSL if ``True``, not otherwise.
            username (str): SMTP username.
            password (str): SMTP password.
        """
        self._host = host
        self._port = port
        self._subject = subject
        self._from_addr = from_addr
        self._to_addrs = to_addrs
        self._stringbuffer = []
        self._use_ssl = use_ssl
        self._username = username
        self._password = password

    def write(self, record):
        """Save event record in a buffer.

        Arguments:
            record (dict): An event record.
        """
        for _, value in record.items():
            self._stringbuffer.append(repr(value))

    def done(self):
        """Send the buffered events as an email alert."""
        message = MIMEMultipart()
        message['Date'] = email.utils.formatdate(localtime=True)
        message['Subject'] = self._subject
        message['From'] = self._from_addr
        message['To'] = email.utils.COMMASPACE.join(self._to_addrs)

        body = ''.join(self._stringbuffer)
        message.attach(MIMEText(body))

        smtp = self._prepare_smtp_session()
        try:
            smtp.sendmail(self._from_addr,
                          self._to_addrs,
                          message.as_string())
        except smtplib.SMTPException as e:
            _log.error('Failed to send email: %s', e)
        finally:
            smtp.quit()

    def _prepare_smtp_session(self):
        """Start an SMTP session.

        Returns:
            smtplib.SMTP or smtplib.SMTP_SSL: An SMTP connection
                with its session ready to send messages.

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
