# Nutrition Tools

## Overview
Nutrition Tools is a simple Python application designed to help users calculate the nutritional content of recipes. It sources nutritional data from the USDA FoodData Central API and uses fuzzy matching to find the closest match to the searched ingredient. Users can load recipes from a CSV file, and the application will analyze the ingredients to provide a detailed nutritional breakdown.

This program should be easy to install and configure. After installing the required dependencies and configuring the USDA API key, users can run the program to analyze their recipes. The output is exported in YAML format, making it easy to read and understand the nutritional content of the recipes.

The YAML output contains the nutritional content of each individual ingredient, as well as the total nutritional content of the recipe. Hopefully being able to see the contribution of each individual ingredient to the total nutritional content of the recipe will help the user make informed choices regarding their diet.


## Installation
To set up the Nutrition Tools project, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/tsinglett/nutrition-tools.git
   ```
2. Navigate to the project directory:
   ```
   cd Nutrition_Tools-v0.1-A1.0
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## API Key Setup

This project requires an API key from the USDA FoodData Central API.

1.  **Register for an API key:** Visit https://fdc.nal.usda.gov/api-key-signup.html and register for a free API key.
2.  **Set up the API key file:**
    * Copy the `src/set_api_key_template.py` file to `src/set_api_key.py`.
    * Open `src/set_api_key.py` in a text editor.
    * Replace the line `API_KEY = ''` with `API_KEY = 'YOUR_API_KEY'`, inserting the API key you obtained from the  USDA FoodData Central API.
3.  **Run the setup script:** Run the `src/set_api_key.py` script. This will set the API key as an environment variable. Currently the code is set up to save the API key to os.environ['API_FoodData_Central']

To verify that the set_api_key script is working properly, you can run it directly using:
```
python src/set_api_key.py
```
This will print the API key saved to os.environ['API_FoodData_Central'] to the console.

## Usage
To 'run' Nutrition Tools, follow these steps:

1. **Create a CSV file with your ingredients:**
   Create a CSV file (e.g., `ingredients.csv`) with the following format:
   ```
   {Ingredient}, {Amount}, {Unit}
   Broccoli, 2, cups
   ```
2. **Run the application:**
Execute the following command to run the application:
```
python main.py
```
The program will prompt you to enter the name of the CSV file containing your ingredients.

## Additional Useful Information:

 **Overview of how Nutrition Tools works at a functional level:**
- **Load API key:** The program loads the USDA FoodData Central API key from the environment variables.
- **Load ingredients from CSV:** The program reads the ingredients and their quantities from the specified CSV file.
- **Search for ingredients:** The program searches the USDA FoodData Central API for each ingredient using fuzzy matching to find the closest match.
- **Retrieve food data:** The program retrieves detailed nutritional information for each ingredient based on the FDC ID.
- **Process food data:** The program processes the food data to extract relevant nutritional information and portions.
- **Calculate conversion factors:** The program calculates conversion factors to convert the standard portion sizes to the specified quantities.
- **Compute ingredient nutrition:** The program computes the nutritional information for each ingredient based on the specified quantities.
- **Compute recipe nutrition:** The program aggregates the nutritional information for all ingredients to compute the total nutritional content of the recipe.
- **Export to YAML:** The program exports the nutritional analysis to a YAML file named `recipe_nutrition.yaml`.

**Logging system:**
The application uses a logging system to provide detailed information about its execution. The logs are saved to a file named `recipe_nutrition.log` and are also printed to the console. 

The logging levels are as follows:
- `DEBUG`: Includes detailed information, such as YAML dumps of the nutrition data. Generates a large file.
- `INFO`: Logs at the beginning and end of each function, within loops, and at decision points.
- `WARNING`: Logs when an error that will not impact output accuracy occurs (e.g., substituting external source portion data if the FDC data is missing).
- `ERROR`: Logs when an error that will impact output accuracy occurs (e.g., missing nutrient data).
- `CRITICAL`: Logs when an error that will cause the program to stop occurs (e.g., missing API key).

WARNING: Setting the log level to DEBUG generates a very large log file for every ingredient. Not intended for regular use, it is mainly for analyzing errors while debugging code. It dumps most important data structures as YAML. Each ingredient has a pretty large amount of nutritional data available from the USDA. Please keep this in mind, and make sure not to leave the logging level set to debug unless you really intend to log everything.

**Final Note:**
I have been programming this project in VS Code, and I have large block comments for major functions.
I normally have these comments collapsed unless I need to check what a function does, what inputs it requires and what it outputs. I have included these to hopefully make it easier to understand how the code operates.

## Contributing
Contributions are currently not possible, I need to spend more time on Github to learn how pull requests and contributing to a project works. Please enjoy this code and turn it into whatever you feel like, and send me a link if you post your project. I would love to see it.

## License
This project is licensed under the MIT License - see the LICENSE file for details.


