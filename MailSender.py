from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor
import cStringIO
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.image import MIMEImage


class MailSender():

    def __init__(self, mailSenderName, mailPassword, smtpHost, smtpPort, logger=None, userName=None, isSecure=True):
        '''
        Mail sender assumes that Twisted reactor has already been running.
        '''
        self.mailSenderName = mailSenderName
        self.mailUserName = (userName if userName else mailSenderName)
        self.mailPassword = mailPassword
        self.smtpHost = smtpHost
        self.smtpPort = int(smtpPort)
        self.isSecure = isSecure
        self.myLogger.info("MailSender init.")

    def sendMail(self, subject, content, toWhom, file2Send=None, fileName=None, callback=None, errBack=None):
        result = self.send(subject, content, toWhom, file2Send, fileName)
        self.myLogger.info("%s | %s | %s" % (subject, content, toWhom))
        if callback and errBack:
            return result.addCallbacks(callback, errBack)
        else:
            return result.addCallbacks(self.cbSentMessage, self.ebSentMessage)

    def send(self, subject, content, toWhom, file2Send, fileName):
        resultDeferred = Deferred()
        msg = MIMEMultipart('mixed', _charset="utf-8")

        if file2Send and fileName:
            if ('png' in fileName) or ('jpg' in fileName) or ('gif' in fileName):
                msg = MIMEMultipart('related', _charset="utf-8")
                msgText = MIMEText(content + '<br><img src="cid:image1"><br>', 'html', 'utf-8')
                msg.attach(msgText)
                msgImage = MIMEImage(file2Send)
                msgImage.add_header('Content-ID', '<image1>')
                msg.attach(msgImage)
            else:
                content = MIMEText(content, 'html', 'utf-8')
                msg.attach(content)
                part = MIMEBase('application', 'zip')
                part.set_payload(file2Send)
                encoders.encode_base64(part)
                part.add_header('Content-Transfer-Encoding', 'base64')
                part.add_header('Content-Disposition', 'attachment', filename='%s' % fileName)
                msg.attach(part)
        else:
            content = MIMEText(content, 'html', 'utf-8')
            msg.attach(content)

        msg["Subject"] = subject
        msg["From"] = self.mailSenderName
        if isinstance(toWhom, (list, tuple)):
            msg["To"] = str(", ").join(toWhom)
        else:
            msg["To"] = toWhom

        email = cStringIO.StringIO(msg.as_string())
        senderFactory = ESMTPSenderFactory(
            self.mailUserName,
            self.mailPassword,
            self.mailSenderName,
            toWhom,
            email,
            resultDeferred,
            requireTransportSecurity=self.isSecure)

        reactor.connectTCP(self.smtpHost, self.smtpPort, senderFactory)
        return resultDeferred

    def cbSentMessage(self, result):
        self.myLogger.info("Mail is sent.")

    def ebSentMessage(self, err):
        self.myLogger.info("Error occured while sending mail: %s", err)
