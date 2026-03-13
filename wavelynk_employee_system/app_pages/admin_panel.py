import secrets
import string

import pandas as pd
import streamlit as st

from modules.audit import log_audit
from modules.employee import (
    get_all_employees,
    get_managers,
    create_employee,
    update_employee_status,
    reset_employee_password,
    update_employee_manager,
    get_team_members_by_manager,
    reassign_team_members,
    update_employee_role,
    get_employee_by_id,
    update_employee_contact,
    update_employee_role_department,
)
from modules.leave import (
    get_all_leave_requests,
    get_leave_requests_for_manager,
    update_leave_status,
    get_leave_types,
    add_leave_type,
    remove_leave_type,
)
from modules.policies import get_policy, update_policy
from modules.holidays import (
    list_holidays,
    add_holiday,
    delete_holiday,
    import_country_holidays,
    clear_country_holidays,
    update_holiday_optional_flag,
)
from modules.masters import (
    get_roles,
    get_active_roles,
    add_role,
    remove_role,
    get_departments,
    get_active_departments,
    add_department,
    remove_department,
)
from modules.email_service import send_new_employee_welcome_email
from utils import is_strong_password


def refresh_logged_in_user_if_needed(updated_user_id: int):
    if st.session_state.get("user") and st.session_state.user["id"] == updated_user_id:
        row = get_employee_by_id(updated_user_id)
        if row:
            st.session_state.user = {
                "id": row["id"],
                "employee_id": row["employee_id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "role": row["role"],
                "department": row["department"],
                "phone": row["phone"],
                "email": row["email"],
                "joining_date": row["joining_date"],
                "employment_status": row["employment_status"],
                "manager_name": row["manager_name"],
                "manager_id": row["manager_id"],
            }


def generate_temp_password(length: int = 12) -> str:
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    all_chars = uppercase + lowercase + digits + special

    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]

    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def show(user):
    allowed_roles = ["Admin", "HR", "Manager", "Team Lead", "HOD"]
    if user["role"] not in allowed_roles:
        st.warning("You do not have access to this page.")
        return

    is_admin_hr = user["role"] in ["Admin", "HR"]

    st.markdown("<div class='page-title'>Admin Panel</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Corporate control for employees, managers, leave types, roles, departments, approvals, policy and holidays.</div>",
        unsafe_allow_html=True,
    )

    if is_admin_hr:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "Employees",
                "Managers",
                "Leave Types",
                "Roles & Departments",
                "Leave Requests",
                "Policy & Holidays",
            ]
        )
    else:
        tab5 = st.tabs(["Leave Requests"])[0]

    # =========================================================
    # TAB 1 - EMPLOYEES
    # =========================================================
    if is_admin_hr:
        with tab1:
            st.subheader("Create Employee")
            st.info(
                "Username will be auto-generated as the Employee ID. New Employee IDs start from 200000. Temporary password will be auto-generated and sent by email."
            )

            role_rows = get_active_roles()
            dept_rows = get_active_departments()

            role_options = (
                [r["role_name"] for r in role_rows] if role_rows else ["Employee"]
            )
            dept_options = (
                [d["department_name"] for d in dept_rows]
                if dept_rows
                else ["Operations"]
            )
            manager_rows = get_managers()

            manager_labels = ["None"] + [
                f"{m['employee_id']} - {m['full_name']} ({m['role']})"
                for m in manager_rows
            ]
            manager_map = {
                f"{m['employee_id']} - {m['full_name']} ({m['role']})": m["id"]
                for m in manager_rows
            }

            with st.form("create_employee_form"):
                full_name = st.text_input("Full Name")
                role = st.selectbox("Role", role_options)
                department = st.selectbox("Department", dept_options)
                phone = st.text_input(
                    "Phone Number (with country code)", placeholder="+919876543210"
                )
                email = st.text_input("Email")
                joining_date = st.date_input("Joining Date")
                selected_manager = st.selectbox("Manager", manager_labels)
                submit = st.form_submit_button(
                    "Create Employee", use_container_width=True
                )

                if submit:
                    if not full_name.strip():
                        st.error("Full Name is required.")
                    else:
                        try:
                            manager_id = (
                                None
                                if selected_manager == "None"
                                else manager_map[selected_manager]
                            )

                            temp_password = generate_temp_password()

                            emp_id = create_employee(
                                "",
                                full_name.strip(),
                                role,
                                department,
                                phone.strip(),
                                email.strip(),
                                str(joining_date),
                                manager_id,
                                temp_password,
                            )

                            email_ok, email_msg = send_new_employee_welcome_email(
                                email.strip(),
                                full_name.strip(),
                                emp_id,
                                emp_id,
                                temp_password,
                                role,
                                department,
                                str(joining_date),
                                (
                                    None
                                    if selected_manager == "None"
                                    else selected_manager
                                ),
                            )

                            log_audit(
                                action="CREATE_EMPLOYEE",
                                actor_name=user["full_name"],
                                target_name=full_name.strip(),
                                details=f"Employee ID: {emp_id}, Username: {emp_id}, Role: {role}, Department: {department}",
                            )

                            if email_ok:
                                st.success(
                                    f"Employee created successfully. Employee ID / Username: {emp_id}. Welcome email sent."
                                )
                            else:
                                st.warning(
                                    f"Employee created successfully. Employee ID / Username: {emp_id}. But welcome email failed: {email_msg}"
                                )

                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not create employee: {e}")

            st.subheader("Employees List")
            emp_df = pd.DataFrame(get_all_employees())
            st.dataframe(emp_df, use_container_width=True)

            if not emp_df.empty:
                selected_id = st.selectbox(
                    "Select Employee User ID",
                    emp_df["id"].tolist(),
                    format_func=lambda x: f"{emp_df.loc[emp_df['id'] == x, 'employee_id'].values[0]} - {emp_df.loc[emp_df['id'] == x, 'full_name'].values[0]}",
                    key="emp_status_id",
                )

                selected_emp_row = emp_df[emp_df["id"] == selected_id].iloc[0]
                selected_emp_role = selected_emp_row["role"]
                selected_emp_name = selected_emp_row["full_name"]

                status = st.selectbox(
                    "Employment Status",
                    ["Active", "On Leave", "Resigned", "Terminated", "Suspended"],
                    key="employment_status_select",
                )

                team_members = (
                    get_team_members_by_manager(selected_id)
                    if selected_emp_role in ["Manager", "Team Lead", "HOD"]
                    else []
                )

                show_reassign = (
                    selected_emp_role in ["Manager", "Team Lead", "HOD"]
                    and status in ["Resigned", "Terminated", "Suspended"]
                    and len(team_members) > 0
                )

                new_manager_id = None

                if show_reassign:
                    st.warning(
                        f"This manager currently has {len(team_members)} team member(s). "
                        "Please reassign them before marking this manager inactive."
                    )

                    team_df = pd.DataFrame(team_members)
                    st.dataframe(team_df, use_container_width=True)

                    reassignment_rows = [
                        m for m in get_managers() if m["id"] != selected_id
                    ]

                    reassignment_labels = ["Keep Unassigned"] + [
                        f"{m['employee_id']} - {m['full_name']} ({m['role']})"
                        for m in reassignment_rows
                    ]
                    reassignment_map = {
                        f"{m['employee_id']} - {m['full_name']} ({m['role']})": m["id"]
                        for m in reassignment_rows
                    }

                    selected_reassignment = st.selectbox(
                        "Reassign Team Members To",
                        reassignment_labels,
                        key="reassign_manager_select",
                    )

                    if selected_reassignment != "Keep Unassigned":
                        new_manager_id = reassignment_map[selected_reassignment]

                if st.button("Update Employment Status", use_container_width=True):
                    try:
                        active_flag = 1 if status in ["Active", "On Leave"] else 0

                        if show_reassign:
                            reassign_team_members(selected_id, new_manager_id)

                        update_employee_status(selected_id, status, active_flag)
                        refresh_logged_in_user_if_needed(selected_id)

                        log_audit(
                            action="UPDATE_EMPLOYEE_STATUS",
                            actor_name=user["full_name"],
                            target_name=selected_emp_name,
                            details=f"New status: {status}, Active flag: {active_flag}",
                        )

                        st.success("Employee status updated successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update status: {e}")

                st.markdown("---")
                st.subheader("Update Employee Contact Details")

                with st.form("update_employee_contact_form"):
                    phone_update = st.text_input(
                        "Update Phone Number",
                        value=str(selected_emp_row["phone"] or ""),
                        key="update_phone_number",
                    )
                    email_update = st.text_input(
                        "Update Email",
                        value=str(selected_emp_row["email"] or ""),
                        key="update_email_value",
                    )
                    update_contact_submit = st.form_submit_button(
                        "Update Contact Details", use_container_width=True
                    )

                    if update_contact_submit:
                        try:
                            update_employee_contact(
                                selected_id,
                                phone_update.strip(),
                                email_update.strip(),
                            )
                            refresh_logged_in_user_if_needed(selected_id)

                            log_audit(
                                action="UPDATE_EMPLOYEE_CONTACT",
                                actor_name=user["full_name"],
                                target_name=selected_emp_name,
                                details=f"Updated phone/email for employee ID {selected_emp_row['employee_id']}",
                            )

                            st.success("Employee contact details updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not update contact details: {e}")

                st.markdown("---")
                st.subheader("Update Employee Role & Department")

                current_role_index = (
                    role_options.index(selected_emp_row["role"])
                    if selected_emp_row["role"] in role_options
                    else 0
                )
                current_dept_index = (
                    dept_options.index(selected_emp_row["department"])
                    if selected_emp_row["department"] in dept_options
                    else 0
                )

                with st.form("update_employee_role_department_form"):
                    updated_role = st.selectbox(
                        "Update Role",
                        role_options,
                        index=current_role_index,
                        key="update_role_value",
                    )
                    updated_department = st.selectbox(
                        "Update Department",
                        dept_options,
                        index=current_dept_index,
                        key="update_department_value",
                    )
                    update_role_department_submit = st.form_submit_button(
                        "Update Role & Department", use_container_width=True
                    )

                    if update_role_department_submit:
                        try:
                            update_employee_role_department(
                                selected_id,
                                updated_role,
                                updated_department,
                            )
                            refresh_logged_in_user_if_needed(selected_id)

                            updated_user = get_employee_by_id(selected_id)

                            log_audit(
                                action="UPDATE_EMPLOYEE_ROLE_DEPARTMENT",
                                actor_name=user["full_name"],
                                target_name=selected_emp_name,
                                details=f"Role: {updated_role}, Department: {updated_department}",
                            )

                            if (
                                updated_user
                                and updated_user["role"] == updated_role
                                and updated_user["department"] == updated_department
                            ):
                                st.success(
                                    "Employee role and department updated successfully."
                                )
                            else:
                                st.error(
                                    "Update did not reflect in database. Please try again."
                                )

                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not update role and department: {e}")

                st.markdown("---")
                st.subheader("Reset Employee Password")
                st.info(
                    "Temporary password must be strong: minimum 8 characters with uppercase, lowercase, number, and special character."
                )

                new_password = st.text_input(
                    "New Temporary Password",
                    type="password",
                    key="reset_password_input",
                )

                if st.button("Reset Employee Password", use_container_width=True):
                    final_password = new_password.strip()

                    if not final_password:
                        st.error("Enter a new password.")
                    else:
                        strong, errors = is_strong_password(final_password)
                        if not strong:
                            st.error(" ".join(errors))
                        else:
                            try:
                                reset_employee_password(selected_id, final_password)

                                log_audit(
                                    action="RESET_EMPLOYEE_PASSWORD",
                                    actor_name=user["full_name"],
                                    target_name=selected_emp_name,
                                    details="Password reset from Admin Panel",
                                )

                                st.success("Password reset successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not reset password: {e}")

    # =========================================================
    # TAB 2 - MANAGERS
    # =========================================================
    if is_admin_hr:
        with tab2:
            st.subheader("Change Manager for Employee")

            emp_df = pd.DataFrame(get_all_employees())

            if not emp_df.empty:
                employee_options = emp_df[emp_df["role"] != "Admin"]
                manager_rows = get_managers()

                if employee_options.empty:
                    st.info("No employees available.")
                elif not manager_rows:
                    st.info("No managers available.")
                else:
                    employee_id = st.selectbox(
                        "Select Employee",
                        employee_options["id"].tolist(),
                        format_func=lambda x: f"{employee_options.loc[employee_options['id'] == x, 'employee_id'].values[0]} - {employee_options.loc[employee_options['id'] == x, 'full_name'].values[0]}",
                        key="manager_employee",
                    )

                    selected_employee_row = employee_options[
                        employee_options["id"] == employee_id
                    ].iloc[0]
                    selected_employee_name = selected_employee_row["full_name"]

                    manager_labels = ["None"] + [
                        f"{m['employee_id']} - {m['full_name']} ({m['role']})"
                        for m in manager_rows
                    ]
                    manager_map = {
                        f"{m['employee_id']} - {m['full_name']} ({m['role']})": m["id"]
                        for m in manager_rows
                    }

                    selected_manager = st.selectbox(
                        "Select Manager",
                        manager_labels,
                        key="manager_name_select",
                    )

                    if st.button("Update Manager", use_container_width=True):
                        try:
                            manager_id = (
                                None
                                if selected_manager == "None"
                                else manager_map[selected_manager]
                            )
                            update_employee_manager(employee_id, manager_id)
                            refresh_logged_in_user_if_needed(employee_id)

                            log_audit(
                                action="UPDATE_EMPLOYEE_MANAGER",
                                actor_name=user["full_name"],
                                target_name=selected_employee_name,
                                details=f"Assigned manager: {selected_manager}",
                            )

                            st.success("Manager updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not update manager: {e}")

    # =========================================================
    # TAB 3 - LEAVE TYPES
    # =========================================================
    if is_admin_hr:
        with tab3:
            st.subheader("Add Leave Type")

            with st.form("leave_type_form"):
                leave_name = st.text_input("Leave Type Name")
                yearly_quota = st.number_input("Yearly Quota", min_value=0, value=10)
                submit_leave_type = st.form_submit_button(
                    "Add Leave Type", use_container_width=True
                )

                if submit_leave_type:
                    if not leave_name.strip():
                        st.error("Enter leave type name.")
                    else:
                        try:
                            add_leave_type(leave_name.strip(), int(yearly_quota))

                            log_audit(
                                action="ADD_LEAVE_TYPE",
                                actor_name=user["full_name"],
                                target_name=leave_name.strip(),
                                details=f"Yearly quota: {int(yearly_quota)}",
                            )

                            st.success("Leave type added successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not add leave type: {e}")

            st.subheader("Existing Leave Types")
            leave_df = pd.DataFrame(get_leave_types())
            st.dataframe(leave_df, use_container_width=True)

            if not leave_df.empty:
                leave_id = st.selectbox(
                    "Select Leave Type ID to Delete",
                    leave_df["id"].tolist(),
                    format_func=lambda x: f"{leave_df.loc[leave_df['id'] == x, 'leave_name'].values[0]} (ID: {x})",
                    key="leave_type_delete_select",
                )

                if st.button("Delete Leave Type", use_container_width=True):
                    try:
                        leave_name = leave_df.loc[
                            leave_df["id"] == leave_id, "leave_name"
                        ].values[0]
                        remove_leave_type(leave_id)

                        log_audit(
                            action="DELETE_LEAVE_TYPE",
                            actor_name=user["full_name"],
                            target_name=str(leave_name),
                            details=f"Deleted leave type ID: {leave_id}",
                        )

                        st.success("Leave type deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete leave type: {e}")

    # =========================================================
    # TAB 4 - ROLES & DEPARTMENTS
    # =========================================================
    if is_admin_hr:
        with tab4:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Roles")

                with st.form("add_role_form"):
                    role_name = st.text_input("New Role Name")
                    add_role_btn = st.form_submit_button(
                        "Add Role", use_container_width=True
                    )

                    if add_role_btn:
                        if not role_name.strip():
                            st.error("Enter role name.")
                        else:
                            try:
                                add_role(role_name.strip())

                                log_audit(
                                    action="ADD_ROLE",
                                    actor_name=user["full_name"],
                                    target_name=role_name.strip(),
                                    details="Role added from Admin Panel",
                                )

                                st.success("Role added successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not add role: {e}")

                role_df = pd.DataFrame(get_roles())
                st.dataframe(role_df, use_container_width=True)

                if not role_df.empty:
                    role_id = st.selectbox(
                        "Select Role ID to Delete",
                        role_df["id"].tolist(),
                        format_func=lambda x: f"{role_df.loc[role_df['id'] == x, 'role_name'].values[0]} (ID: {x})",
                        key="role_delete_id",
                    )

                    if st.button("Delete Role", use_container_width=True):
                        try:
                            role_name = role_df.loc[
                                role_df["id"] == role_id, "role_name"
                            ].values[0]
                            remove_role(role_id)

                            log_audit(
                                action="DELETE_ROLE",
                                actor_name=user["full_name"],
                                target_name=str(role_name),
                                details=f"Deleted role ID: {role_id}",
                            )

                            st.success("Role deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not delete role: {e}")

            with col2:
                st.subheader("Departments")

                with st.form("add_department_form"):
                    department_name = st.text_input("New Department Name")
                    add_department_btn = st.form_submit_button(
                        "Add Department", use_container_width=True
                    )

                    if add_department_btn:
                        if not department_name.strip():
                            st.error("Enter department name.")
                        else:
                            try:
                                add_department(department_name.strip())

                                log_audit(
                                    action="ADD_DEPARTMENT",
                                    actor_name=user["full_name"],
                                    target_name=department_name.strip(),
                                    details="Department added from Admin Panel",
                                )

                                st.success("Department added successfully.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not add department: {e}")

                dept_df = pd.DataFrame(get_departments())
                st.dataframe(dept_df, use_container_width=True)

                if not dept_df.empty:
                    department_id = st.selectbox(
                        "Select Department ID to Delete",
                        dept_df["id"].tolist(),
                        format_func=lambda x: f"{dept_df.loc[dept_df['id'] == x, 'department_name'].values[0]} (ID: {x})",
                        key="department_delete_id",
                    )

                    if st.button("Delete Department", use_container_width=True):
                        try:
                            department_name = dept_df.loc[
                                dept_df["id"] == department_id, "department_name"
                            ].values[0]
                            remove_department(department_id)

                            log_audit(
                                action="DELETE_DEPARTMENT",
                                actor_name=user["full_name"],
                                target_name=str(department_name),
                                details=f"Deleted department ID: {department_id}",
                            )

                            st.success("Department deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not delete department: {e}")

    # =========================================================
    # TAB 5 - LEAVE REQUESTS
    # =========================================================
    with tab5:
        st.subheader("Leave Requests")

        if is_admin_hr:
            leaves = pd.DataFrame(get_all_leave_requests())
        else:
            leaves = pd.DataFrame(get_leave_requests_for_manager(user["id"]))

        if leaves.empty:
            st.info("No leave requests available.")
        else:
            st.dataframe(leaves, use_container_width=True)

            leave_id = st.selectbox(
                "Select Leave Request ID",
                leaves["id"].tolist(),
                format_func=lambda x: f"Request ID {x} - {leaves.loc[leaves['id'] == x, 'full_name'].values[0]}",
                key="leave_request_id_select",
            )

            new_status = st.selectbox(
                "New Status", ["Approved", "Rejected"], key="leave_status_select"
            )

            if st.button("Update Leave Status", use_container_width=True):
                try:
                    leave_emp_name = leaves.loc[
                        leaves["id"] == leave_id, "full_name"
                    ].values[0]

                    update_leave_status(leave_id, new_status, user["full_name"])

                    log_audit(
                        action="UPDATE_LEAVE_STATUS",
                        actor_name=user["full_name"],
                        target_name=str(leave_emp_name),
                        details=f"Leave request ID {leave_id} updated to {new_status}",
                    )

                    st.success("Leave request updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not update leave request: {e}")

    # =========================================================
    # TAB 6 - POLICY & HOLIDAYS
    # =========================================================
    if is_admin_hr:
        with tab6:
            st.subheader("Company Policy")

            policy = get_policy()

            with st.form("policy_form"):
                login_time = st.text_input(
                    "Login Time (HH:MM)", value=policy["login_time"]
                )
                logout_time = st.text_input(
                    "Logout Time (HH:MM)", value=policy["logout_time"]
                )
                login_grace = st.number_input(
                    "Login Grace Minutes",
                    min_value=0,
                    value=int(policy["login_grace_minutes"]),
                )
                logout_grace = st.number_input(
                    "Logout Grace Minutes",
                    min_value=0,
                    value=int(policy["logout_grace_minutes"]),
                )
                tea_break = st.number_input(
                    "Tea Break Minutes",
                    min_value=0,
                    value=int(policy["tea_break_minutes"]),
                )
                lunch_break = st.number_input(
                    "Lunch Break Minutes",
                    min_value=0,
                    value=int(policy["lunch_break_minutes"]),
                )
                personal_break = st.number_input(
                    "Personal Break Minutes",
                    min_value=0,
                    value=int(policy["personal_break_minutes"]),
                )
                submit_policy = st.form_submit_button(
                    "Save Policy", use_container_width=True
                )

                if submit_policy:
                    try:
                        update_policy(
                            login_time,
                            logout_time,
                            int(login_grace),
                            int(logout_grace),
                            int(tea_break),
                            int(lunch_break),
                            int(personal_break),
                        )

                        log_audit(
                            action="UPDATE_POLICY",
                            actor_name=user["full_name"],
                            target_name="Company Policy",
                            details=f"Login {login_time}, Logout {logout_time}",
                        )

                        st.success("Policy updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update policy: {e}")

            st.subheader("Manual Holiday Add")

            with st.form("holiday_form"):
                holiday_name = st.text_input("Holiday Name")
                holiday_date = st.date_input("Holiday Date")
                optional_holiday = st.checkbox("Optional Holiday")
                submit_holiday = st.form_submit_button(
                    "Add Manual Holiday", use_container_width=True
                )

                if submit_holiday:
                    if not holiday_name.strip():
                        st.error("Holiday name is required.")
                    else:
                        try:
                            added = add_holiday(
                                holiday_name.strip(),
                                str(holiday_date),
                                "MANUAL",
                                1 if optional_holiday else 0,
                            )
                            if added:
                                log_audit(
                                    action="ADD_HOLIDAY",
                                    actor_name=user["full_name"],
                                    target_name=holiday_name.strip(),
                                    details=f"Date: {holiday_date}, Optional: {optional_holiday}",
                                )
                                st.success("Holiday added.")
                            else:
                                st.warning("Holiday already exists.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not add holiday: {e}")

            st.subheader("Import Country Holidays Automatically")

            country_options = {
                "India": "IN",
                "United States": "US",
                "United Kingdom": "GB",
                "United Arab Emirates": "AE",
                "Singapore": "SG",
                "Australia": "AU",
                "Canada": "CA",
                "Germany": "DE",
                "France": "FR",
                "Japan": "JP",
            }

            with st.form("import_country_holiday_form"):
                country_name = st.selectbox(
                    "Select Country", list(country_options.keys())
                )
                holiday_year = st.number_input(
                    "Year", min_value=2000, max_value=2100, value=2026
                )
                submit_import = st.form_submit_button(
                    "Import Country Holidays", use_container_width=True
                )

                if submit_import:
                    try:
                        country_code = country_options[country_name]
                        result = import_country_holidays(
                            country_code, int(holiday_year)
                        )

                        log_audit(
                            action="IMPORT_COUNTRY_HOLIDAYS",
                            actor_name=user["full_name"],
                            target_name=country_name,
                            details=f"Year: {holiday_year}, Inserted: {result['inserted']}, Skipped: {result['skipped']}",
                        )

                        st.success(
                            f"{country_name}: imported {result['inserted']} holidays, skipped {result['skipped']} existing holidays."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not import holidays: {e}")

            st.subheader("Delete Imported Country Holidays by Year")

            with st.form("clear_country_holiday_form"):
                delete_country_name = st.selectbox(
                    "Select Country to Clear",
                    list(country_options.keys()),
                    key="delete_country_name",
                )
                delete_year = st.number_input(
                    "Year to Clear",
                    min_value=2000,
                    max_value=2100,
                    value=2026,
                    key="delete_year",
                )
                submit_clear = st.form_submit_button(
                    "Delete Country Holidays", use_container_width=True
                )

                if submit_clear:
                    try:
                        delete_country_code = country_options[delete_country_name]
                        clear_country_holidays(delete_country_code, int(delete_year))

                        log_audit(
                            action="CLEAR_COUNTRY_HOLIDAYS",
                            actor_name=user["full_name"],
                            target_name=delete_country_name,
                            details=f"Year: {delete_year}",
                        )

                        st.success(
                            f"{delete_country_name} holidays deleted for {delete_year}."
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete country holidays: {e}")

            st.subheader("All Holidays")

            holiday_df = pd.DataFrame(list_holidays())
            if not holiday_df.empty and "optional_flag" in holiday_df.columns:
                holiday_df["Holiday Type"] = holiday_df["optional_flag"].apply(
                    lambda x: "Optional" if int(x) == 1 else "Mandatory"
                )

            st.dataframe(holiday_df, use_container_width=True)

            if not holiday_df.empty:
                holiday_id = st.selectbox(
                    "Select Holiday ID",
                    holiday_df["id"].tolist(),
                    format_func=lambda x: f"{holiday_df.loc[holiday_df['id'] == x, 'holiday_name'].values[0]} - {holiday_df.loc[holiday_df['id'] == x, 'holiday_date'].values[0]} ({holiday_df.loc[holiday_df['id'] == x, 'country_code'].values[0]})",
                    key="holiday_id_select",
                )

                holiday_type = st.selectbox(
                    "Set Holiday Type",
                    ["Mandatory", "Optional"],
                    key="holiday_type_select",
                )

                if st.button("Update Holiday Type", use_container_width=True):
                    try:
                        holiday_name = holiday_df.loc[
                            holiday_df["id"] == holiday_id, "holiday_name"
                        ].values[0]
                        update_holiday_optional_flag(
                            holiday_id,
                            1 if holiday_type == "Optional" else 0,
                        )

                        log_audit(
                            action="UPDATE_HOLIDAY_TYPE",
                            actor_name=user["full_name"],
                            target_name=str(holiday_name),
                            details=f"Holiday type set to {holiday_type}",
                        )

                        st.success("Holiday type updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update holiday type: {e}")

                if st.button("Delete Selected Holiday", use_container_width=True):
                    try:
                        holiday_name = holiday_df.loc[
                            holiday_df["id"] == holiday_id, "holiday_name"
                        ].values[0]
                        delete_holiday(holiday_id)

                        log_audit(
                            action="DELETE_HOLIDAY",
                            actor_name=user["full_name"],
                            target_name=str(holiday_name),
                            details=f"Deleted holiday ID: {holiday_id}",
                        )

                        st.success("Holiday deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not delete holiday: {e}")
