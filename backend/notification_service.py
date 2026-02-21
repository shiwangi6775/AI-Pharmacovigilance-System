from twilio.rest import Client

ACCOUNT_SID = "AC2cb236ccbdc904e4b04787597643890f"
AUTH_TOKEN = "346e10a3d204953668a25adfa5c67d94"
TWILIO_PHONE = "+15677066325"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_sms(to_number, message):
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE,
        to=to_number
    )

def make_call(to_number):
    client.calls.create(
        twiml="""
        <Response>
            <Say>
                This is an urgent pharmacovigilance alert.
                Please contact your doctor immediately.
            </Say>
        </Response>
        """,
        from_=TWILIO_PHONE,
        to=to_number
    )
