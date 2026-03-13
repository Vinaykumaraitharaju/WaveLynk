import pandas as pd
import streamlit as st

from modules.audit import log_audit
from modules.leave import get_leave_requests_for_manager, update_leave_status


def show(user):
    if user["role"] not in ["Manager", "Team Lead", "HOD"]:
        st.warning("You do not have access to this page.")
        return

    st.markdown(
        "<div class='page-title'>Team Leave Approvals</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='page-subtitle'>Review and approve leave requests submitted by your team members.</div>",
        unsafe_allow_html=True,
    )

    leaves = pd.DataFrame(get_leave_requests_for_manager(user["id"]))

    if leaves.empty:
        st.info("No leave requests available for your team.")
        return

    pending_leaves = leaves[leaves["status"] == "Pending"].copy()
    history_leaves = leaves[leaves["status"] != "Pending"].copy()

    st.subheader("Pending Requests")

    if pending_leaves.empty:
        st.info("No pending leave requests.")
    else:
        st.dataframe(pending_leaves, use_container_width=True)

        leave_id = st.selectbox(
            "Select Pending Leave Request",
            pending_leaves["id"].tolist(),
            format_func=lambda x: (
                f"Request ID {x} - "
                f"{pending_leaves.loc[pending_leaves['id'] == x, 'full_name'].values[0]}"
            ),
            key="manager_leave_request_id_select",
        )

        new_status = st.selectbox(
            "Action",
            ["Approved", "Rejected"],
            key="manager_leave_status_select",
        )

        if st.button("Submit Approval Decision", use_container_width=True):
            try:
                leave_emp_name = pending_leaves.loc[
                    pending_leaves["id"] == leave_id, "full_name"
                ].values[0]

                update_leave_status(leave_id, new_status, user["full_name"])

                log_audit(
                    action="TEAM_LEAVE_APPROVAL",
                    actor_name=user["full_name"],
                    target_name=str(leave_emp_name),
                    details=f"Leave request ID {leave_id} updated to {new_status}",
                )

                st.success(f"Leave request {new_status.lower()} successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Could not update leave request: {e}")

    st.markdown("---")
    st.subheader("Leave Request History")

    if history_leaves.empty:
        st.info("No processed leave requests yet.")
    else:
        st.dataframe(history_leaves, use_container_width=True)
