import pandas as pd
import numpy as np
import streamlit as st
import altair as alt  # Using Altair for both charts (add 'altair' to requirements.txt)

# Streamlit Web App
st.title("Health Score Dashboard")

# File Upload
uploaded_file = st.file_uploader("Upload New Data (CSV or Excel)", type=["csv", "xlsx"])
df_dict = {}
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            df_dict['Sheet1'] = df  # Treat CSV as single sheet
            st.success("Data uploaded and dashboard updated!")
        else:
            df_dict = pd.read_excel(uploaded_file, sheet_name=None)
            st.success("Data uploaded from multiple sheets and dashboard updated!")
    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("Upload a file to see the dashboard.")

# If no data, stop
if not df_dict:
    st.stop()

# Summary Page if multiple sheets
if len(df_dict) > 1:
    summary_tab, *test_tabs = st.tabs(["Summary"] + list(df_dict.keys()))
    with summary_tab:
        st.header("Summary Dashboard")
        summary_data = {}
        for sheet_name, df in df_dict.items():
            # Clean Value column (handle 'df_a1c' if present)
            if 'df_a1c' in df.columns:
                df = df.rename(columns={'df_a1c': 'Value'})
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
            df = df.dropna(subset=['Value'])
            average = df['Value'].mean()
            summary_data[sheet_name] = f"Average Value: {average:.2f}"

        for test, metric in summary_data.items():
            st.metric(test, metric)

# Process each sheet/test
tabs = st.tabs(list(df_dict.keys())) if len(df_dict) > 1 else [None]
for i, (sheet_name, df) in enumerate(df_dict.items()):
    with tabs[i] if len(df_dict) > 1 else st.container():
        # Clean columns
        if 'df_a1c' in df.columns:
            df = df.rename(columns={'df_a1c': 'Value'})
        if 'Age' in df.columns:
            df['Age'] = df['Age'].str.extract(r'(\d+)').astype(float, errors='ignore')
        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Value'])

        # Test Name from Column 5 (Parameter Name, assuming consistent per sheet)
        test_name = df['Parameter Name'].iloc[0] if 'Parameter Name' in df.columns and not df.empty else sheet_name
        st.header(f"{test_name} Health Score Dashboard")

        # Calculate stats
        average_a1c = df['Value'].mean()
        total_patients = len(df)
        num_normal = len(df[df['Value'] < 5.7])
        num_pre = len(df[(df['Value'] >= 5.7) & (df['Value'] < 6.5)])
        num_diab = len(df[df['Value'] >= 6.5])
        percent_diab = (num_diab / total_patients) * 100 if total_patients > 0 else 0
        percent_pre = (num_pre / total_patients) * 100 if total_patients > 0 else 0
        percent_normal = (num_normal / total_patients) * 100 if total_patients > 0 else 0

        if percent_diab < 10:
            health_grade = 'A'
        elif percent_diab < 20:
            health_grade = 'B'
        elif percent_diab < 30:
            health_grade = 'C'
        else:
            health_grade = 'D'

        # Display Metrics
        st.subheader("Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Health Grade", health_grade)
        col2.metric(f"Average {test_name}", f"{average_a1c:.2f}")
        col3.metric("Total Residents Tested", total_patients)

        col4, col5, col6 = st.columns(3)
        col4.metric("Normal (<5.7)", f"{num_normal} ({percent_normal:.2f}%)", delta_color="normal")
        col5.metric("Pre-Diabetes (5.7-6.4)", f"{num_pre} ({percent_pre:.2f}%)", delta_color="off")
        col6.metric("Diabetes (>=6.5)", f"{num_diab} ({percent_diab:.2f}%)", delta_color="inverse")

        # Sex Metrics and Chart (Column 2: Sex)
        if 'Sex' in df.columns:
            sex_counts = df['Sex'].value_counts(normalize=True) * 100
            male_percent = sex_counts.get('Male', 0)
            female_percent = sex_counts.get('Female', 0)
            st.subheader("Gender Breakdown")
            col7, col8 = st.columns(2)
            col7.metric("Male %", f"{male_percent:.2f}%")
            col8.metric("Female %", f"{female_percent:.2f}%")

            # Pie Chart for Sex
            sex_data = pd.DataFrame({
                'Gender': ['Male', 'Female'],
                'Percentage': [male_percent, female_percent]
            })
            sex_pie = alt.Chart(sex_data).mark_arc().encode(
                theta=alt.Theta(field="Percentage", type="quantitative"),
                color=alt.Color(field="Gender", type="nominal", scale=alt.Scale(range=['blue', 'pink'])),
                tooltip=['Gender', 'Percentage']
            ).properties(
                title='Gender Distribution',
                width=400,
                height=300
            )
            st.altair_chart(sex_pie, use_container_width=True)

        # Age Range Chart (Column 1: Age)
        if 'Age' in df.columns:
            df['Age Range'] = pd.cut(df['Age'], bins=[0, 18, 25, 35, 50, 65, 75, np.inf], labels=['<18', '18-25', '26-35', '36-50', '51-65', '66-75', '75+'], right=True)
            age_counts = df['Age Range'].value_counts().sort_index()
            age_data = pd.DataFrame({'Age Range': age_counts.index, 'Count': age_counts.values})

            st.subheader("Age Range Distribution")
            age_bar = alt.Chart(age_data).mark_bar(color='purple').encode(
                x='Age Range',
                y='Count',
                tooltip=['Age Range', 'Count']
            ).properties(
                title='Age Ranges',
                width=700,
                height=400
            )
            st.altair_chart(age_bar, use_container_width=True)

        # Charts for Test Values
        st.subheader("Charts")

        # Histogram using Altair
        hist_chart = alt.Chart(df).mark_bar(color='skyblue').encode(
            x=alt.X('Value:Q', bin=alt.Bin(maxbins=20)),
            y='count()',
            tooltip=['Value', 'count()']
        ).properties(
            title=f'{test_name} Value Distribution',
            width=700,
            height=400
        )
        st.altair_chart(hist_chart, use_container_width=True)

        # Pie Chart using Altair
        pie_data = pd.DataFrame({
            'Category': ['Normal', 'Pre-Diabetes', 'Diabetes'],
            'Count': [num_normal, num_pre, num_diab]
        })
        pie_chart = alt.Chart(pie_data).mark_arc().encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(field="Category", type="nominal", scale=alt.Scale(range=['green', 'orange', 'red'])),
            tooltip=['Category', 'Count']
        ).properties(
            title=f'{test_name} Risk Distribution',
            width=400,
            height=300
        )
        st.altair_chart(pie_chart, use_container_width=True)