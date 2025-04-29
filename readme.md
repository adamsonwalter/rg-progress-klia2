# README.md

## WBS Progress Tracker

This Streamlit application provides a simple way to visualize and track the progress of a project based on a 2-level Work Breakdown Structure (WBS).

**Features:**

*   Loads initial WBS data from a CSV file (`Gantt Chart - KLIA (26 Mar 2025)(Project schedule).csv`).
*   Displays tasks in a Parent -> Child hierarchy.
*   Parent tasks (Phases) can be expanded or collapsed to show/hide Child tasks using `st.expander`.
*   Checkboxes allow marking tasks as complete.
*   Ticking a Parent task automatically ticks all its Child tasks.
*   The Parent task checkbox automatically updates based on the completion status of its Child tasks (checked only if *all* children are checked).
*   An overall progress bar shows the percentage of completed Child tasks.
*   Allows adding new Parent or Child tasks dynamically to the structure.

**Project Structure:**

*   `app.py`: The main Streamlit application script.
*   `Gantt Chart - KLIA (26 Mar 2025)(Project schedule).csv`: The input data file containing the project tasks.
*   `requirements.txt`: Lists the necessary Python packages.
*   `README.md`: This file.

**How to Run Locally:**

1.  Make sure you have Python installed.
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Place the `Gantt Chart - KLIA (26 Mar 2025)(Project schedule).csv` file in the same directory as `app.py`.
4.  Run the Streamlit app from your terminal:
    ```bash
    streamlit run app.py
    ```
5.  The application will open in your web browser.

**How to Deploy to Streamlit Community Cloud:**

1.  Create a GitHub repository containing `app.py`, `requirements.txt`, and the CSV data file (`Gantt Chart - KLIA (26 Mar 2025)(Project schedule).csv`).
2.  Sign up or log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3.  Click "New app" and connect your GitHub account.
4.  Select the repository you created.
5.  Ensure the "Main file path" is set to `app.py`.
6.  Click "Deploy!". Streamlit will handle the installation of requirements and hosting.

**Notes:**

*   The CSV parsing logic in `app.py` is tailored to the specific format observed in the provided `Gantt Chart - KLIA...csv` file. Changes to the CSV structure (especially the first few rows or how Phases/Tasks are indicated) might require adjustments to the `parse_csv_to_wbs` function.
*   The "Add Task" functionality currently adds new Parents at the end of the list and new Children at the end of the selected Parent's child list. More complex insertion (e.g., "insert before task X") is not implemented to maintain simplicity.