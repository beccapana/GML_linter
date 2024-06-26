# GML Linter
## README ONLY FOR `test version.py`
This application provides a graphical user interface (GUI) for linting GML (GameMaker Language) code files. It identifies various syntax and style issues in GML code and provides options to view errors and warnings, as well as to save fixed versions of the code.

## Features

- **Linting**: Detects and reports errors and warnings in GML code files.
- **Syntax Checks**: Includes checks for line length, indentation, trailing spaces, uninitialized variables, syntax errors in control statements, naming conventions, and unused variables.
- **Automatic Fixes**: Provides automated fixes for certain formatting issues in the code, such as splitting long lines and correcting spacing around commas and brackets.
- **Graphical Interface**: Utilizes tkinter for the GUI, allowing users to interact with the application through buttons and text areas.

## Usage

1. **Open GML File**: Click the "Open GML File" button to select a .gml file for linting.
2. **View Results**: Errors and warnings will be displayed in the text area.
3. **Save Fixed Code**: Optionally save a fixed version of the code with corrected formatting issues.

## Additional Checks

- **Naming Conventions**: Warns if variable or function names do not follow camelCase convention.
- **Unused Variables**: Identifies variables declared but not used in the code, providing comments for such occurrences.

## Requirements

- Python 3.x
- tkinter library (usually included in standard Python distributions)

## Getting Started

To run the application:
1. Clone the repository or download the script.
2. Ensure you have Python installed.
3. Install any dependencies (`tkinter`).
4. Execute the script (`python gml_linter.py`).

## Contributing

Contributions are welcome! Feel free to fork the repository and submit pull requests with improvements or additional features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
