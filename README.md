# Pocket — Personal Expense Tracker

A browser version of the Python expense-tracker project. Add expenses, set monthly budgets, see category totals, delete entries, and import/export CSV files.

## First run in PyCharm

Keep the whole folder together. Open this folder as a project; do not paste app.py into the old terminal tracker. Your original tracker and CSV stay separate.

1. Open the **Terminal** panel inside PyCharm.
2. Make sure you are in the folder containing `app.py`, `tracker.py`, and `requirements.txt`.
3. Install the app's dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

4. Start the web app:

   ```sh
   python -m streamlit run app.py
   ```

On a Mac, use `python3` instead of `python` if needed. Use the interpreter configured for your PyCharm project. Python 3.12 or newer is a convenient choice; this copy was tested on Python 3.14.

The command prints a local URL, usually http://localhost:8501. Open it in your browser. Unlike the terminal project, use this Streamlit command rather than PyCharm's ordinary Run Python command. Keep the terminal running while using the page. Press Control+C in that terminal to stop it.

If your app reports that port 8501 is already in use, use:

```sh
python -m streamlit run app.py --server.port 8502
```

## Try it

1. Open the sidebar using the chevron at the upper left on a narrow window.
2. Set a $2,000 budget for the selected month.
3. Add a $25 Food expense dated within that month.
4. Confirm $25 spent, $1,975 remaining, and Food in the chart.
5. Add another Food expense and check that it joins the same category.
6. Use **Delete an expense**, choose an entry, and confirm deletion.
7. Download your expenses before closing or refreshing the browser.

**Try sample expenses** loads fictional examples only when the session is empty. **Start over** clears them after confirmation.

## Your existing CSV works

Expand **Import a CSV**, select the original `expenses.csv` or `expenses_upgraded.csv`, and click **Import valid expenses**. The importer reports bad rows and skips exact duplicates by default. Disable duplicate skipping if identical rows represent separate real expenses.

Required columns:

```csv
date,category,amount,description
2026-09-18,Food,25.00,Lunch
```

Import never runs just because you select a file: the explicit button performs it. Download includes every month and uses the same four-column format as your terminal project.

## Where the data lives

Each browser connection has its own expenses and budgets in Streamlit session state. Visitors do not share a global expense list. This app does not save their data in a shared server CSV.

Refreshing, closing the session, or restarting the server can clear the session. **Download your CSV to keep expenses, and upload it on a future visit.** Monthly budgets are not included in that CSV and must be entered again. This is a classroom demo without accounts or durable cloud storage. Data is processed by the Python server; session isolation does not mean browser-only processing or encryption from the hosting provider.

## Publish for free when your GitHub account is ready

The app is ready to deploy, but this folder is not itself a public website. You need a GitHub account and a Streamlit Community Cloud account to publish it.

1. Create a free account at https://github.com/signup. Complete your own password, verification, and account terms.
2. Create a repository named `pocket-expense-tracker`. A public repository is a simple option for a class demo; its code will be public.
3. Upload `app.py`, `tracker.py`, and `requirements.txt` to the repository root. Include README.md and tests if desired. Do not upload your personal expense CSV or virtual environment.
4. Include `.streamlit/config.toml` for the colors and upload-size limit. If your Mac hides dot folders, use GitHub's **Add file → Create new file**, enter `.streamlit/config.toml` as the filename, and paste this project's config contents. The folder name begins with a dot.
5. Sign in at https://share.streamlit.io and connect your GitHub account.
6. Choose **Create app → Yup, I have an app**. Select your repository, its actual branch (usually `main`), and `app.py` as the entrypoint.
7. Select a supported Python version in Advanced settings (3.12+), then deploy.
8. Open the resulting `*.streamlit.app` address in a separate/private browser window and try it before sharing it with your instructor. Check the app's sharing settings if it requires sign-in.

Hosting is free through Streamlit Community Cloud. Local file persistence is not guaranteed there, which is why this app uses upload/download instead.

Official guidance:
- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/create-your-account
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/develop/concepts/connections/connecting-to-data

## Understand the code

- **tracker.py** holds validation, calculations, and CSV handling. These functions don't know anything about buttons or pages.
- **app.py** builds the interface and connects controls to those functions.
- **st.session_state** remembers this visitor's data when Streamlit reruns the script after a click.
- **Forms** collect related inputs before submitting them together.
- **Integer cents** replace floating-point amounts internally. $25.50 is stored as 2550, so arithmetic stays exact. Decimal is used to parse and format dollars.
- **Stable IDs** keep deletion tied to the chosen expense even when the table is sorted.
- **requirements.txt** tells another computer which packages to install.

Keep your original numbered-menu program for the assignment unless your instructor approves substituting the browser interface. This website is an optional showcase of the same core project.

## Verification

From this folder, after installing dependencies:

```sh
python -m unittest discover -s tests -v
```

Checks cover exact currency arithmetic, bad dates/amounts, monthly totals, CSV round trips, invalid rows/headers, duplicate imports, forms, budgets, deletion confirmation, month filtering, reset confirmation, and separate visitor sessions.
