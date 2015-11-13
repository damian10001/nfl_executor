#!/usr/bin/python

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_mail(recipient_address, message):
    # me == my email address
    # you == recipient's email address
    me = "damian.lasek@ericsson.com"
    you = recipient_address
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Nfl Executor results"
    msg['From'] = me
    msg['To'] = you
    
    # Create the body of the message (a plain-text and an HTML version).
#     text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttps://www.python.org"
#     html = """\
#     <html>
#       <head></head>
#       <body>
#         <p>Hi edamlas!<br>
#            How are you?<br>
#            Here is the <a href="https://www.python.org">link</a> you wanted.
#         </p>
#       </body>
#     </html>
#     """
    
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(message, 'plain')
#     part2 = MIMEText(html, 'html')
    
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
#     msg.attach(part2)
    
    # Send the message via local SMTP server.
    server = smtplib.SMTP('localhost')
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    server.sendmail(me, you, msg.as_string())
    server.quit()

