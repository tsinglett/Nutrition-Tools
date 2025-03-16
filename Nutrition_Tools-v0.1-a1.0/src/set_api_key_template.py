import os

'''
This script sets an environment variable for the FoodData Central API key.

Register for an API key at https://fdc.nal.usda.gov/api-key-signup.html
and replace the value of API_KEY with your own key.

The API is provided free of charge by the USDA Agricultural Research Service,
and will require first, last name and email to register.
'''
API_KEY = '' # Enter your API key here

def set_api_key():
    os.environ['API_FoodData_Central'] = API_KEY
    print("API key set successfully.")

def main():
    set_api_key()

if __name__ == "__main__":
    # Running this script standalone will set the API key and print the stored value.
    main()
    value = os.environ.get('API_FoodData_Central')
    print(value)