import streamlit as st
import tempfile
import os
import importlib.util
import sys
import re
import math
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_unit_tests(file_path):
    with open(file_path, 'r') as file:
        python_code = file.read()

    client = OpenAI(api_key= os.environ.get("OPENAI_API_KEY"))
    
    prompt = f"Generate comprehensive unit tests starting with the first function and generating each test line by line these tests will be in text form start with the function's name for example:  'add(1,2)' for a function called add make sure to generate enough values to test all possible conditions and to have a very high coverage, pay attention to the parameters to make sure you generate accurate results and most importantly make sure to cover all cases: ```\n\n{python_code} ``` \n\n only respond with the solution as your response will be directly input into the txt file so just response with the answers no comments in the solution either, make sure to generate test cases that can break the program###"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}],
        temperature=0
    )

    unit_tests = response.choices[0].message.content
    return unit_tests

def parse_test_case(test):
    test = test.strip()
    if not test:
        return None
    match = re.match(r"(\w+)\((.*)\)", test)
    if match:
        return match.group(1), eval(match.group(2), {"math": math})
    else:
        return None

def run_tests(test_file_path, module_path):
    module_name = module_path.split('/')[-1].split('.')[0]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with open(test_file_path, 'r') as file:
        test_content = file.readlines()

    results = []
    for test in test_content:
        parsed_case = parse_test_case(test)
        if parsed_case:
            function_name, params = parsed_case
            try:
                func = getattr(module, function_name)
                result = func(*params)
                results.append(f"{function_name}{params} = {result}\n")
            except Exception as e:
                results.append(f"Error executing {function_name}{params}: {str(e)}\n")
    return results

def main():
    
    logo_url = "https://res.cloudinary.com/dgdbxflan/image/upload/v1715612505/541c6f_bc97a1abbbcb4cdba1660d35ee0f1a11_mv2_hurv8g.jpg"
    st.image(logo_url, width=200)  # Adjust width as necessary
    
    st.title("Python Unit Test Generator and Executor")
    

    uploaded_file = st.file_uploader("Upload your Python file", type='py')
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmpfile:
            tmpfile.write(uploaded_file.getvalue())
            file_path = tmpfile.name
        
        if st.button('Generate and Run Tests'):
            test_content = generate_unit_tests(file_path)
            test_file_path = f"{tempfile.gettempdir()}/generated_tests.py"
            with open(test_file_path, 'w') as f:
                f.write(test_content)
            results = run_tests(test_file_path, file_path)

            st.text_area("Generated Unit Tests", test_content, height=300)
            st.text_area("Test Results", "\n".join(results), height=300)

            st.download_button("Download Unit Tests", test_content, file_name="unit_tests.py")
            st.download_button("Download Test Results", "\n".join(results), file_name="test_results.txt")

            os.unlink(file_path)  # Clean up temporary files

if __name__ == "__main__":
    main()
