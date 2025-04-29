# app.py
import streamlit as st
import pandas as pd
import csv
from io import StringIO

# --- Configuration ---
DATA_FILE = "Gantt Chart - KLIA (26 Mar 2025)(Project schedule).csv"
APP_TITLE = "WBS Progress Tracker - KLIA District Cooling System"

# --- Helper Functions ---

def parse_csv_to_wbs(csv_content):
    """Parses the specific CSV structure into a WBS list."""
    wbs = []
    current_parent = None
    parent_index = -1

    # Use StringIO to treat the string content like a file
    f = StringIO(csv_content)
    reader = csv.reader(f)

    try:
        # Skip header rows until we find the task data structure
        # This is brittle; assumes structure won't change drastically
        for _ in range(7): # Skip first 7 rows based on observed format
             next(reader)

        row_num = 8 # Start counting after skipped rows
        for row in reader:
            row_num += 1
            # Stop if we hit many empty rows (likely end of data)
            if not any(field.strip() for field in row):
                if current_parent: # Make sure last parent is added if file ends abruptly
                    pass # No action needed, parent was added when detected
                # Heuristic: stop after a few blank rows if needed, but pandas handles EOF better
                continue # Skip fully blank rows

            task_name = row[1].strip() if len(row) > 1 else ""
            task_id_indicator = row[0].strip() if len(row) > 0 else ""

            # Identify Parent Task (Phase row)
            # Heuristic: Parent rows have empty first column and "Phase" in the second.
            if not task_id_indicator and task_name.lower().startswith("phase"):
                parent_index += 1
                current_parent = {
                    "id": f"p_{parent_index}",
                    "name": task_name,
                    "level": 0,
                    "completed": False,
                    "expanded": True, # Start expanded
                    "children": []
                }
                wbs.append(current_parent)
                # print(f"Row {row_num}: Found Parent - {task_name}")

            # Identify Child Task
            # Heuristic: Child rows follow a parent, have something in col A or B, and are not phase rows
            elif current_parent and task_name and not task_name.lower().startswith("phase"):
                 # Ensure child is not another phase starting row
                 if not (not task_id_indicator and task_name.lower().startswith("phase")):
                    child_index = len(current_parent["children"])
                    child_task = {
                        "id": f"p_{parent_index}_c_{child_index}",
                        "name": task_name,
                        "level": 1,
                        "completed": False,
                        # Optional: Could parse progress % from col D if needed
                        # 'initial_progress': row[3] if len(row) > 3 else "0%"
                    }
                    current_parent["children"].append(child_task)
                    # print(f"Row {row_num}: Found Child - {task_name} (Parent: {current_parent['name']})")

    except StopIteration:
        st.warning("Reached end of CSV data while parsing.")
    except Exception as e:
        st.error(f"Error parsing CSV on row {row_num}: {e}")
        st.error(f"Problematic row data: {row}")
        return [] # Return empty list on error

    # Initial completion status sync after loading
    sync_parent_completion(wbs)
    return wbs

def sync_parent_completion(wbs_data):
    """Ensure parent completion status reflects children's status."""
    for parent in wbs_data:
        if parent.get("children"):
            all_children_complete = all(c.get("completed", False) for c in parent["children"])
            parent["completed"] = all_children_complete
        else:
             # If a parent has no children, its completion is just its own state
             # For now, assume parents *must* have children to be containers
             pass # Keep its existing state or default to False if needed

def calculate_progress(wbs_data):
    """Calculates overall progress based on completed child tasks."""
    total_children = 0
    completed_children = 0
    for parent in wbs_data:
        for child in parent.get("children", []):
            total_children += 1
            if child.get("completed", False):
                completed_children += 1
    return (completed_children / total_children) if total_children > 0 else 0

def initialize_state():
    """Initializes session state if not already done."""
    if "wbs_data" not in st.session_state:
        st.session_state.wbs_data = [] # Initialize as empty list
        try:
            # Read the entire file content first
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            # Now parse the content
            st.session_state.wbs_data = parse_csv_to_wbs(csv_content)
            if not st.session_state.wbs_data:
                 st.error(f"Could not load or parse data from {DATA_FILE}. Please check the file format.")

        except FileNotFoundError:
            st.error(f"Error: {DATA_FILE} not found. Please make sure it's in the same directory as the app.")
        except Exception as e:
            st.error(f"An unexpected error occurred loading the data: {e}")

    if "show_add_task_form" not in st.session_state:
        st.session_state.show_add_task_form = False

# --- Main App Logic ---
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

# Initialize state (loads data on first run)
initialize_state()

# Ensure wbs_data exists and is a list before proceeding
if not isinstance(st.session_state.get("wbs_data"), list):
    st.error("WBS data is not loaded correctly. Cannot proceed.")
    st.stop() # Halt execution if data isn't loaded

# --- Progress Overview ---
if st.session_state.wbs_data:
    progress_value = calculate_progress(st.session_state.wbs_data)
    st.progress(progress_value)
    st.metric("Overall Progress", f"{progress_value:.1%}")
else:
    st.info("No WBS data loaded to display progress.")

st.markdown("---") # Separator

# --- Add Task Section ---
if st.button("➕ Add New Task"):
    st.session_state.show_add_task_form = not st.session_state.show_add_task_form

if st.session_state.show_add_task_form:
    with st.form("add_task_form"):
        st.subheader("Add New Task")
        new_task_name = st.text_input("Task Name", key="new_task_name_input")
        new_task_type = st.radio("Task Type", ["Parent (Phase)", "Child"], key="new_task_type_radio")

        parent_options = {f"p_{i}": p["name"] for i, p in enumerate(st.session_state.wbs_data)}
        selected_parent_id = None
        if new_task_type == "Child":
            if not parent_options:
                 st.warning("Cannot add a child task as no parent tasks exist yet.")
                 target_parent_display = ""
            else:
                target_parent_display = st.selectbox(
                    "Add Child To Parent:",
                    options=list(parent_options.keys()),
                    format_func=lambda x: parent_options[x],
                    key="target_parent_select"
                )
                selected_parent_id = target_parent_display

        # Insertion Point Logic (Simplified: Add Parent at end, Add Child at end of selected Parent)
        # More complex insertion (before/after specific task) adds significant complexity
        if new_task_type == "Parent":
            st.info("New Parent tasks will be added at the end of the list.")
        elif new_task_type == "Child" and selected_parent_id:
             st.info(f"New Child task will be added at the end of '{parent_options[selected_parent_id]}'.")


        submitted = st.form_submit_button("Add Task")

        if submitted:
            if not new_task_name:
                st.warning("Please enter a task name.")
            else:
                if new_task_type == "Parent":
                    parent_index = len(st.session_state.wbs_data)
                    new_parent = {
                        "id": f"p_{parent_index}",
                        "name": new_task_name,
                        "level": 0,
                        "completed": False,
                        "expanded": True,
                        "children": []
                    }
                    st.session_state.wbs_data.append(new_parent)
                    st.success(f"Added Parent: {new_task_name}")
                    st.session_state.show_add_task_form = False # Hide form after adding
                    st.experimental_rerun()

                elif new_task_type == "Child":
                    if selected_parent_id:
                        # Find the parent in the list
                        parent_found = False
                        for i, p in enumerate(st.session_state.wbs_data):
                             if p["id"] == selected_parent_id:
                                parent_index = i
                                child_index = len(p["children"])
                                new_child = {
                                    "id": f"p_{parent_index}_c_{child_index}",
                                    "name": new_task_name,
                                    "level": 1,
                                    "completed": False,
                                }
                                st.session_state.wbs_data[i]["children"].append(new_child)
                                # Ensure parent gets unchecked if it was completed before adding an incomplete child
                                st.session_state.wbs_data[i]["completed"] = False
                                st.success(f"Added Child '{new_task_name}' to Parent '{p['name']}'")
                                parent_found = True
                                break
                        if not parent_found:
                             st.error("Selected parent not found. Cannot add child.")

                        st.session_state.show_add_task_form = False # Hide form after adding
                        st.experimental_rerun()
                    else:
                        st.warning("Please select a Parent to add the Child task to.")


    st.markdown("---") # Separator after form

# --- WBS Display and Interaction ---
if not st.session_state.wbs_data:
    st.info("Upload or parse a CSV file to see the WBS.")
else:
    wbs_changed = False # Flag to detect changes requiring a rerun

    # Create a mutable copy to modify during iteration if needed, though direct modification of session state is typical in Streamlit callbacks
    current_wbs = st.session_state.wbs_data

    for parent_idx, parent_task in enumerate(current_wbs):
        parent_id = parent_task['id']
        parent_key_base = f"task_{parent_id}"

        # Use st.expander for the parent task
        is_expanded = st.session_state.get(f"{parent_key_base}_expanded", parent_task.get("expanded", True))

        with st.expander(f"{parent_task['name']}", expanded=is_expanded):
            st.session_state[f"{parent_key_base}_expanded"] = True # Mark as expanded when opened

            # --- Parent Checkbox ---
            parent_completed = st.checkbox(
                f"Complete Phase", # Simpler label for parent checkbox
                value=parent_task.get("completed", False),
                key=f"{parent_key_base}_cb",
                help=f"Mark '{parent_task['name']}' and all its sub-tasks as complete."
            )

            # Check if parent state *changed* due to user interaction
            if parent_completed != parent_task.get("completed", False):
                parent_task["completed"] = parent_completed
                # If parent is checked, check all children. If unchecked, uncheck all children.
                for child_idx, child_task in enumerate(parent_task.get("children", [])):
                    child_task["completed"] = parent_completed
                wbs_changed = True
                # Need to rerun immediately to reflect child state changes visually
                st.experimental_rerun()


            # --- Child Task Checkboxes ---
            st.markdown("---") # Separator within expander
            children_changed = False
            all_children_now_complete = True if parent_task.get("children") else False # Assume true if no children

            for child_idx, child_task in enumerate(parent_task.get("children", [])):
                child_id = child_task['id']
                child_key = f"task_{child_id}_cb"

                child_completed = st.checkbox(
                    child_task['name'],
                    value=child_task.get("completed", False),
                    key=child_key
                )

                # Check if child state *changed*
                if child_completed != child_task.get("completed", False):
                    child_task["completed"] = child_completed
                    children_changed = True
                    wbs_changed = True # Mark general change

                # Track if all children are complete *after* potential changes this round
                if not child_task["completed"]:
                    all_children_now_complete = False

            # --- Sync Parent state based on Children ---
            # If children changed, or if parent is currently checked but not all children are
            if children_changed or (parent_task["completed"] and not all_children_now_complete):
                 if parent_task["completed"] != all_children_now_complete:
                      parent_task["completed"] = all_children_now_complete
                      # Rerun needed to update parent checkbox visually if it changed based on children
                      st.experimental_rerun()


        # Store collapsed state if expander is closed (st.expander doesn't have a direct callback for closed state)
        # This part is tricky; Streamlit doesn't easily report when an expander is *closed* by the user.
        # We set it to expanded when opened. If it's not interacted with in the next run, it implies closed state.
        # A more robust way might involve tracking interaction, but this is simpler for now.
        # For simplicity, we'll just let expanders reopen on rerun unless explicitly managed.
        # Let's stick with the default behavior or manage state only on open.


    # Persist changes back to session state (although modifying the iterated dicts often does this directly)
    st.session_state.wbs_data = current_wbs

    # Rerun if any fundamental WBS change occurred that wasn't handled by specific reruns above
    # (This is a safety net, might not be strictly needed with the targeted reruns)
    # if wbs_changed:
    #    st.experimental_rerun() # This might cause too many reruns, rely on specific ones first.


# --- Display Raw Data (Optional Debugging) ---
# with st.expander("Show Raw WBS Data"):
#    st.json(st.session_state.wbs_data)