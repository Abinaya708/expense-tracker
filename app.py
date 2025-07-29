import streamlit as st
import sqlite3
import re
from fpdf import FPDF
from datetime import datetime

# --- DB Setup ---
conn = sqlite3.connect('expenses.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS expenses (user_id INTEGER, date TEXT, item TEXT, amount REAL)''')
conn.commit()

# --- User Management ---
def is_valid_email(email):                      #---> Email Validation
    if "@" not in email or "." not in email:
        return False
    if email.startswith("@") or email.endswith("@") or email.startswith(".") or email.endswith("."):
        return False

    try:
        local_part, domain = email.split("@")
        if "." not in domain:
            return False
        domain_name, extension = domain.rsplit(".", 1)
        if not local_part or not domain_name or len(extension) < 2 or len(extension) > 6:
            return False
        return True
    except ValueError:
        return False


def is_email_registered(email):                #---> Is email already registered?
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    return c.fetchone() is not None

def is_name_taken(name):                       #---> Is name already taken?
    c.execute("SELECT id FROM users WHERE name=?", (name,))
    return c.fetchone() is not None



# --- Registration and Login ---

def register(name, email, password):
    if not is_valid_email(email):
        return "Invalid email format!"
    if is_name_taken(name):
        return "Name already taken! Please choose another."
    if is_email_registered(email):
        return "Email already registered!"
    c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
    conn.commit()
    return "Success"


def login(email, password):
    c.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password))
    return c.fetchone()






# --- Expense Management ---
def add_expense(user_id, date, item, amount):
    c.execute("INSERT INTO expenses (user_id, date, item, amount) VALUES (?, ?, ?, ?)", (user_id, date, item, amount))
    conn.commit()

def get_expenses(user_id, start_date=None, end_date=None):
    query = "SELECT date, item, amount FROM expenses WHERE user_id=?"
    params = [user_id]
    if start_date and end_date:
        query += " AND date BETWEEN ? AND ?"
        params += [start_date, end_date]
    c.execute(query, params)
    return c.fetchall()







# --- PDF Generation ---
def generate_pdf(data, filename="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Expense Report", ln=True, align="C")
    for date, item, amount in data:
        pdf.cell(200, 10, txt=f"{date} | {item} | Rs.{amount}", ln=True)
    pdf.output(filename)







# --- Streamlit App ---

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None

st.title("💸 Expense Tracker")

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Register", "Login"])

    if menu == "Register":
        name = st.text_input("Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            result = register(name, email, password)
            if result == "Success":
                st.success("User registered successfully!")
            else:
                st.error(result)


    elif menu == "Login":
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")


else:
    st.sidebar.success("✅ Logged in")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

    st.success("You are logged in.")
    option = st.selectbox("Action", ["Add Expense", "View Report"])

    if option == "Add Expense":
        date = st.date_input("Date")
        item = st.text_input("Item/Description")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        if st.button("Save Expense"):
            add_expense(st.session_state.user_id, str(date), item, amount)
            st.success("Expense saved!")

    elif option == "View Report":
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
        if st.button("Generate Report"):
            results = get_expenses(st.session_state.user_id, str(start), str(end))
            if results:
                st.write("### Report")
                for row in results:
                    st.write(row)
                generate_pdf(results)
                with open("report.pdf", "rb") as f:
                    st.download_button("Download PDF", f, file_name="report.pdf")
            else:
                st.warning("No data found.")
