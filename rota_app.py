import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import requests  # For Supabase API
import bcrypt  # For password hashing

# Custom CSS for branding
css = """
<style>
    /* Background color */
    .stApp {
        background-color: #f0f2d9;
    }
    /* Text color */
    body, p, div, span, label, input, select, textarea, button, h1, h2, h3, h4, h5, h6 {
        color: #0a4d29 !important;
    }
    /* Sidebar and other elements */
    .stSidebar {
        background-color: #f0f2d9;
    }
    /* Buttons - white background with dark text */
    .stButton > button {
        background-color: #ffffff;
        color: #0a4d29;
        border: 1px solid #0a4d29;
    }
    .stButton > button:hover {
        background-color: #0a4d29;
        color: #ffffff;
    }
    /* Dataframes and tables - adjust for readability */
    .stDataFrame, .dataframe {
        background-color: #ffffff;
        color: #0a4d29;
    }
    /* Inputs - white background */
    .stTextInput > div > div > input, .stSelectbox > div > div > select, .stNumberInput > div > div > input {
        background-color: #ffffff;
        color: #0a4d29;
    }
    /* Alerts and success messages */
    .stAlert {
        background-color: #ffffff;
        color: #0a4d29;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

SUPABASE_URL = "https://htnbizrnnryvsfummxfa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0bmJpenJubnJ5dnNmdW1teGZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI0MDUyNDIsImV4cCI6MjA2Nzk4MTI0Mn0.pc3t1b5rblQtHBLHmDG29IgtfXjwBwXTc-wVPCPVDjo"
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def save_pending(full_name, data):
    requests.post(f"{SUPABASE_URL}/rest/v1/pending_employees", headers=headers, json={"full_name": full_name, "data": json.dumps(data)})

def load_pending():
    response = requests.get(f"{SUPABASE_URL}/rest/v1/pending_employees?select=*", headers=headers)
    pending = {}
    if response.status_code == 200:
        for item in response.json():
            pending[item['full_name']] = json.loads(item['data'])
    return pending

def delete_pending(full_name):
    requests.delete(f"{SUPABASE_URL}/rest/v1/pending_employees?full_name=eq.{full_name}", headers=headers)

# Initialize session state
if 'employees' not in st.session_state:
    st.session_state.employees = {}
    # Auto-add Admin User if not present
    if 'Admin User' not in st.session_state.employees:
        hashed_pw = bcrypt.hashpw("test".encode(), bcrypt.gensalt())
        st.session_state.employees['Admin User'] = {
            'first_name': 'Admin',
            'surname': 'User',
            'date_of_birth': '1900-01-01',
            'start_date': '2025-01-01',
            'email': 'admin@example.com',
            'password': hashed_pw.decode(),
            'type': 'FOH',
            'wage': 0.0,
            'employment_type': 'full_time',
            'holiday_entitlement_days': 28,
            'holiday_taken_days': 0,
            'accrued_holiday_hours': 0.0,
            'used_holiday_hours': 0.0,
            'total_hours_worked': 0.0,
            'role': 'admin'  # New: role field
        }
if 'pending_employees' not in st.session_state:
    st.session_state.pending_employees = load_pending()
if 'schedule' not in st.session_state:
    st.session_state.schedule = {}  # {week_start: {day: {emp: {...}}}}
if 'holidays' not in st.session_state:
    st.session_state.holidays = {}  # {week_start: {day: [emps]}}
if 'days' not in st.session_state:
    st.session_state.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
if 'areas' not in st.session_state:
    st.session_state.areas = ["Kitchen BOH", "Front of House"]
if 'accrual_rate' not in st.session_state:
    st.session_state.accrual_rate = 0.1207
if 'standard_day_hours' not in st.session_state:
    st.session_state.standard_day_hours = 8.0
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None  # 'admin', 'manager', or 'employee'
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_week_start' not in st.session_state:
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())  # Assume week starts Monday
    st.session_state.current_week_start = monday.strftime('%Y-%m-%d')

# Sign Up Form (accessible without login)
if not st.session_state.logged_in and st.sidebar.button("Sign Up as New Employee"):
    st.title("New Employee Sign Up")
    with st.form("new_employee"):
        first_name = st.text_input("First Name")
        surname = st.text_input("Surname")
        dob = st.date_input("Date of Birth", format="DD/MM/YYYY", min_value=datetime.today() - timedelta(days=365*100), max_value=datetime.today() - timedelta(days=365*18))
        start_date = st.date_input("Employment Start Date", format="DD/MM/YYYY")
        email = st.text_input("Email")
        password = st.text_input("Set Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Submit for Approval")
        
        if submit:
            if password != confirm_pw:
                st.error("Passwords do not match.")
            else:
                full_name = f"{first_name} {surname}".strip()
                if full_name not in st.session_state.employees and full_name not in st.session_state.pending_employees:
                    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    pending_data = {
                        'first_name': first_name,
                        'surname': surname,
                        'date_of_birth': dob.strftime("%d/%m/%Y"),
                        'start_date': start_date.strftime("%d/%m/%Y"),
                        'email': email,
                        'password': hashed_pw,
                        'type': '',  # Admin to set
                        'wage': 0.0,  # Admin to set
                        'employment_type': '',  # Admin to set
                        'holiday_entitlement_days': 0,
                        'holiday_taken_days': 0,
                        'accrued_holiday_hours': 0.0,
                        'used_holiday_hours': 0.0,
                        'total_hours_worked': 0.0,
                        'role': 'employee'  # Default; admin can change to manager
                    }
                    st.session_state.pending_employees[full_name] = pending_data
                    save_pending(full_name, pending_data)
                    st.success("Your sign-up has been submitted for approval!")
                    st.rerun()
                else:
                    st.error("Name already exists.")

# Basic login (for demo; not secure)
if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Username (full name)")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in st.session_state.employees:
            stored_pw = st.session_state.employees[username]['password'].encode()
            if bcrypt.checkpw(password.encode(), stored_pw):
                st.session_state.logged_in = True
                st.session_state.current_user = username
                st.session_state.user_role = st.session_state.employees[username]['role']
                st.rerun()
            else:
                st.error("Incorrect password.")
        else:
            st.error("User not found or pending approval.")
    st.stop()

# Sidebar navigation
st.sidebar.title("Cafe Rota App")
if st.session_state.user_role == 'admin':
    page = st.sidebar.radio("Pages", ["Approve Sign-Ups", "Employees", "Schedule", "Reports"])
elif st.session_state.user_role == 'manager':
    page = st.sidebar.radio("Pages", ["Employees", "Schedule", "Reports"])
else:
    page = st.sidebar.radio("Pages", ["View Schedule", "Request Holiday"])

if page == "Approve Sign-Ups" and st.session_state.user_role == 'admin':
    st.title("Approve New Employees")
    st.session_state.pending_employees = load_pending()  # Reload from DB
    if st.session_state.pending_employees:
        for full_name, data in list(st.session_state.pending_employees.items()):
            st.subheader(full_name)
            st.write(f"DOB: {data['date_of_birth']}, Start: {data['start_date']}, Email: {data['email']}")
            emp_type = st.selectbox("Type", ["FOH", "BOH"], key=f"type_{full_name}")
            wage = st.number_input("Wage (£/hr)", min_value=0.0, key=f"wage_{full_name}")
            employment_type = st.selectbox("Employment Type", ["full_time", "hourly"], key=f"emp_type_{full_name}")
            role = st.selectbox("Role", ["employee", "manager"], key=f"role_{full_name}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Approve", key=f"approve_{full_name}"):
                    data['type'] = emp_type
                    data['wage'] = wage
                    data['employment_type'] = employment_type
                    data['role'] = role
                    data['holiday_entitlement_days'] = 28 if employment_type == 'full_time' else 0
                    st.session_state.employees[full_name] = data
                    delete_pending(full_name)
                    st.session_state.pending_employees = load_pending()  # Reload
                    # Initialize schedule for new employee
                    for week_key in st.session_state.schedule:
                        for day in st.session_state.days:
                            st.session_state.schedule[week_key][day][full_name] = {'start': '', 'end': '', 'break_minutes': 0, 'locked': False}
                    st.success(f"{full_name} approved!")
                    st.rerun()
            with col2:
                if st.button("Reject", key=f"reject_{full_name}"):
                    delete_pending(full_name)
                    st.session_state.pending_employees = load_pending()  # Reload
                    st.success(f"{full_name} rejected.")
    else:
        st.info("No pending sign-ups.")

if page == "Employees":
    if st.session_state.user_role in ['admin', 'manager']:
        st.title("Manage Employees")
        
        # Add employee form (for admins/managers)
        with st.form("add_employee"):
            first_name = st.text_input("First Name")
            surname = st.text_input("Surname")
            dob = st.date_input("Date of Birth", format="DD/MM/YYYY", min_value=datetime.today() - timedelta(days=365*100), max_value=datetime.today() - timedelta(days=365*18))
            start_date = st.date_input("Start Date", format="DD/MM/YYYY")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")  # For manual add
            emp_type = st.selectbox("Type", ["FOH", "BOH"])
            wage = st.number_input("Wage (£/hr)", min_value=0.0)
            employment_type = st.selectbox("Employment Type", ["full_time", "hourly"])
            role = st.selectbox("Role", ["employee", "manager"]) if st.session_state.user_role == 'admin' else 'employee'
            submit = st.form_submit_button("Add Employee")
            
            if submit:
                full_name = f"{first_name} {surname}".strip()
                if full_name not in st.session_state.employees:
                    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() if password else ''
                    st.session_state.employees[full_name] = {
                        'first_name': first_name,
                        'surname': surname,
                        'date_of_birth': dob.strftime("%d/%m/%Y"),
                        'start_date': start_date.strftime("%d/%m/%Y"),
                        'email': email,
                        'password': hashed_pw,
                        'type': emp_type,
                        'wage': wage,
                        'employment_type': employment_type,
                        'holiday_entitlement_days': 28 if employment_type == 'full_time' else 0,
                        'holiday_taken_days': 0,
                        'accrued_holiday_hours': 0.0,
                        'used_holiday_hours': 0.0,
                        'total_hours_worked': 0.0,
                        'role': role
                    }
                    # Initialize schedule for new employee across all weeks
                    for week_key in st.session_state.schedule:
                        for day in st.session_state.days:
                            st.session_state.schedule[week_key][day][full_name] = {'start': '', 'end': '', 'break_minutes': 0, 'locked': False}
                    st.success("Employee added!")
                    st.rerun()
                else:
                    st.error("Duplicate employee.")
        
        # Display employees (hide sensitive info for managers)
        if st.session_state.employees:
            emp_data = {k: v.copy() for k, v in st.session_state.employees.items()}
            if st.session_state.user_role == 'manager':
                for d in emp_data.values():
                    d.pop('wage', None)
                    d.pop('password', None)
            emp_df = pd.DataFrame.from_dict(emp_data, orient='index')
            st.dataframe(emp_df)

if page == "Schedule" or page == "View Schedule":
    view_only = page == "View Schedule" or st.session_state.user_role == 'employee'
    st.title("Schedule")
    
    # Week navigation
    current_week_start = datetime.strptime(st.session_state.current_week_start, '%Y-%m-%d')
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous Week"):
            prev_week = current_week_start - timedelta(days=7)
            st.session_state.current_week_start = prev_week.strftime('%Y-%m-%d')
            st.rerun()
    with col2:
        st.write(f"Week: {st.session_state.current_week_start} to {(current_week_start + timedelta(days=6)).strftime('%Y-%m-%d')}")
    with col3:
        if st.button("Next Week"):
            next_week = current_week_start + timedelta(days=7)
            st.session_state.current_week_start = next_week.strftime('%Y-%m-%d')
            st.rerun()
    
    week_key = st.session_state.current_week_start
    if week_key not in st.session_state.schedule:
        st.session_state.schedule[week_key] = {day: {emp: {'start': '', 'end': '', 'break_minutes': 0, 'locked': False} for emp in st.session_state.employees} for day in st.session_state.days}
    if week_key not in st.session_state.holidays:
        st.session_state.holidays[week_key] = {day: [] for day in st.session_state.days}
    
    # Function to calculate hours and cost for the week
    def calculate_hours_cost(full_name):
        total_hours = 0.0
        for day in st.session_state.days:
            sch = st.session_state.schedule[week_key].get(day, {}).get(full_name, {})
            if 'start' in sch and sch['start'] and 'end' in sch and sch['end']:
                start_time = datetime.strptime(sch['start'], '%H:%M')
                end_time = datetime.strptime(sch['end'], '%H:%M')
                shift_h = (end_time - start_time).total_seconds() / 3600
                total_hours += max(0, shift_h - sch.get('break_minutes', 0) / 60)
        wage = st.session_state.employees[full_name]['wage']
        cost = total_hours * wage
        return total_hours, cost
    
    for area in st.session_state.areas:
        st.subheader(area)
        area_type = 'BOH' if 'BOH' in area else 'FOH'  # Fixed mapping
        area_emps = [name for name, d in st.session_state.employees.items() if d['type'] == area_type]
        if area_emps or not view_only:
            data = {" ": []}  # For initials/photo placeholder
            for day in st.session_state.days:
                data[day] = []
            for emp in area_emps:
                initials = ''.join(word[0].upper() for word in emp.split())
                hours, cost = calculate_hours_cost(emp)
                data[" "].append(f"{initials}\n{hours:.0f}h £{cost:.2f}")
                for day in st.session_state.days:
                    sch = st.session_state.schedule[week_key].get(day, {}).get(emp, {})
                    cell = f"{sch.get('start', '')}-{sch.get('end', '')} ({sch.get('break_minutes', 0)}m)" if sch.get('start') else '--'
                    if sch.get('locked', False):
                        cell += ' LOCKED'
                    if emp in st.session_state.holidays[week_key].get(day, []):
                        cell = 'Time off'
                    data[day].append(cell)
            df = pd.DataFrame(data)
            if view_only:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                edited_df = st.data_editor(df, use_container_width=True, hide_index=True, disabled=[" "], key=f"schedule_editor_{area}_{week_key}")
                # Update from edits
                for i, row in edited_df.iterrows():
                    emp = area_emps[i]
                    for day in st.session_state.days:
                        cell = row[day]
                        if cell != '--' and 'Time off' not in cell:
                            try:
                                parts = cell.split(' ')
                                time_range = parts[0].split('-')
                                break_str = parts[1].strip('()m')
                                break_min = int(break_str) if break_str.isdigit() else 0
                                locked = 'LOCKED' in cell
                                st.session_state.schedule[week_key][day][emp] = {'start': time_range[0], 'end': time_range[1], 'break_minutes': break_min, 'locked': locked}
                            except:
                                pass
            
        if not view_only:
            with st.expander(f"Add Shift to {area}"):
                emp = st.selectbox("Select Employee", area_emps or ["No employees in this area"], key=f"add_emp_{area}")
                if emp == "No employees in this area":
                    st.warning("Add employees first in the Employees page.")
                else:
                    day = st.selectbox("Day", st.session_state.days, key=f"add_day_{area}")
                    start = st.time_input("Start Time", key=f"add_start_{area}")
                    end = st.time_input("End Time", key=f"add_end_{area}")
                    break_min = st.number_input("Break Minutes", min_value=0, key=f"add_break_{area}")
                    locked = st.checkbox("Locked", key=f"add_locked_{area}")
                    if st.button("Save Shift", key=f"save_shift_{area}"):
                        st.session_state.schedule[week_key][day][emp] = {'start': start.strftime('%H:%M'), 'end': end.strftime('%H:%M'), 'break_minutes': break_min, 'locked': locked}
                        st.success("Shift added!")
                        st.rerun()

elif page == "Reports":
    if st.session_state.user_role in ['admin', 'manager']:
        st.title("Reports")
        
        st.subheader("Holiday Entitlements")
        for full_name, data in st.session_state.employees.items():
            if data['employment_type'] == 'full_time':
                remaining = data['holiday_entitlement_days'] - data['holiday_taken_days']
                st.write(f"{full_name}: Full-time - Remaining: {remaining} days")
            else:
                remaining = data['accrued_holiday_hours'] - data['used_holiday_hours']
                st.write(f"{full_name}: Hourly - Remaining: {remaining:.2f} hours")
        
        st.subheader("Weekly Pay")
        week_key = st.session_state.current_week_start
        for full_name, data in st.session_state.employees.items():
            paid_hours = 0.0
            holiday_pay = 0.0
            for day in st.session_state.days:
                sch = st.session_state.schedule.get(week_key, {}).get(day, {}).get(full_name, {})
                if 'start' in sch and sch['start']:
                    start = datetime.strptime(sch['start'], '%H:%M')
                    end = datetime.strptime(sch['end'], '%H:%M')
                    shift_h = (end - start).total_seconds() / 3600
                    paid_hours += max(0, shift_h - sch['break_minutes'] / 60)
                if full_name in st.session_state.holidays.get(week_key, {}).get(day, []):
                    holiday_pay += st.session_state.standard_day_hours * data['wage']
            shift_pay = paid_hours * data['wage']
            total_pay = shift_pay + holiday_pay
            st.write(f"{full_name}: Shift £{shift_pay:.2f} ({paid_hours:.2f} hours) + Holiday £{holiday_pay:.2f} = £{total_pay:.2f}")

elif page == "Request Holiday":
    st.title("Request Holiday")
    week_key = st.session_state.current_week_start
    requested_day = st.selectbox("Select Day", st.session_state.days)
    if st.button("Request Time Off"):
        if st.session_state.current_user not in st.session_state.holidays.get(week_key, {}).get(requested_day, []):
            if week_key not in st.session_state.holidays:
                st.session_state.holidays[week_key] = {day: [] for day in st.session_state.days}
            st.session_state.holidays[week_key][requested_day].append(st.session_state.current_user)
            # Deduct entitlement (admin can approve)
            data = st.session_state.employees[st.session_state.current_user]
            if data['employment_type'] == 'full_time':
                data['holiday_taken_days'] += 1
            else:
                data['used_holiday_hours'] += st.session_state.standard_day_hours
            st.success(f"Requested time off on {requested_day}. Awaiting approval.")

# Save/Load/Finalize/Clear (admin/manager only)
if st.session_state.user_role in ['admin', 'manager']:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Save All"):
            data = {
                "employees": st.session_state.employees,
                "pending_employees": st.session_state.pending_employees,
                "schedule": st.session_state.schedule,
                "holidays": st.session_state.holidays
            }
            with open("rota_data.json", "w") as f:
                json.dump(data, f)
            st.success("Saved!")
    with col2:
        if st.button("Load All"):
            if os.path.exists("rota_data.json"):
                with open("rota_data.json", "r") as f:
                    data = json.load(f)
                st.session_state.employees = data.get("employees", {})
                st.session_state.pending_employees = data.get("pending_employees", {})
                st.session_state.schedule = data.get("schedule", {})
                st.session_state.holidays = data.get("holidays", {})
                st.success("Loaded!")
            else:
                st.error("No save file.")
    with col3:
        if st.button("Finalize Week"):
            week_key = st.session_state.current_week_start
            for full_name, data in st.session_state.employees.items():
                week_hours = 0.0
                for day in st.session_state.days:
                    sch = st.session_state.schedule.get(week_key, {}).get(day, {}).get(full_name, {})
                    if 'start' in sch and sch['start']:
                        start = datetime.strptime(sch['start'], '%H:%M')
                        end = datetime.strptime(sch['end'], '%H:%M')
                        shift_h = (end - start).total_seconds() / 3600
                        week_hours += max(0, shift_h - sch['break_minutes'] / 60)
                data['total_hours_worked'] += week_hours
                if data['employment_type'] == 'hourly':
                    data['accrued_holiday_hours'] += week_hours * st.session_state.accrual_rate
            st.success("Week finalized!")
    with col4:
        if st.button("Clear Schedule"):
            week_key = st.session_state.current_week_start
            st.session_state.schedule[week_key] = {day: {emp: {'start': '', 'end': '', 'break_minutes': 0, 'locked': False} for emp in st.session_state.employees} for day in st.session_state.days}
            st.session_state.holidays[week_key] = {day: [] for day in st.session_state.days}
            st.success("Schedule cleared!")
