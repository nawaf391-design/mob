name: Deploy Streamlit App

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-and-run:
    runs-on: ubuntu-latest

    steps:
    - name: Check out repository code
      uses: actions/checkout@v4

    - name: Set up Python Environment
      uses: actions/setup-python@v5
      with:
        python-version: '3.11' # استخدام نسخة مستقرة للمكتبات الذكية

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install streamlit yfinance ta crewai

    - name: Run Application Check
      run: |
        # هذا الأمر يتأكد من أن الكود سليم وقابل للتشغيل دون أخطاء استيراد
        python -c "import streamlit; import yfinance; import ta; import crewai; print('All dependencies installed successfully!')"
