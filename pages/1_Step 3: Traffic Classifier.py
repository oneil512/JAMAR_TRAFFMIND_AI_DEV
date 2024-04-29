import streamlit as st

# Set page configuration
st.set_page_config(page_title="TraffMind AI Traffic Classifier", layout="wide")

st.header("TraffMind AI Traffic Classifier")

# Description of the Traffic Classifier
st.markdown("""
The **TraffMind AI Traffic Classifier** is designed to enhance traffic management and analysis by classifying vehicles into distinct categories. This powerful tool can categorize vehicles into:
- **6 bins**: For basic classification needs, such as distinguishing between cars, vans, trucks, buses, motorcycles, and bicycles.
- **13 bins**: For more detailed analysis, providing finer distinctions among vehicle types.
- **Custom classifications**: Tailored to meet specific requirements, allowing for unique categorizations based on user-defined criteria.

### Coming Soon!
This feature is under development and will be available soon. It aims to provide unparalleled accuracy in vehicle classification, helping urban planners, traffic management teams, and researchers gain deeper insights into traffic flow dynamics.
""")
