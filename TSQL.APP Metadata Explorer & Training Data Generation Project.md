# TSQL.APP Metadata Explorer & Training Data Generation Project

## 1. Introduction

The **TSQL.APP Metadata Explorer** is a Python-based tool designed to introspect the metadata database of a TSQL.APP framework installation. Its primary purpose is to automatically discover and analyze framework components—such as stored procedures, user-defined functions, and existing action scripts—to generate structured data. This structured data serves as a foundational resource for creating comprehensive training documentation and enhancing understanding of how to develop effectively within the TSQL.APP "SQL-First" paradigm.

This project aids developers, technical writers, and trainers in understanding the data-driven architecture of TSQL.APP, where application structure and business logic are primarily defined and stored within database metadata.

## 2. Project Goals

*   **Automated Discovery:** To automatically identify TSQL.APP framework Stored Procedures (SPs) and User-Defined Functions (UDFs).
*   **Detailed Parameter Analysis:** To parse SP/UDF definitions to extract accurate parameter information, including full data types, default values, and `OUTPUT`/`READONLY` status.
*   **Action Script Corpus Collection:** To retrieve and store a corpus of existing TSQL.APP action scripts from the metadata database.
*   **Usage Pattern Identification:** To analyze the action script corpus to find real-world usage examples of framework components and identify common coding patterns.
*   **Embedded Documentation Extraction:** To find and extract any developer-provided documentation or code examples embedded within SQL object definitions (e.g., `/*code ... */` or `/*help.description ... */` blocks).
*   **Structured Data Generation:** To output a comprehensive JSON file (`tsql_app_training_guide_data.json`) containing all discovered and analyzed information, suitable for feeding into documentation generation processes or for direct analysis.
*   **Facilitate Training Material Creation:** Ultimately, to provide the raw material needed to teach developers how to write valid, efficient, and best-practice compliant action scripts for TSQL.APP.

## 3. How It Works: Key Information Sources

The Metadata Explorer leverages several key sources:

*   **TSQL.APP Metadata Database:** The primary target for introspection. The script connects directly to the SQL Server database that holds the TSQL.APP project's metadata (e.g., a database named `YourApp_proj`). It queries:
    *   System views like `sys.objects`, `sys.schemas`, `sys.sql_modules`, and `sys.parameters` to find SPs/UDFs and their definitions.
    *   TSQL.APP specific metadata tables like `dbo.api_card_actions` (for card-specific action scripts, typically from an `unparsed_sql` column) and `dbo.api_actions` (for general action scripts, typically from `sql_script` or `unparsed_sql` columns).
    *   `INFORMATION_SCHEMA.TABLES` and `INFORMATION_SCHEMA.COLUMNS` to dynamically understand the schema of the target database, making queries more robust.
*   **User-Provided SQL View (Optional but Recommended):** The script can leverage a user-created SQL view (default name: `dbo.tsql_app_parameter_info_3`, configurable via the `SQL_VIEW_FOR_PARAM_INFO` environment variable) that pre-parses SP/UDF definitions to reliably extract parameter default values and optionality status. This is often more robust than Python-side regex for defaults due to T-SQL's complex syntax.
*   **Embedded Documentation in SQL Objects:** The Python parser looks for specially formatted comment blocks within SP/UDF definitions (e.g., `/*code ... */`, `/*help.description ... */`) to extract usage examples and descriptions.
*   **Environment Variables:** For database connection details and configuration of patterns.

## 4. Core Functionality of `metadata_explorer_final.py`

The Python script (`metadata_explorer_final.py`) performs the following main tasks:

1.  **Database Connection:** Securely connects to the specified SQL Server database using credentials and settings from a `.env` file.
2.  **Schema Introspection & "Memory":**
    *   On its first run (or when forced), it discovers the actual table and column structure of the target database and saves this to `discovered_schema.json`.
    *   Subsequent runs load this "schema memory" to build queries safely, avoiding "Invalid column name" errors by only referencing columns confirmed to exist.
3.  **Framework API Analysis:**
    *   Identifies potential TSQL.APP framework SPs and UDFs based on name patterns defined in the `FRAMEWORK_OBJECT_PATTERNS` environment variable.
    *   Parses the T-SQL definitions of these objects (`sys.sql_modules.definition`) using regular expressions to extract detailed parameter information (full type, default values, `OUTPUT`/`READONLY` status).
    *   Extracts any embedded documentation.
    *   If a user-provided SQL view for parameter info exists, it prioritizes default values from this view.
    *   Saves the collated API details to `framework_api_details.json`.
4.  **Action Script Corpus Management:**
    *   Fetches T-SQL source code of action scripts from relevant metadata tables.
    *   Saves this corpus to `action_scripts_corpus.json`.
5.  **Content Analysis & Example Finding:**
    *   Analyzes action scripts to identify calls to known framework SPs/UDFs and usage of TSQL.APP context variables (defined by `TSQL_APP_CONTEXT_VARIABLES` environment variable).
    *   Finds real-world usage examples of SPs/UDFs within the action script corpus.
    *   Calculates co-occurrence statistics for framework objects (i.e., which SPs/UDFs are often used together).
6.  **Output Generation:**
    *   Produces a primary output file: `tsql_app_training_guide_data.json`. This JSON file contains:
        *   `framework_api_reference`: Detailed information for each discovered SP and UDF.
        *   `action_script_analysis_summary`: Statistics and samples from the analysis of actual action scripts.
        *   `metadata`: Information about the script run and data sources.
    *   Updates a `previous_run_summary.json` to track changes between runs.

## 5. Prerequisites

*   **Python 3.x** installed.
*   Required Python packages: `pyodbc`, `python-dotenv`. Install them using pip:
    ```bash
    pip install pyodbc python-dotenv
    ```
*   **ODBC Driver for SQL Server:** Ensure an appropriate ODBC driver for SQL Server is installed on the machine running the script (e.g., "ODBC Driver 17 for SQL Server").
*   **Access to the TSQL.APP Metadata Database:** SQL Server credentials with at least read access to the system views (`sys.objects`, `sys.sql_modules`, etc.) and the TSQL.APP metadata tables (`dbo.api_card_actions`, `dbo.api_actions`, etc.).
*   **(Optional but Recommended) SQL View for Parameter Defaults:** Create the SQL view (e.g., `dbo.tsql_app_parameter_info_3` as provided in previous discussions) in your TSQL.APP metadata database. This view should parse SP/UDF definitions to extract `object_id`, `parameter_name`, `is_optional` (0 or 1), and `default_value` (as a string).

## 6. Setup and Configuration

1.  **Clone/Download the Script:** Place `metadata_explorer_final.py` in your project directory.
2.  **Create a `.env` file:** In the same directory as the script, create a file named `.env` with your database connection details and other configurations. Example:

    ```env
    # Database Connection
    TSQL_DB_SERVER=your_server_address
    DB_PORT=1433 # Optional, remove if using default or named instance
    DB_NAME=your_tsql_app_metadata_database_name
    DB_USERNAME=your_sql_username
    DB_PASSWORD=your_sql_password
    # DB_DRIVER={ODBC Driver 17 for SQL Server} # Optional, defaults to this
    # DB_TRUSTED_CONNECTION=no # Use 'yes' for Windows Authentication, then USERNAME/PASSWORD are not needed
    DB_TIMEOUT=30

    # Framework Object Discovery Patterns (comma-separated)
    FRAMEWORK_OBJECT_PATTERNS=sp_api_%,sp_sys_%,context_%,dbo.IsEmpty,dbo.HasRole,dbo.abcLeft,dbo.CAMEL_SPACE,dbo.escape_string,dbo.ABCDATE,dbo.date_nice,dbo.floor,dbo.round,dbo.str2date,dbo.str2dec,dbo.regex_%

    # TSQL.APP Context Variables (comma-separated)
    TSQL_APP_CONTEXT_VARIABLES=@card_id,@id,@ids,@user_id,@card_name,@user_name,@basetable,@tablename,@identity_column,@parent_card_id,@parent_id,@path,@previous_path,@is_new,@is_form,@hostname,@is_picklist,@picklist_fieldname,@picklist_type,@card_field_id,@parent_card_name,@parent_parent_id,@user,@uri,@selected_field_name,@origin,@current_card_action_id

    # (Optional) Name of your SQL view for pre-parsed parameter defaults
    SQL_VIEW_FOR_PARAM_INFO=dbo.tsql_app_parameter_info_3

    # (Optional) Limits for fetching action scripts for the corpus
    # MAX_CARD_ACTIONS_TO_CORPUS=250
    # MAX_API_ACTIONS_TO_CORPUS=150
    # LIMIT_PRINT_SCRIPT_ANALYSIS_SAMPLE=20 # Number of analyzed scripts to include in detail in JSON output
    ```
    *   Adjust `FRAMEWORK_OBJECT_PATTERNS` to match the naming conventions of your TSQL.APP framework's SPs and UDFs.
    *   Adjust `TSQL_APP_CONTEXT_VARIABLES` if your framework uses a different set.

## 7. Running the Script

Open a terminal or command prompt in the directory containing the script and the `.env` file.

*   **Standard Run (uses memory files if available):**
    ```bash
    python metadata_explorer_final.py
    ```

*   **Force Full Rediscovery (ignores all memory files and re-fetches everything from DB):**
    ```bash
    python metadata_explorer_final.py --force-full-rediscover
    ```

*   **Force Specific Re-discovery:**
    *   Re-discover database schema: `python metadata_explorer_final.py --rediscover-schema`
    *   Re-discover framework API details: `python metadata_explorer_final.py --rediscover-api`
    *   Re-fetch action scripts for the corpus: `python metadata_explorer_final.py --refresh-action-scripts`

*   **Test Parsing for a Specific Stored Procedure or Function:**
    ```bash
    python metadata_explorer_final.py --test-sp sp_api_modal_image
    python metadata_explorer_final.py --test-sp dbo.context_user --debug-parser
    ```
    (Use `--debug-parser` to see detailed regex parsing steps, very useful for troubleshooting.)

*   **Test Analysis for a Specific Action Script:**
    ```bash
    python metadata_explorer_final.py --test-action-script-id 123 
    python metadata_explorer_final.py --test-action-script-id 45 --test-action-script-table api_actions
    ```

## 8. Output Files

The script generates/updates the following files in the same directory:

*   **`tsql_app_training_guide_data.json` (Primary Output):** Contains the structured data for framework SPs/UDFs, parameter details, embedded examples, real-world usage examples from action scripts, and a sample of analyzed action scripts. This is the main file to be used for documentation generation.
*   **`discovered_schema.json` (Memory File):** Caches the discovered database table and column structure.
*   **`framework_api_details.json` (Memory File):** Caches the discovered details of framework SPs and UDFs.
*   **`action_scripts_corpus.json` (Memory File):** Caches the retrieved action script source code.
*   **`previous_run_summary.json` (Memory File):** Stores a summary of the last run's statistics to show changes in the current run.

## 9. Using the Output for Documentation

The `tsql_app_training_guide_data.json` file is the key deliverable. It can be used in various ways:

1.  **Input to Automated Documentation Tools:** Use other scripts or templating engines (e.g., Jinja2 with Python) to transform the JSON data into Markdown, HTML, or other documentation formats.
2.  **Manual Reference:** Developers and technical writers can directly browse the JSON file to understand SP/UDF parameters, find examples, and see how components are used.
3.  **LLM Enhancement:** The structured data can be used as context to fine-tune or prompt Large Language Models for generating more accurate and detailed TSQL.APP specific documentation or code assistance.
4.  **Consistency Checking:** Analyze the output to identify inconsistencies in SP naming, parameterization, or adherence to coding standards.

## 10. Troubleshooting

*   **"Invalid column name" errors:** Usually means the schema discovery is out of sync or an assumed column doesn't exist. Run with `--rediscover-schema`. If it persists, check the `build_safe_select_query` logic and the actual table structures.
*   **Database Connection Errors:**
    *   Verify all details in your `.env` file (server, database, username, password, driver).
    *   Ensure the SQL Server instance is accessible from the machine running the script.
    *   Check firewall settings.
    *   Ensure the correct ODBC driver is installed and specified.
*   **Parameter Parsing Issues (`type_from_def` incorrect, defaults missing):**
    *   This is the most complex part. Use `python metadata_explorer_final.py --test-sp YourProblematicSP --debug-parser`. Examine the debug output, especially the "Isolated param section" and the "Processing declaration part" sections, to see what text the regex is working with and how it's matching (or failing to match).
    *   Ensure your optional SQL View (`SQL_VIEW_FOR_PARAM_INFO`) is correctly created and populated if you are relying on it for defaults. The script will log if it can't find or use the view.
    *   The Python regex parser (`parse_sql_parameters_from_definition`) may need further refinement for very complex or unusually formatted T-SQL procedure definitions.
*   **No Real Usage Examples Found:**
    *   Ensure `FRAMEWORK_OBJECT_PATTERNS` correctly identifies your SPs/UDFs.
    *   Ensure the script is fetching action scripts from the correct tables (`api_card_actions`, `api_actions`) and SQL columns (`unparsed_sql`, `sql_script`).
    *   The action script corpus might not contain examples of the specific SP you're testing, or the `MAX_..._TO_CORPUS` limits might be too low. Try running with `--refresh-action-scripts`.

This Metadata Explorer project provides a powerful, automated way to gain deep insights into the TSQL.APP framework, significantly aiding the creation of high-quality developer documentation.

---