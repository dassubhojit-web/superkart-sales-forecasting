import os

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="SuperKart Sales Forecast", layout="wide")

backend_url = os.getenv("BACKEND_URL", "http://backend:7860").rstrip("/")
st.title("SuperKart Sales Forecast")

single_tab, batch_tab = st.tabs(["Single prediction", "Batch inference"])

with single_tab:
    with st.form("prediction_form"):
        left, middle, right = st.columns(3)
        with left:
            product_weight = st.number_input("Product weight", min_value=0.01, value=12.66, step=0.10)
            sugar_content = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
            allocated_area = st.number_input(
                "Allocated-area ratio", min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f"
            )
            product_mrp = st.number_input("Product MRP", min_value=0.01, value=117.08, step=1.0)
        with middle:
            store_size = st.selectbox("Store size", ["Small", "Medium", "High"], index=1)
            city_tier = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"], index=1)
            store_type = st.selectbox(
                "Store type",
                ["Departmental Store", "Food Mart", "Supermarket Type1", "Supermarket Type2", "Supermarket Type3"],
                index=3,
            )
        with right:
            product_prefix = st.selectbox("Product family", ["DR", "FD", "NC"], index=1)
            store_age = st.number_input("Store age in 2026", min_value=0, max_value=100, value=17, step=1)
            product_group = st.selectbox("Product handling group", ["Perishables", "Non Perishables"], index=1)
        submitted = st.form_submit_button("Estimate sales", type="primary", use_container_width=True)

    if submitted:
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": sugar_content,
            "Product_Allocated_Area": allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": city_tier,
            "Store_Type": store_type,
            "Product_Id_char": product_prefix,
            "Store_Age_Years": store_age,
            "Product_Type_Category": product_group,
        }
        try:
            response = requests.post(f"{backend_url}/v1/predict", json=payload, timeout=30)
            response.raise_for_status()
            st.metric("Estimated product-store sales", f"{response.json()['prediction']:,.2f}")
        except (requests.RequestException, KeyError, ValueError) as error:
            st.error(f"Prediction request failed: {error}")

with batch_tab:
    uploaded_file = st.file_uploader("Upload a CSV with the ten model features", type=["csv"])
    run_batch = st.button("Run batch inference", disabled=uploaded_file is None, use_container_width=True)
    if run_batch and uploaded_file is not None:
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            response = requests.post(f"{backend_url}/v1/predictbatch", files=files, timeout=120)
            response.raise_for_status()
            results = pd.DataFrame(response.json()["predictions"])
            st.dataframe(results, use_container_width=True, hide_index=True)
            st.download_button(
                "Download predictions",
                results.to_csv(index=False).encode("utf-8"),
                file_name="superkart_predictions.csv",
                mime="text/csv",
                use_container_width=True,
            )
        except (requests.RequestException, KeyError, ValueError) as error:
            st.error(f"Batch request failed: {error}")
