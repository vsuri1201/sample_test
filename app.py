import os
from flask import Flask, request, jsonify
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from io import BytesIO

app = Flask(__name__)

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
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    primary_skills = request.form.get('primarySkills')
    current_designation = request.form.get('currentDesignation')
    subject = request.form.get('subject')
    message = request.form.get('message')
    us_citizen = request.form.get('usCitizen')
    visa_sponsorship = request.form.get('visaSponsorship')
    hr_email = os.getenv('HR_EMAIL')

    # Optional: Check if there's an attachment in the request
    attachment = request.files.get('attachments')
    filename = None
    attachment_io = None

    # If there's an attachment, read it into memory
    if attachment:
        filename = secure_filename(attachment.filename)
        attachment_io = BytesIO(attachment.read())  # Read file into memory

    # Create acknowledgment email to the user
    acknowledgment_msg = Message(
        subject="Application Received: " + subject,
        recipients=[email],
        body=f"Hello {first_name} {last_name},\n\nThank you for applying. We have received your application.\n\n"
             "Our team will get back to you soon.\n\nBest regards,\nYour Company"
    )

    try:
        mail.send(acknowledgment_msg)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Create the notification email to HR with all form details
    hr_msg = Message(
        subject="New Job Application: " + subject,
        recipients=[hr_email],  # Replace with your HR email
        body=f"New job application from {first_name} {last_name} ({email}).\n\n"
             f"Primary Skills: {primary_skills}\n"
             f"Current Designation: {current_designation}\n"
             f"US Citizen: {us_citizen}\n"
             f"Visa Sponsorship: {visa_sponsorship}\n\n"
             f"Message: {message}\n\n"
             "Resume attached." if attachment else "No resume attached."
    )

    # If there is an attachment, attach it to the HR email
    if attachment_io:
        hr_msg.attach(filename, attachment.content_type, attachment_io.read())

    try:
        mail.send(hr_msg)
    except Exception as e:
        return jsonify({'error': 'Failed to send email to HR: ' + str(e)}), 500

    return jsonify({'message': 'Application submitted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
