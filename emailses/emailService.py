import boto3
import traceback

import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "ap-south-1"
SENDER_EMAIL = "anusidu071@gmail.com"

ses = boto3.client(
    "ses",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def send_welcome_email(to_email: str):
    print("Background email started for:", to_email)

    try:
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                "ToAddresses": [to_email]
            },
            Message={
                "Subject": {
                    "Data": "📩 Ryval-X Offer Letter Sent Successfully"
                },
                "Body": {
                    "Html": {
                        "Data": """
                        <html>
                          <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
                            <div style="max-width:600px; margin:auto; background:#ffffff; padding:24px; border-radius:8px;">
                              
                              <h2 style="color:#1a73e8;">Offer Letter Sent – Ryval-X</h2>

                              <p>Dear Candidate,</p>

                              <p>
                                We are pleased to inform you that your
                                <strong>Ryval-X Offer Letter</strong>
                                has been successfully sent to this email address.
                              </p>

                              <p>
                                Please review the offer details carefully and confirm your acceptance
                                within the mentioned timeline.
                              </p>

                              <p>
                                If you have any questions or did not receive the offer email,
                                feel free to contact us.
                              </p>

                              <p style="margin-top:20px;">
                                Best regards,<br>
                                <strong>HR Team</strong><br>
                                Ryval-X
                              </p>

                              <hr style="margin:30px 0;">

                              <p style="font-size:12px; color:#666;">
                                © 2026 Ryval-X. All rights reserved.
                              </p>
                            </div>
                          </body>
                        </html>
                        """
                    }
                }
            }
        )

        print("EMAIL SENT SUCCESSFULLY")
        print("MessageId:", response["MessageId"])

    except Exception as e:
        print("EMAIL FAILED")
        print(str(e))
        traceback.print_exc()
