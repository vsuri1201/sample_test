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

    session['application_firstName']=firstName
    session['application_lastName']=lastName
    session['application_email']=email
    session['application_mobile']=mobile
    session['application_primarySkills']=primarySkills
    session['application_currentDesignation']=currentDesignation
    session['application_message']=message
    session['application_usCitizen']=usCitizen
    session['application_visaSponsorship']=visaSponsorship
    session['application_jobDetail']=jobDetail
    session['application_attachment']=attachment
    session['application_filename']=filename
    session['application_attachment_io']=attachment_io

    return send_application_emails()


def send_application_emails():
    # Create acknowledgment email to the user
    acknowledgment_msg = Message(
        subject="Application Received: " + session.get('application_jobDetail'),
        recipients=[session.get('application_email')],
        body = (
        f"Hello {session.get('application_firstName')} {session.get('application_lastName')},\n\n"
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
        subject="New Job Application: " + session.get('application_jobDetail'),
        recipients=[os.getenv('HR_EMAIL')],  # Replace with your HR email
        body = (
            f"New job application from {session.get('application_firstName')} {session.get('application_lastName')}.\n\n"
            f"Contact Details: {session.get('application_email')}, {session.get('application_mobile')}\n"
            f"Primary Skills: {session.get('application_primarySkills')}\n"
            f"Current Designation: {session.get('application_currentDesignation')}\n"
            f"US Citizen: {session.get('application_usCitizen')}\n"
            f"Visa Sponsorship Required: {session.get('application_visaSponsorship')}\n\n"
            f"Message: {session.get('application_message')}\n\n"
            "Resume attached." if session.get('application_attachment') else "No resume attached."
        )
    )

    # If there is an attachment, attach it to the HR email
    if session.get('application_attachment_io'):
        hr_msg.attach(session.get('application_filename'), session.get('application_attachment').content_type, session.get('application_attachment_io').read())

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

    session['inquiry_name'] = name
    session['inquiry_email'] = email
    session['inquiry_subject'] = subject
    session['inquiry_message'] = message

    return send_inquiry_emails()    

def send_inquiry_emails():
    # Create the notification email to HR with inquiry details
    hr_msg = Message(
        subject = session.get('inquiry_subject'),
        recipients = [os.getenv('HR_EMAIL')],
        body = (
            f"Message from {session.get('inquiry_name')} ({session.get('inquiry_email')})\n\n{session.get('inquiry_message')}"
        )
    )
    try:
        mail.send(hr_msg)
        print('Inquiry email sent to HR')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Create acknowledgment email to the user regarding the inquiry
    acknowledgment_msg = Message(
        subject="DO NOT REPLY "+session.get('inquiry_subject'),
        recipients=[session.get('inquiry_email')],
        body = (
        f"Hello {session.get('inquiry_name')},\n\n"
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
