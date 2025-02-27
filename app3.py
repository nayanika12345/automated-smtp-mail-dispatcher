import streamlit as st
import mysql.connector
from mysql.connector import Error
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import hashlib
import schedule
import time
import threading
import pytz
import plotly.express as px
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
import plotly.graph_objects as go
from io import StringIO


# Database connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root', 
            password='nayanika', 
            database='user_management'
        )
        return connection
    except Error as e:
        st.error(f"The error '{e}' occurred")
        return None

# Login functionality
def check_user(email, password):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    connection.close()
    if user and check_password(password, user['password']):
        return user
    return None

# Registration functionality
def register_user(name, email, password, contact_info):
    hashed_password = hash_password(password)
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password, contact_info) VALUES (%s, %s, %s, %s)",
        (name, email, hashed_password, contact_info)
    )
    connection.commit()
    cursor.close()
    connection.close()

# Password hashing and checking
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(input_password, stored_password):
    return hash_password(input_password) == stored_password

# Template CRUD Operations
def create_template(name, subject, body):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO templates (name, subject, body) VALUES (%s, %s, %s)",
        (name, subject, body)
    )
    connection.commit()
    cursor.close()
    connection.close()

def read_templates():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM templates")
    templates = cursor.fetchall()
    cursor.close()
    connection.close()
    return templates

def update_template(template_id, name, subject, body):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE templates SET name = %s, subject = %s, body = %s WHERE id = %s",
        (name, subject, body, template_id)
    )
    connection.commit()
    cursor.close()
    connection.close()

def delete_template(template_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM templates WHERE id = %s", (template_id,))
    connection.commit()
    cursor.close()
    connection.close()

# Contact CRUD Operations
def create_contact(name, email, phone_number):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO contacts (name, email, phone_number) VALUES (%s, %s, %s)",
        (name, email, phone_number)
    )
    connection.commit()
    cursor.close()
    connection.close()

def read_contacts():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()
    cursor.close()
    connection.close()
    return contacts

def delete_contact(contact_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
# Log email events
def log_email_event(email, status):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO application_log (email, timestamp, status) VALUES (%s, %s, %s)",
        (email, datetime.now(), status)
    )
    connection.commit()
    cursor.close()
    connection.close()

def send_email(subject, body, recipients, email_service='gmail'):
    sender_email = "hanumanagasiddikkone@gmail.com" if email_service == 'gmail' else "nayanikakolli@outlook.com"
    password = "jqcu kjgs faqn yrbf" if email_service == 'gmail' else "mtgoevfqvktdxrzg"
    
    try:
        for email in recipients:
            mime_message = MIMEMultipart()
            mime_message['From'] = sender_email
            mime_message['To'] = email
            mime_message['Subject'] = subject
            mime_message.attach(MIMEText(body, 'plain'))

            if email_service == 'gmail':
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, password)
                    server.send_message(mime_message)
            elif email_service == 'outlook':
                with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
                    server.starttls()
                    server.login(sender_email, password)
                    server.send_message(mime_message)

            log_email_event(email, 'Sent')
        st.success(f"Email sent to {len(recipients)} recipient(s).")
    except Exception as e:
        for email in recipients:
            log_email_event(email, 'Failed')
        st.error(f"Failed to send email: {e}")



def schedule_email(subject, body, recipients, send_time, email_service):
    def job():
        send_email(subject, body, recipients, email_service)
        
    # Schedule the job at the specified time
    schedule.every().day.at(send_time).do(job)
    
    # Function to run the scheduler in a background thread
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)  # Check for pending tasks every second
    
    # Start the scheduling process in a background thread
    threading.Thread(target=run_schedule, daemon=True).start()

# Streamlit App Interface
st.set_page_config(page_title="Nayanika's Mailing Application", page_icon="✉️")

# Function to display scheduled emails in the sidebar
def display_scheduled_emails():
    
    if len(st.session_state.scheduled_emails) == 0:
        st.sidebar.write("No emails scheduled.")
    else:
        st.sidebar.subheader("Scheduled Emails")
        for email in st.session_state.scheduled_emails:
            st.sidebar.write(f"Subject: {email['subject']}")
            st.sidebar.write(f"Recipient: {email['recipient']}")
            st.sidebar.write(f"Scheduled Time: {email['send_time']}")
            st.sidebar.write("-" * 30)

def load_recipients_from_csv(uploaded_file):
    if uploaded_file is not None:
        # Read the CSV file as a pandas DataFrame
        
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        df = pd.read_csv(stringio)
        
        # Assuming the CSV has a column named 'email' for email addresses
        if 'email' in df.columns:
            return df['email'].tolist()
        else:
            st.error("CSV file must contain an 'email' column.")
            return []
    return []


# Logout functionality
def logout():
    st.session_state.user = None
    st.session_state.logged_in = False  # Optional, if you are using this flag for login status
    st.session_state.clear()  # Clears all session state
    st.write("You have been logged out.")

# Sidebar Login and Registration
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.title("Login Page")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = check_user(email, password)
        if user:
            st.session_state.user = user
            st.success("Login successful!")
        else:
            st.error("Invalid credentials")

# Function to get color selections for each mail status
def get_color_scheme():
    read_color = st.color_picker("Choose color for Read", "#1f77b4")
    unread_color = st.color_picker("Choose color for Unread", "#ff7f0e")
    failed_color = st.color_picker("Choose color for Failed", "#d62728")
    return read_color, unread_color, failed_color


def register():
    st.title("Registration Page")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    contact_info = st.text_input("Contact Info")
    if st.button("Register"):
        register_user(name, email, password, contact_info)
        st.success("Registration successful! Please log in.")

# Logout Button on Navbar
if st.session_state.user is not None:
    st.sidebar.button("Logout", on_click=logout)

# Login or Register Page
if st.session_state.user is None:
    page = st.sidebar.radio("Choose an option", ["Login", "Register"])
    if page == "Login":
        login()
    elif page == "Register":
        register()
else:
    # Logged in user can access the email functionality
    st.sidebar.success(f"Welcome, {st.session_state.user['name']}")

    # Send Email Interface
    tab = st.sidebar.selectbox("Select Action", ["Send Email", "Manage Templates", "Manage Contacts", "Dashboard", "Application Log","Scheduled mails"])


    # Send Email
    if tab == "Send Email":
        st.header("Send Email")

        email_service = st.selectbox("Choose Email Service", ["Gmail", "Outlook"])
        st.write(f"You selected: {email_service}")

        # Option to choose a template or compose custom email
        templates = read_templates()
        template_names = [template['name'] for template in templates]
        selected_template_name = st.selectbox("Choose Template (Optional)", ["None"] + template_names)

        # Initialize subject and body variables
        subject = ""
        body = ""

        # If a template is selected, prefill the subject and body
        if selected_template_name != "None":
            selected_template = next((t for t in templates if t['name'] == selected_template_name), None)
            if selected_template:
                subject = selected_template['subject']
                body = selected_template['body']

        # Allow user to edit subject and body if they selected a template
        subject = st.text_input("Subject", value=subject)
        body = st.text_area("Message Body", value=body)

        # Allow the user to select recipients from contacts
        contacts = read_contacts()
        contact_emails = [contact['email'] for contact in contacts]
        selected_from_contacts = st.multiselect("Select Recipients", contact_emails)
        uploaded_file = st.file_uploader("Upload CSV file with email addresses (Optional)", type=["csv"])
        recipients_from_csv = load_recipients_from_csv(uploaded_file)
        selected_recipients = selected_from_contacts + recipients_from_csv

        # Options to send immediately or schedule
        send_option = st.radio("Send Option", ["Send Immediately", "Schedule Email"])

        if send_option == "Send Immediately":
            if st.button("Send Email Now"):
                if subject and body and selected_recipients:
                    send_email(subject, body, selected_recipients, email_service=email_service.lower())
                else:
                    st.warning("Please fill in the subject, body, and select at least one recipient.")

        elif send_option == "Schedule Email":
            # Combine date and time properly
            send_date = st.date_input("Select Date", min_value=datetime.today())
            # Use session_state to dynamically update and store selected time
            if "send_time" not in st.session_state:
                st.session_state.send_time = datetime.now().time()  # Default to current time

            send_time = st.time_input("Select Time", value=st.session_state.send_time)

            # Store the selected time in session state to ensure it updates
            st.session_state.send_time = send_time

            # Create a full datetime object by combining date and time
            send_datetime = datetime.combine(send_date, st.session_state.send_time)

            send_time_obj = datetime.combine(send_date, send_time)  # Combine date and time
            send_time_str = send_time_obj.strftime("%H:%M")  # Extract the time in HH:MM format
            
            # Display the selected time (for debugging)
            st.write(f"Selected time: {send_time_obj.strftime('%H:%M:%S')}")

            # Schedule the email when the button is clicked
            if st.button("Schedule Email"):
                if send_time_obj < datetime.now():
                    st.warning("Cannot schedule an email for a past time.")
                else:
                    if subject and body and selected_recipients:
                        threading.Thread(target=schedule_email, args=(subject, body, selected_recipients, send_time_str, email_service.lower())).start()
                        st.success(f"Email scheduled for {send_time_obj.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.session_state.scheduled_emails.append({
                            'subject': subject,
                            'recipient': selected_recipients,
                            'send_time': send_datetime.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    else:
                        st.warning("Please fill in the subject, body, and select at least one recipient.")

    elif tab=="Scheduled mails":
        display_scheduled_emails()
        st.write("Mails will be sent at specified time")
        st.image("send.png")

    # Dashboard for Email Statistics
    elif tab == "Dashboard":
        st.header("Dashboard")

        # Connect to get log data
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT status, timestamp FROM application_log")
        logs = cursor.fetchall()
        cursor.close()
        connection.close()

        if logs:
            # Convert logs to DataFrame for easier manipulation
            log_df = pd.DataFrame(logs)
            log_df['timestamp'] = pd.to_datetime(log_df['timestamp'])
            log_df['date'] = log_df['timestamp'].dt.date  # Extract date for the x-axis

            # Group by date and status for count aggregation
            status_counts = log_df.groupby(['date', 'status']).size().unstack(fill_value=0)

            # Get colors for the chart from user input
            read_color, unread_color, failed_color = get_color_scheme()

            # Bar Chart for daily status counts (Read, Unread, Failed)
            st.subheader("Daily Email Status Counts")
            bar_fig = go.Figure()

            bar_fig.add_trace(go.Bar(
                x=status_counts.index,
                y=status_counts['Sent'],
                name='sent',
                marker_color=read_color,
                hovertemplate="Date: %{x}<br>Status: Sent: %{y}<br>Timestamp: %{customdata}<extra></extra>",  # Use customdata for timestamp
                customdata=log_df.loc[log_df['status'] == 'Sent', 'timestamp']
            ))

            bar_fig.add_trace(go.Bar(
                x=status_counts.index,
                y=status_counts['Read'],
                name='Unread',
                marker_color=unread_color,
                hovertemplate="Date: %{x}<br>Status: Read: %{y}<br>Timestamp: %{customdata}<extra></extra>",  # Use customdata for timestamp
                customdata=log_df.loc[log_df['status'] == 'Read', 'timestamp']
            ))

            bar_fig.add_trace(go.Bar(
                x=status_counts.index,
                y=status_counts['Failed'],
                name='Failed',
                marker_color=failed_color,
                hovertemplate="Date: %{x}<br>Status: Failed: %{y}<br>Timestamp: %{customdata}<extra></extra>",  # Use customdata for timestamp
                customdata=log_df.loc[log_df['status'] == 'Failed', 'timestamp']

            ))

            bar_fig.update_layout(
                barmode='stack',
                title="Email Status by Day",
                xaxis_title="Date",
                yaxis_title="Count",
                legend_title="Status",
                template="plotly_dark",
                xaxis=dict(tickformat="%Y-%m-%d")
            )

            st.plotly_chart(bar_fig)

            # Pie chart for email status distribution
            st.subheader("Email Status Distribution")
            status_counts_summary = log_df['status'].value_counts()

            pie_fig = go.Figure(data=[go.Pie(
                labels=status_counts_summary.index,
                values=status_counts_summary.values,
                marker=dict(colors=[read_color, unread_color, failed_color])
            )])

            pie_fig.update_layout(title="Email Status Distribution", template="plotly_dark")
            st.plotly_chart(pie_fig)

            # Box Plot for email sending times (if numeric data is available in logs)
            st.subheader("Email Sending Time Distribution")
            log_df['hour'] = log_df['timestamp'].dt.hour

            plt.figure(figsize=(10, 6))
            sns.boxplot(data=log_df, x='hour', y='status', palette=[read_color, unread_color, failed_color])
            plt.title("Email Sending Time Distribution by Status")
            plt.xlabel("Hour of Day")
            plt.ylabel("Status")
            st.pyplot(plt)

        else:
            st.warning("No log data available.")

        # Application Log
    elif tab == "Application Log":
        st.header("Application Log")

        connection = create_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM application_log ORDER BY timestamp DESC")
        log_data = cursor.fetchall()
        cursor.close()
        connection.close()

        if log_data:
            log_df = pd.DataFrame(log_data)
            st.dataframe(log_df)
        else:
            st.info("No log entries found.")


    # Manage Templates
    elif tab == "Manage Templates":
        st.header("Manage Email Templates")
        action = st.radio("Choose action", ["Create", "View", "Update", "Delete"])

        if action == "Create":
            name = st.text_input("Template Name")
            subject = st.text_input("Subject")
            body = st.text_area("Body")
            if st.button("Create Template"):
                create_template(name, subject, body)
                st.success("Template Created Successfully!")

        elif action == "View":
            templates = read_templates()
            for template in templates:
                st.subheader(template['name'])
                st.write("Subject:", template['subject'])
                st.write("Body:", template['body'])

        elif action == "Update":
            templates = read_templates()
            template_names = [template['name'] for template in templates]
            selected_template_name = st.selectbox("Select Template", template_names)
            selected_template = next((t for t in templates if t['name'] == selected_template_name), None)

            if selected_template:
                new_name = st.text_input("Template Name", value=selected_template['name'])
                new_subject = st.text_input("Subject", value=selected_template['subject'])
                new_body = st.text_area("Body", value=selected_template['body'])
                if st.button("Update Template"):
                    update_template(selected_template['id'], new_name, new_subject, new_body)
                    st.success("Template Updated Successfully!")

        elif action == "Delete":
            templates = read_templates()
            template_names = [template['name'] for template in templates]
            selected_template_name = st.selectbox("Select Template to Delete", template_names)
            selected_template = next((t for t in templates if t['name'] == selected_template_name), None)

            if selected_template:
                if st.button("Delete Template"):
                    delete_template(selected_template['id'])
                    st.success("Template Deleted Successfully!")

    # Manage Contacts
    elif tab == "Manage Contacts":
        st.header("Manage Contacts")
        action = st.radio("Choose action", ["Add Contact", "View Contacts", "Delete Contact"])

        if action == "Add Contact":
            name = st.text_input("Contact Name")
            email = st.text_input("Contact Email")
            phone_number = st.text_input("Contact Phone Number")
            if st.button("Add Contact"):
                create_contact(name, email, phone_number)
                st.success("Contact Added Successfully!")

        elif action == "View Contacts":
            contacts = read_contacts()
            for contact in contacts:
                st.write(f"Name: {contact['name']}, Email: {contact['email']}, Phone: {contact['phone_number']}")

        elif action == "Delete Contact":
            contacts = read_contacts()
            contact_names = [contact['name'] for contact in contacts]
            selected_contact_name = st.selectbox("Select Contact to Delete", contact_names)
            selected_contact = next((c for c in contacts if c['name'] == selected_contact_name), None)

            if selected_contact:
                if st.button("Delete Contact"):
                    delete_contact(selected_contact['id'])
                    st.success("Contact Deleted Successfully!")

# Running the app
if __name__ == "__main__":
    st.write("Welcome to the Email App!")
    if "scheduled_emails" not in st.session_state:
        st.session_state.scheduled_emails = []

                                
                