import json
import boto3
from botocore.exceptions import ClientError
import phonenumbers

SENDER = "jesusd.diazdiaz@gmail.com"

SNS = "SNS"
EMAIL = "EMAIL"
BOTH = "BOTH"
TYPE_SERVICES = {
    "SNS": SNS,
    "EMAIL": EMAIL,
    "BOTH": BOTH,
}

APPROVAL = "APPROVAL"
REJECTED = "REJECTED"
TYPE_STATUS = {
    "APPROVAL": APPROVAL,
    "REJECTED": REJECTED
}

APPROVAL_TEMPLATE = "ApprovalTemplate"
REJECTED_TEMPLATE = "RejectedTemplate"


def handle_send_email(username, email, is_approved):
    try:
        client = boto3.client('ses')
        response = client.send_templated_email(
            Destination={
                'ToAddresses': [
                    email,
                ],
            },
            Source=SENDER,
            Template=APPROVAL_TEMPLATE if is_approved else REJECTED_TEMPLATE,
            TemplateData=json.dumps({"username": username})
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
        return response


def handle_send_sms(username, phone_number, is_approved):
    sns = boto3.client('sns')
    text = "Aprobado" if is_approved else "Rechazado"
    response = sns.publish(
        PhoneNumber=phone_number,
        Message="Hi {}, Fuiste {}".format(username, text)
    )
    return response


def respond(err, res=None):
    return {
        'statusCode': 400 if err else 200,
        'body': err.args[0] if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    body = json.loads(event['body'])
    username = body['username']
    email = body['email']
    phone_number = body['phoneNumber']
    service = body['service']
    is_approved = body['isApproved']

    try:
        phonenumbers.parse(phone_number, None)
    except phonenumbers.NumberParseException:
        return respond(ValueError("invalid phone number"))

    if service in TYPE_SERVICES:
        response = {}
        if service == EMAIL or service == BOTH:
            response['email'] = handle_send_email(username, email, is_approved)
        if service == SNS or service == BOTH:
            response['sns'] = handle_send_sms(username, phone_number, is_approved)
        return respond(None, response)
    else:
        return respond(ValueError('Unsupported service "{}"'.format(service)))
