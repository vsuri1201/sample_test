import os
from flask import Flask, request, jsonify, session
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)
CORS(app)

app.secret_key = os.urandom(24)
# Flask-Mail configuration from environment variables
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

@app.route('/apply', methods=['POST'])
def apply():
    # Retrieve form data
    firstName = request.form.get('firstName')
    lastName = request.form.get('lastName')
    email = request.form.get('email')
    mobile = request.form.get('mobile')
    primarySkills = request.form.get('primarySkills')
    currentDesignation = request.form.get('currentDesignation')
    message = request.form.get('message')
    usCitizen = request.form.get('usCitizen')
    visaSponsorship = request.form.get('visaSponsorship')
    jobDetail = request.form.get('jobDetail')
    # Optional: Check if there's an attachment in the request
    attachment = request.files.get('attachment')
    filename = None
    attachment_io = None

    # If there's an attachment, read it into memory
    if attachment:
        filename = secure_filename(attachment.filename)
        attachment_io = BytesIO(attachment.read())  # Read file into memory

    print(firstName, lastName, email, mobile, primarySkills, currentDesignation, message, usCitizen, visaSponsorship, jobDetail, attachment, filename)

    return send_application_emails(
        firstName=firstName,
        lastName=lastName,
        email=email,
        mobile=mobile,
        primarySkills=primarySkills,
        currentDesignation=currentDesignation,
        message=message,
        usCitizen=usCitizen,
        visaSponsorship=visaSponsorship,
        jobDetail=jobDetail,
        attachment=attachment,
        filename=filename,
        attachment_io=attachment_io
    )


def send_application_emails(firstName, lastName, email, mobile, primarySkills, currentDesignation, message, usCitizen, visaSponsorship, jobDetail, attachment, filename, attachment_io):
    # Create acknowledgment email to the user
    acknowledgment_msg = Message(
        subject="Application Received: " + jobDetail,
        recipients=[email],
        body = (
        f"Hello {firstName} {lastName},\n\n"
        f"Thank you for applying. We have received your application.\n\n"
        "Our team will get back to you soon.\n\nBest regards,\n" + os.getenv('COMPANY_NAME')
        )
    )

    try:
        mail.send(acknowledgment_msg)
        print("Application acknowledgment sent to user")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Create the notification email to HR with all form details
    hr_msg = Message(
        subject="New Job Application: " + jobDetail,
        recipients=[os.getenv('HR_EMAIL')],  # Replace with your HR email
        body = (
            f"New job application from {firstName} {lastName}.\n\n"
            f"Contact Details: {email}, {mobile}\n"
            f"Primary Skills: {primarySkills}\n"
            f"Current Designation: {currentDesignation}\n"
            f"US Citizen: {usCitizen}\n"
            f"Visa Sponsorship Required: {visaSponsorship}\n\n"
            f"Message: {message}\n\n"
            "Resume attached." if attachment else "No resume attached."
        )
    )

    # If there is an attachment, attach it to the HR email
    if attachment_io:
        hr_msg.attach(filename, attachment.content_type, attachment_io.read())

    try:
        mail.send(hr_msg)
        print('Job Application sent to HR')
    except Exception as e:
        return jsonify({'error': 'Failed to send email to HR: ' + str(e)}), 500

    return jsonify({'message': 'Application submitted successfully'}), 200

@app.route('/send-message', methods=['POST'])
def send_user_message():
    #Retrieve form data
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    print(name, email, subject, message)

    return send_inquiry_emails(
        name=name,
        email=email,
        subject=subject,
        message=message
    )
    

def send_inquiry_emails(name, email, subject, message):
    # Create the notification email to HR with inquiry details
    hr_msg = Message(
        subject = subject,
        recipients = [os.getenv('HR_EMAIL')],
        body = (
            f"Message from {name} ({email})\n\n{message}"
        )
    )
    try:
        mail.send(hr_msg)
        print('Inquiry email sent to HR')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Create acknowledgment email to the user regarding the inquiry
    acknowledgment_msg = Message(
        subject="DO NOT REPLY "+subject,
        recipients=[email],
        body = (
        f"Hello {name},\n\n"
        f"Thanks for writing to us. We have received your inquiry.\n\n"
        "Our team will get back to you soon.\n\nBest regards,\n" + os.getenv('COMPANY_NAME')
        )
    )
    try:
        mail.send(acknowledgment_msg)
        print("Inquiry Acknowledgment sent to user")
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Inquiry submitted successfully'}), 200


if __name__ == '__main__':
    app.run()
