from twilio.rest import Client

ACCOUNT_SID = "YOUR_TWILIO_SID"
AUTH_TOKEN = "YOUR_TWILIO_TOKEN"
TWILIO_NUMBER = "+1XXXXXXXXX"

client = Client(ACCOUNT_SID, AUTH_TOKEN)


def send_sms(phone, message):
    client.messages.create(
        body=message,
        from_=TWILIO_NUMBER,
        to=phone
    )


def make_call(phone):
    client.calls.create(
        to=phone,
        from_=TWILIO_NUMBER,
        twiml="""
        <Response>
            <Say voice="alice">
                This is an automated pharmacovigilance safety call.
                You reported a serious drug reaction.
                Please contact your healthcare provider immediately.
            </Say>
        </Response>
        """
    )
