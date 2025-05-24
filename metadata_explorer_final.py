# metadata_explorer_final.py

import pyodbc
import json
import os
import re
from dotenv import load_dotenv
import argparse
from datetime import datetime
from collections import Counter

# Try to import json
import os
import argparse
from dotenv import load_dotenv
from framework_training.training_generator import TrainingExampleGenerator
from framework_training.utils import save_json_file

# Global variable for training availability
TRAINING_AVAILABLE = True

# Initialize argument parser
parser = argparse.ArgumentParser(description="TSQL.APP Training Data Generator with Enhanced Memory & Smarter Indicators")
parser.add_argument("--force-full-rediscover", action="store_true", help="Force re-discovery of everything: schema, API, and action scripts.")
parser.add_argument("--rediscover-schema", action="store_true", help="Force schema re-discovery.")
parser.add_argument("--rediscover-api", action="store_true", help="Force API details re-discovery.")
parser.add_argument("--refresh-action-scripts", action="store_true", help="Force action scripts re-fetching.")
parser.add_argument("--debug-parser", action="store_true", help="Enable detailed parser debugging.")
parser.add_argument("--test-sp", type=str, help="Test parsing for a specific SP/UDF. Provide name (e.g., 'sp_api_backup' or 'dbo.my_function').")
parser.add_argument("--test-action-script-id", type=int, help="Test analysis for a specific action script ID.")
parser.add_argument("--test-action-script-table", type=str, choices=['api_card_actions', 'api_actions'], default='api_card_actions', help="Table for --test-action-script-id (default: api_card_actions).")
parser.add_argument("--max-examples-for-test-sp", type=int, default=3, help="Max real usage examples to fetch when testing a single SP (default: 3).")

# Load environment variables from .env file
load_dotenv()

# Parse arguments globally
script_args_global = parser.parse_args()

def main():
    # Load framework API details
    api_file = os.path.join('framework_training', 'framework_api.json')
    with open(api_file, 'r', encoding='utf-8') as f:
        framework_api = json.load(f)

    # Initialize training generator
    training_generator = TrainingExampleGenerator(framework_api)

    # Load action scripts corpus
    corpus_file = os.path.join('framework_training', 'action_scripts_corpus.json')
    with open(corpus_file, 'r', encoding='utf-8') as f:
        action_scripts_corpus = json.load(f)

    # Generate training materials
    if TRAINING_AVAILABLE:
        results = training_generator.generate_examples(action_scripts_corpus, relationships)
        
        # If testing a specific procedure, print its details
        if script_args_global.test_sp:
            print(f"\n=== TESTING PROCEDURE: {script_args_global.test_sp} ===")
            test_procedure(framework_api, script_args_global.test_sp)
    else:
        print("INFO: Skipping training material generation as module is not available")

# Load environment variables from .env file
load_dotenv()

# --- Configuration & Globals ---
SCHEMA_MEMORY_FILE = "discovered_schema.json"
API_DETAILS_MEMORY_FILE = "framework_api_details.json"
ACTION_SCRIPTS_CORPUS_FILE = "action_scripts_corpus.json"
TRAINING_GUIDE_OUTPUT_FILE = "tsql_app_training_guide_data.json"
PREVIOUS_RUN_SUMMARY_FILE = "previous_run_summary.json"
# Define the name of your SQL view for parameter info
SQL_VIEW_FOR_PARAM_INFO = os.getenv("SQL_VIEW_FOR_PARAM_INFO", "dbo.tsql_app_parameter_info_3")


DB_CONFIG = {
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}'),
    'server': os.getenv('TSQL_DB_SERVER'), 'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME'), 'uid': os.getenv('DB_USERNAME'),
    'pwd': os.getenv('DB_PASSWORD'),
    'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION', 'no').lower(),
    'timeout': os.getenv('DB_TIMEOUT', '30')
}

essential_env_vars_to_check = ['TSQL_DB_SERVER', 'DB_NAME']
if DB_CONFIG['trusted_connection'] != 'yes':
    essential_env_vars_to_check.extend(['DB_USERNAME', 'DB_PASSWORD'])
missing_configs = [key for key in essential_env_vars_to_check if not os.getenv(key)]
if missing_configs:
    print(f"Error: Missing essential database configuration in .env file: {', '.join(missing_configs)}")
    exit(1)

_discovered_schema_cache = {}
_framework_api_details_cache = {}
_action_scripts_corpus_cache = {}
_previous_run_summary = {}

# --- Helper Functions ---
def execute_query(sql, params=None, fetch_one=False):
    server_address = DB_CONFIG['server']
    if DB_CONFIG.get('port') and DB_CONFIG['port'].strip(): server_address += f",{DB_CONFIG['port']}"
    conn_str_parts = [f"DRIVER={DB_CONFIG['driver']}", f"SERVER={server_address}", f"DATABASE={DB_CONFIG['database']}"]
    if DB_CONFIG['trusted_connection'] == 'yes': conn_str_parts.append("Trusted_Connection=yes")
    else:
        if DB_CONFIG['uid']: conn_str_parts.append(f"UID={DB_CONFIG['uid']}")
        if DB_CONFIG['pwd']: conn_str_parts.append(f"PWD={DB_CONFIG['pwd']}")
    conn_str_parts.extend(["Encrypt=no", "TrustServerCertificate=yes"])
    conn_str = ";".join(conn_str_parts) + ";"
    results, cnxn = [], None
    try:
        cnxn = pyodbc.connect(conn_str, timeout=int(DB_CONFIG['timeout']))
        with cnxn.cursor() as cursor:
            cursor.execute(sql, params) if params else cursor.execute(sql)
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                if fetch_one:
                    row_data = cursor.fetchone()
                    return dict(zip(columns, row_data)) if row_data else None
                for row_data_item in cursor.fetchall():
                    results.append(dict(zip(columns, row_data_item)))
    except pyodbc.Error as ex:
        print(f"DATABASE_ERROR ({ex.args[0]}) in execute_query: {ex}\nFailed SQL: {sql}")
        return None
    except Exception as e:
        print(f"UNEXPECTED_ERROR in execute_query: {e}\nProblematic SQL: {sql}")
        return None
    finally:
        if cnxn: cnxn.close()
    return results


def load_memory_file(filepath, cache_dict_ref_to_update):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                cache_dict_ref_to_update.clear()
                cache_dict_ref_to_update.update(loaded_data)
            return True
        except Exception as e:
            print(f"MEMORY_ERROR: Could not load '{filepath}': {e}")
    return False

def save_memory_file(filepath, data_dict_to_save):
    if not isinstance(data_dict_to_save, dict):
        return
    if "metadata" not in data_dict_to_save:
        temp_wrapper = {}
        temp_wrapper.update(data_dict_to_save)
        temp_wrapper["metadata"] = {}
        dict_to_actually_save = temp_wrapper
    else:
        dict_to_actually_save = data_dict_to_save
    dict_to_actually_save["metadata"]["last_updated"] = datetime.now().isoformat()
    if "source" not in dict_to_actually_save["metadata"]:
        dict_to_actually_save["metadata"]["source"] = "script_save"
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dict_to_actually_save, f, indent=4, default=str)
        print(f"MEMORY_SAVE: Saved data to '{filepath}'.")
    except Exception as e:
        print(f"MEMORY_ERROR: Could not save to '{filepath}': {e}")

def discover_table_schema_from_db(schema_name, table_name, local_args):
    global _discovered_schema_cache
    cache_key = f"{schema_name.lower()}.{table_name.lower()}"
    _discovered_schema_cache.setdefault("tables", {})
    sql_exists = "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?;"
    if not execute_query(sql_exists, (schema_name, table_name), fetch_one=True):
        _discovered_schema_cache["tables"][cache_key] = {"exists": False, "columns": []}
        return
    sql_columns = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION;
    """
    rows = execute_query(sql_columns, (schema_name, table_name))
    columns_info = []
    if rows:
        for r in rows:
            columns_info.append({
                "name": r['COLUMN_NAME'], "type": r['DATA_TYPE'],
                "length": r.get('CHARACTER_MAXIMUM_LENGTH') or r.get('NUMERIC_PRECISION')
            })
    _discovered_schema_cache["tables"][cache_key] = {"exists": True, "columns": columns_info}


def get_actual_columns_for_table(schema_name, table_name, local_args):
    global _discovered_schema_cache
    cache_key = f"{schema_name.lower()}.{table_name.lower()}"
    _discovered_schema_cache.setdefault("tables", {})
    if not local_args.rediscover_schema and cache_key in _discovered_schema_cache["tables"]:
        table_info = _discovered_schema_cache["tables"][cache_key]
        return table_info["columns"] if table_info["exists"] else None
    discover_table_schema_from_db(schema_name, table_name, local_args)
    if cache_key in _discovered_schema_cache["tables"] and _discovered_schema_cache["tables"][cache_key]["exists"]:
        return _discovered_schema_cache["tables"][cache_key]["columns"]
    return None


def build_safe_select_query(schema_name, table_name, assumed_columns_list, local_args, where_clause="", order_by_clause="", top_n=100):
    columns_info_list = get_actual_columns_for_table(schema_name, table_name, local_args)
    if columns_info_list is None: return None, []
    actual_column_names_lower = [ci['name'].lower() for ci in columns_info_list]
    actual_column_original_case_map = {ci['name'].lower(): ci['name'] for ci in columns_info_list}
    safe_select_parts, final_selected_cols_or_aliases = [], []
    for assumed_col_spec in assumed_columns_list:
        col_to_check_lower, alias, original_assumed_name = ("", None, assumed_col_spec)
        if isinstance(assumed_col_spec, tuple):
            col_to_check_lower, alias, original_assumed_name = assumed_col_spec[0].lower(), assumed_col_spec[1], assumed_col_spec[0]
        else: col_to_check_lower = assumed_col_spec.lower()
        if col_to_check_lower in actual_column_names_lower:
            db_col_name_original_case = actual_column_original_case_map[col_to_check_lower]
            select_part = f"[{db_col_name_original_case}] AS [{alias}]" if alias else f"[{db_col_name_original_case}]"
            safe_select_parts.append(select_part)
            final_selected_cols_or_aliases.append(alias if alias else db_col_name_original_case)
    if not safe_select_parts:
        if columns_info_list:
            fallback_col_name = actual_column_original_case_map.get('id') or columns_info_list[0]['name']
            safe_select_parts.append(f"[{fallback_col_name}]")
            final_selected_cols_or_aliases.append(fallback_col_name)
        else: return None, []
    select_clause_str = ", ".join(safe_select_parts)
    top_clause = f"TOP ({top_n}) " if top_n and isinstance(top_n, int) and top_n > 0 else ""
    query = f"SELECT {top_clause}{select_clause_str} FROM [{schema_name}].[{table_name}]"
    if where_clause: query += f" WHERE {where_clause}"
    if order_by_clause:
        safe_order_by_parts = []
        final_selected_names_lower = [c.lower().replace('[','').replace(']','') for c in final_selected_cols_or_aliases]
        for ob_part in order_by_clause.replace("ORDER BY", "", 1).strip().split(','):
            ob_col_name_match = re.match(r'\s*\[?([\w\s\."\']+)\]?\s*(ASC|DESC)?', ob_part.strip(), re.IGNORECASE)
            if ob_col_name_match:
                ob_col_name, ob_direction = ob_col_name_match.group(1), (ob_col_name_match.group(2) or "").upper()
                ob_col_name_cleaned = ob_col_name.replace('[','').replace(']','').replace('"','').replace("'",'')
                if ob_col_name_cleaned.lower() in final_selected_names_lower:
                    original_case_ob_col = next((sel_col for sel_col in final_selected_cols_or_aliases if sel_col.lower().replace('[','').replace(']','') == ob_col_name_cleaned.lower()), ob_col_name_cleaned)
                    safe_order_by_parts.append(f"[{original_case_ob_col}] {ob_direction}".strip())
        if safe_order_by_parts: query += f" ORDER BY {', '.join(safe_order_by_parts)}"
    return query + ";", final_selected_cols_or_aliases


def print_results(title, data, description_or_actual_cols=None, actual_columns_queried_if_four_args=None):
    description, actual_columns_queried_list = "", None
    if actual_columns_queried_if_four_args is not None:
        description, actual_columns_queried_list = description_or_actual_cols, actual_columns_queried_if_four_args
    elif isinstance(description_or_actual_cols, list): actual_columns_queried_list = description_or_actual_cols
    elif description_or_actual_cols is not None: description = description_or_actual_cols
    print(f"\n--- {title} ---")
    if description: print(description)
    if actual_columns_queried_list: print(f"SCHEMA_INFO: Queried columns: {', '.join(actual_columns_queried_list)}")
    if data is None: print("RESULT_INFO: Error or no data.")
    elif not data and not isinstance(data, dict): print("RESULT_INFO: No data found (empty list/iterable).")
    elif isinstance(data, list) and not data: print("RESULT_INFO: No data found (empty list).")
    elif isinstance(data, list):
        for i, row in enumerate(data): print(f"Row {i+1}: {json.dumps(row, indent=2, default=str)}")
    else: print(json.dumps(data, indent=2, default=str))

def parse_sql_parameters_from_definition(definition_text, object_name_for_debug="", local_args=None):
    params = {}
    if not definition_text: return params
    debug_parser_enabled = local_args.debug_parser if local_args and hasattr(local_args, 'debug_parser') else False
    
    if debug_parser_enabled:
        print(f"\nDEBUG_PARSER: --- Start Processing Definition for '{object_name_for_debug}' ---")
        # print(f"DEBUG_PARSER: Full Definition (first 1000 chars):\n{definition_text[:1000]}\n---")

    # 1. Pre-processing: Remove comments
    definition_text_no_blocks = re.sub(r'/\*[\s\S]*?\*/', '', definition_text)
    lines = definition_text_no_blocks.splitlines()
    cleaned_lines = []
    for line in lines:
        in_string = False; comment_start = -1
        for i, char in enumerate(line):
            if char == "'": in_string = not in_string
            elif char == '-' and i + 1 < len(line) and line[i+1] == '-' and not in_string:
                comment_start = i; break
        cleaned_lines.append(line if comment_start == -1 else line[:comment_start])
    definition_text_no_comments = "\n".join(cleaned_lines)
    
    if debug_parser_enabled:
        print(f"DEBUG_PARSER: Definition after comment removal (first 1000 chars):\n{definition_text_no_comments[:1000]}\n---")

    # 2. Isolate the parameter declaration section
    param_section_text = ""
    header_regex = re.compile(
        r'(CREATE|ALTER)\s+(PROC(?:EDURE)?|FUNCTION)\s+'
        r'((?:\[.*?\]|[\w.]+)\s*\.\s*(?:\[.*?\]|[\w.]+)|(?:\[.*?\]|[\w.]+))\s*'
        r'([\s\S]*?)'
        r'(?=\bAS\b|\bRETURNS\b|\bWITH\b)', re.IGNORECASE
    )
    header_match = header_regex.search(definition_text_no_comments)

    if header_match:
        text_after_object_name = header_match.group(4).strip()
        if debug_parser_enabled:
            print(f"DEBUG_PARSER: Text after object name (potential params): '{text_after_object_name}'")
        if text_after_object_name.startswith('('):
            open_paren_count = 0; end_paren_index = -1
            for i, char_ in enumerate(text_after_object_name):
                if char_ == '(': open_paren_count += 1
                elif char_ == ')':
                    open_paren_count -= 1
                    if open_paren_count == 0: end_paren_index = i; break
            if end_paren_index != -1: param_section_text = text_after_object_name[1:end_paren_index]
            else:
                param_section_text = text_after_object_name
                if debug_parser_enabled: print(f"DEBUG_PARSER: Warning - Mismatched parentheses. Using: '{param_section_text}'")
        else: param_section_text = text_after_object_name
        if debug_parser_enabled: print(f"DEBUG_PARSER: Isolated param section:\n---\n'{param_section_text}'\n---")
    else:
        if debug_parser_enabled: print(f"DEBUG_PARSER: Could not isolate header/param section.")
        return params
    if not param_section_text.strip():
        if debug_parser_enabled: print(f"DEBUG_PARSER: Param section is empty.")
        return params

    param_regex_str = r"""
        @(?P<name>\w+)
        [\s\r\n]+
        (?P<type_declaration>
            (?:\[?(?:[\w\s\.]+?)\]?\.\[?[\w\s\.]+?\]? | \[?[\w\s\.]+?\]?)
            (?: [\s\r\n]* \(\s*(?P<size>MAX|[\d\s,]+)\s*\) )?
            (?: [\s\r\n]* \(TRANSLATOR\) )?
        )
        (?: 
            [\s\r\n]*=[\s\r\n]*
            (?P<default>
                NULL\b |
                N?'(?:[^']|'')*?' |
                0x[0-9a-fA-F]+ |
                [\-\+]?\b(?:\d+\.\d*|\.\d+|\d+)\b(?:[eE][\-\+]?\d+)? |
                (?:(?:\[?[\w\.]+\]?\.)?\[?[\w\.]+\]?)\s*\( (?: [^()'] | N?'(?:[^']|'')*?' )*? \) |
                @\w+
            )
        )?
        (?:[\s\r\n]+(?P<output>OUTPUT|OUT))?
        (?:[\s\r\n]+(?P<readonly>READONLY))?
    """
    param_regex = re.compile(param_regex_str, re.VERBOSE | re.IGNORECASE)
    declarations = re.split(r',(?=[\s\r\n]*@)', param_section_text)
    
    if debug_parser_enabled:
        print(f"DEBUG_PARSER: Split declarations for '{object_name_for_debug}': {declarations}")

    for i, decl_part in enumerate(declarations):
        clean_decl_part = decl_part.strip()
        if debug_parser_enabled:
            print(f"DEBUG_PARSER: Processing declaration part #{i+1}: '{clean_decl_part}'")
        if not clean_decl_part.startswith('@'):
            if debug_parser_enabled: print(f"DEBUG_PARSER: Skipping part, no @: '{clean_decl_part}'")
            continue
        match = param_regex.match(clean_decl_part)
        if match:
            param_data = match.groupdict()
            p_name = "@" + param_data['name']
            full_type_str = param_data['type_declaration'].strip() if param_data['type_declaration'] else None
            default_val_cleaned = param_data['default'].strip() if param_data['default'] else None
            if default_val_cleaned and default_val_cleaned.upper() == 'NULL': default_val_cleaned = "NULL"
            params[p_name] = {
                'type_from_def': full_type_str, 'default_value_from_def': default_val_cleaned,
                'is_output_from_def': bool(param_data['output']), 'is_readonly_from_def': bool(param_data['readonly']),
                'full_declaration_from_def': match.group(0).strip(), 'size_from_def': param_data.get('size')}
            if debug_parser_enabled: print(f"DEBUG_PARSER: SUCCESS - Matched for {p_name}: {params[p_name]}")
        elif debug_parser_enabled: print(f"DEBUG_PARSER: FAIL - No regex match for param part: '{clean_decl_part}'")
    if debug_parser_enabled:
        if not params and param_section_text.strip(): print(f"DEBUG_PARSER: WARNING - No params matched from non-empty section.")
        print(f"DEBUG_PARSER: --- End Processing Definition for '{object_name_for_debug}' --- Result: {params}")
    return params


def extract_special_comment_block(definition_text, block_tag="code"):
    if not definition_text: return None
    pattern = re.compile(r"/\*\s*" + re.escape(block_tag) + r"\s*([\s\S]*?)\s*\*/", re.IGNORECASE | re.DOTALL)
    match = pattern.search(definition_text)
    return match.group(1).strip() if match else None

def get_framework_objects_info(framework_object_name_patterns, local_args):
    global _framework_api_details_cache
    if not local_args.rediscover_api and _framework_api_details_cache.get("api_objects"):
        return _framework_api_details_cache.get("api_objects", [])
    print("FRAMEWORK_API: Discovering framework objects and parameters from DB...")
    objects_info, name_conditions_list = [], []
    for pattern in framework_object_name_patterns:
        clean_pattern = pattern.replace('dbo.','').strip().replace('[','').replace(']','')
        if clean_pattern: name_conditions_list.append(f"so.name LIKE '{clean_pattern}'")
    if not name_conditions_list:
        _framework_api_details_cache["api_objects"], _framework_api_details_cache["metadata"]["source"] = [], "db_no_patterns"
        return []
    name_conditions_sql_fragment = " OR ".join(name_conditions_list)
    sql_objects = f"""SELECT s.name AS SchemaName, so.name AS ObjectName, so.object_id AS ObjectId, 
                           RTRIM(so.type) AS ObjectTypeShort, so.type_desc AS ObjectTypeDesc, 
                           sm.definition AS DefinitionText
                    FROM sys.objects AS so JOIN sys.schemas AS s ON so.schema_id = s.schema_id
                    LEFT JOIN sys.sql_modules AS sm ON so.object_id = sm.object_id
                    WHERE so.type IN ('P', 'FN', 'IF', 'TF') AND ({name_conditions_sql_fragment}) ORDER BY s.name, so.name;"""
    framework_objects = execute_query(sql_objects)
    if not framework_objects:
        _framework_api_details_cache["api_objects"], _framework_api_details_cache["metadata"]["source"] = [], "db_no_objects_found"
        return []
    object_ids = [obj['ObjectId'] for obj in framework_objects if obj['ObjectId']]
    if not object_ids:
        _framework_api_details_cache["api_objects"], _framework_api_details_cache["metadata"]["source"] = framework_objects, "db_objects_no_ids"
        return framework_objects
    safe_object_ids_str = ','.join(map(str, [int(oid) for oid in object_ids]))
    params_from_sys = {}
    sql_sys_params = f"""SELECT p.object_id, p.name AS ParameterNameSys, TYPE_NAME(p.user_type_id) AS SystemType,
                               p.max_length AS MaxLengthBytes, p.precision AS Precision, p.scale AS Scale,
                               p.is_output AS IsOutputSys, p.parameter_id AS ParameterOrder
                        FROM sys.parameters AS p WHERE p.object_id IN ({safe_object_ids_str}) ORDER BY p.object_id, p.parameter_id;"""
    sys_param_rows = execute_query(sql_sys_params)
    if sys_param_rows:
        for row in sys_param_rows: params_from_sys.setdefault(row['object_id'], []).append(row)
    
    pre_parsed_defaults = {}
    # Use the SQL_VIEW_FOR_PARAM_INFO global variable
    view_schema, view_table_name = SQL_VIEW_FOR_PARAM_INFO.split('.') if '.' in SQL_VIEW_FOR_PARAM_INFO else ('dbo', SQL_VIEW_FOR_PARAM_INFO)
    view_exists_query = f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{view_schema}' AND TABLE_NAME = '{view_table_name}';"
    view_exists = execute_query(view_exists_query, fetch_one=True)

    if view_exists:
        print(f"FRAMEWORK_API: Querying SQL View '{SQL_VIEW_FOR_PARAM_INFO}' for pre-parsed defaults...")
        # Adjust columns if your view has different names or more info (like is_output_from_view)
        sql_view_params = f"""SELECT object_id, parameter_name, is_optional, default_value 
                              FROM {SQL_VIEW_FOR_PARAM_INFO} WHERE object_id IN ({safe_object_ids_str});"""
        view_param_rows = execute_query(sql_view_params)
        if view_param_rows:
            for row in view_param_rows:
                pre_parsed_defaults.setdefault(row['object_id'], {})[row['parameter_name']] = {
                    'is_optional_from_view': bool(row['is_optional']),
                    'default_value_from_view': row['default_value']}
        else: print(f"FRAMEWORK_API: No data from SQL View '{SQL_VIEW_FOR_PARAM_INFO}'. Python parsing for defaults.")
    else: print(f"FRAMEWORK_API: SQL View '{SQL_VIEW_FOR_PARAM_INFO}' not found. Python parsing for defaults.")

    for obj in framework_objects:
        parsed_params_from_py_def = {}
        if not obj['DefinitionText']: print(f"WARNING_PARSER: DefinitionText for {obj['SchemaName']}.{obj['ObjectName']} is NULL.")
        else: parsed_params_from_py_def = parse_sql_parameters_from_definition(obj['DefinitionText'], obj['ObjectName'], local_args)
        final_params, obj_type_short = [], obj['ObjectTypeShort']
        if obj_type_short in ('FN', 'IF', 'TF'):
            sys_return_param = next((p for p in params_from_sys.get(obj['ObjectId'], []) if p['ParameterOrder'] == 0), None)
            if sys_return_param:
                type_from_py_def_return = None
                if obj['DefinitionText']:
                    def_return_match = re.search(r'RETURNS\s+(TABLE\s*\(.*?\)|TABLE\s+@\w+\s+TABLE\s*\(.*?\)|(?:\[?[\w\.]+\]?\.)?\[?[\w\.]+\]?(?:\s*\(\s*(?:MAX|[\d\s,]+)\s*\))?)\s*(?:WITH|AS|BEGIN)', obj['DefinitionText'], re.IGNORECASE | re.DOTALL)
                    type_from_py_def_return = def_return_match.group(1).strip() if def_return_match else sys_return_param['SystemType']
                if type_from_py_def_return and type_from_py_def_return.upper().startswith("TABLE"): type_from_py_def_return = "TABLE" 
                final_params.append({"name": "[Return Value]", "type_from_sys": sys_return_param['SystemType'], "type_from_def": type_from_py_def_return,
                                     "max_length_bytes": sys_return_param['MaxLengthBytes'], "precision": sys_return_param['Precision'], "scale": sys_return_param['Scale'],
                                     "is_output": True, "default_value": None, "has_default": False, "is_readonly": False, "order": 0, "full_declaration_from_def": None})
        for sys_p in params_from_sys.get(obj['ObjectId'], []):
            if sys_p['ParameterOrder'] == 0 and obj_type_short in ('FN', 'IF', 'TF'): continue
            param_name_sys = sys_p['ParameterNameSys']
            view_info = pre_parsed_defaults.get(obj['ObjectId'], {}).get(param_name_sys, {})
            default_val_from_view, has_default_from_view = view_info.get('default_value_from_view'), view_info.get('is_optional_from_view', False)
            py_def_info = parsed_params_from_py_def.get(param_name_sys, {})
            type_from_py_def, default_val_from_py_def = py_def_info.get('type_from_def'), py_def_info.get('default_value_from_def')
            is_output_from_py_def, is_readonly_from_py_def = py_def_info.get('is_output_from_def', False), py_def_info.get('is_readonly_from_def', False)
            full_decl_from_py_def = py_def_info.get('full_declaration_from_def')
            final_default_value, final_has_default = (default_val_from_view, has_default_from_view) if view_info else (default_val_from_py_def, default_val_from_py_def is not None)
            final_is_output = is_output_from_py_def or bool(sys_p['IsOutputSys'])
            final_params.append({"name": param_name_sys, "type_from_sys": sys_p['SystemType'], "type_from_def": type_from_py_def,
                                 "max_length_bytes": sys_p['MaxLengthBytes'], "precision": sys_p['Precision'], "scale": sys_p['Scale'],
                                 "is_output": final_is_output, "default_value": final_default_value, "has_default": final_has_default,
                                 "is_readonly": is_readonly_from_py_def, "order": sys_p['ParameterOrder'], "full_declaration_from_def": full_decl_from_py_def})
        for p_name_py, p_info_py in parsed_params_from_py_def.items():
            if not any(p['name'] == p_name_py for p in final_params):
                 original_case_name_match = re.match(r"@(\w+)", p_info_py.get('full_declaration_from_def',''))
                 original_case_name = "@"+original_case_name_match.group(1) if original_case_name_match else p_name_py
                 def_default_val_py = p_info_py.get('default_value_from_def')
                 final_params.append({"name": original_case_name, "type_from_sys": None, "type_from_def": p_info_py.get('type_from_def'),
                                      "max_length_bytes": None, "precision": None, "scale": None, "is_output": p_info_py.get('is_output_from_def', False),
                                      "default_value": def_default_val_py, "has_default": bool(def_default_val_py is not None), "is_readonly": p_info_py.get('is_readonly_from_def', False),
                                      "order": len(final_params) + 1000, "full_declaration_from_def": p_info_py.get('full_declaration_from_def')})
        objects_info.append({"schema_name": obj['SchemaName'], "object_name": obj['ObjectName'], "object_type": obj['ObjectTypeDesc'],
                             "object_type_short": obj_type_short, "parameters": sorted(final_params, key=lambda p: p.get('order', 999)),
                             "embedded_example": extract_special_comment_block(obj['DefinitionText'], "code"),
                             "embedded_description": extract_special_comment_block(obj['DefinitionText'], "help.description"), "co_occurrence_stats": {}})
    _framework_api_details_cache["api_objects"], _framework_api_details_cache["metadata"]["source"] = objects_info, "db_discovery_full_with_view_attempt"
    return objects_info

def get_action_scripts_source(table_name, sql_column_name_options, local_args, id_col_name='id', name_col_name='name', max_scripts=50):
    actual_cols_info = get_actual_columns_for_table('dbo', table_name, local_args)
    if not actual_cols_info: return []
    sql_col_to_use_original_case = next((c['name'] for option in sql_column_name_options for c in actual_cols_info if c['name'].lower() == option.lower()), None)
    if not sql_col_to_use_original_case: return []
    select_spec = [(sql_col_to_use_original_case, 'sql_source')]
    id_col_original_case = next((c['name'] for c in actual_cols_info if c['name'].lower() == id_col_name.lower()), None)
    if id_col_original_case: select_spec.append((id_col_original_case, 'action_id'))
    name_col_original_case = next((c['name'] for c in actual_cols_info if c['name'].lower() == name_col_name.lower()), None)
    if name_col_original_case: select_spec.append((name_col_original_case, 'action_name'))
    order_by = f"[{id_col_original_case}] DESC" if id_col_original_case else ""
    query, _ = build_safe_select_query('dbo', table_name, select_spec, local_args, order_by_clause=order_by, top_n=max_scripts)
    if not query: return []
    scripts = execute_query(query)
    if scripts:
        for script in scripts: script['source_table'] = table_name
    return scripts if scripts else []


def get_real_usage_examples(sp_name_to_search, local_args, max_examples=3):
    examples, corpus_to_search, found_count = [], _action_scripts_corpus_cache.get("scripts", []), 0
    if not corpus_to_search: return []
    pattern = r'\b(?:EXEC\s+)?(?:dbo\.)?' + re.escape(sp_name_to_search) + r'\b'
    for script_info in corpus_to_search:
        sql_text = script_info.get('sql_source')
        if sql_text and re.search(pattern, sql_text, re.IGNORECASE):
            examples.append(script_info); found_count +=1
            if found_count >= max_examples: break
    return examples

def analyze_action_script_content(sql_source_text, framework_api_ref):
    findings = {'sps_called': [], 'udfs_called': [], 'context_vars_found': set()}
    if not sql_source_text or not framework_api_ref or not isinstance(framework_api_ref, list) or not all(isinstance(item, dict) for item in framework_api_ref): return findings
    sp_map = {item['object_name'].lower(): f"{item['schema_name']}.{item['object_name']}" for item in framework_api_ref if item.get('object_type_short') == 'P'}
    udf_map = {item['object_name'].lower(): f"{item['schema_name']}.{item['object_name']}" for item in framework_api_ref if item.get('object_type_short') in ('FN', 'IF', 'TF')}
    exec_matches = re.finditer(r'\bEXEC\s+(?:(\[?[\w\s\.]+\]?)\s*\.\s*)?(\[?[\w\s\.]+\]?)\b', sql_source_text, re.IGNORECASE)
    for match in exec_matches:
        sp_name_part = match.group(2).replace('[','').replace(']','').replace('"','')
        if sp_name_part.lower() in sp_map: findings['sps_called'].append(sp_map[sp_name_part.lower()])
    udf_call_matches = re.finditer(r'\b(?:(\[?[\w\s\.]+\]?)\s*\.\s*)?(\[?[\w\s\.]+\]?)\s*\(', sql_source_text, re.IGNORECASE)
    for match in udf_call_matches:
        udf_name_part = match.group(2).replace('[','').replace(']','').replace('"','')
        if udf_name_part.lower() in udf_map: findings['udfs_called'].append(udf_map[udf_name_part.lower()])
    context_vars_str = os.getenv('TSQL_APP_CONTEXT_VARIABLES', '@card_id,@id,@ids,@user_id,@card_name,@user_name,@basetable,@tablename,@parent_id,@parent_card_id,@path,@is_form,@is_new,@current_card_action_id')
    context_vars = [cv.strip() for cv in context_vars_str.split(',') if cv.strip()]
    for var in context_vars:
        if re.search(re.escape(var) + r'\b', sql_source_text, re.IGNORECASE): findings['context_vars_found'].add(var)
    findings['sps_called'], findings['udfs_called'] = sorted(list(set(findings['sps_called']))), sorted(list(set(findings['udfs_called'])))
    return findings


def update_co_occurrence_stats(framework_api_details_list, all_script_analysis_findings):
    if not framework_api_details_list or not all_script_analysis_findings: return
    api_object_map_full_name = {f"{obj.get('schema_name','dbo')}.{obj['object_name']}".lower(): obj for obj in framework_api_details_list}
    for finding_detail in all_script_analysis_findings:
        analysis_content = finding_detail.get("analysis_findings", {})
        all_objects_in_script = set(analysis_content.get('sps_called', [])) | set(analysis_content.get('udfs_called', []))
        for obj_fullname_A_lower in (name.lower() for name in all_objects_in_script):
            api_obj_A = api_object_map_full_name.get(obj_fullname_A_lower)
            if not api_obj_A: continue
            current_stats = api_obj_A.get('co_occurrence_stats', {})
            if not isinstance(current_stats, Counter): api_obj_A['co_occurrence_stats'] = Counter(current_stats if isinstance(current_stats, dict) else {})
            for obj_fullname_B_lower in (name.lower() for name in all_objects_in_script):
                if obj_fullname_A_lower == obj_fullname_B_lower: continue
                obj_fullname_B_original_case = next((name for name in all_objects_in_script if name.lower() == obj_fullname_B_lower), obj_fullname_B_lower)
                api_obj_A['co_occurrence_stats'][obj_fullname_B_original_case] += 1
    for api_obj in framework_api_details_list:
        if 'co_occurrence_stats' in api_obj and isinstance(api_obj['co_occurrence_stats'], Counter):
            api_obj['co_occurrence_stats'] = dict(api_obj['co_occurrence_stats'])

def generate_simple_training_examples(framework_api_details, output_filename="simple_training_examples.json"):
    """
    Generate simple training examples showing how to use stored procedures.
    """
    print(f"TRAINING: Creating simple training examples...")
    
    training_examples = []
    
    # Get only stored procedures (not functions)
    procedures = [obj for obj in framework_api_details if obj.get('object_type_short') == 'P']
    
    if not procedures:
        print("No procedures found to create examples for.")
        return []
    
    # Create 5 simple examples
    for i, proc in enumerate(procedures[:5]):  # Only first 5 procedures
        proc_name = proc['object_name']
        schema_name = proc.get('schema_name', 'dbo')
        
        # Get parameters for this procedure
        params = [p for p in proc.get('parameters', []) if p.get('name') != '[Return Value]']
        
        # Create a simple script example
        script_lines = []
        script_lines.append(f"-- Example {i+1}: How to use {proc_name}")
        script_lines.append("")
        
        # Add parameter declarations
        if params:
            script_lines.append("-- Declare parameters")
            for param in params[:3]:  # Only show first 3 parameters
                param_name = param['name']
                param_type = param.get('type_from_sys', 'nvarchar(255)')
                
                # Create simple sample values
                if 'id' in param_name.lower():
                    sample_value = "123"
                elif 'name' in param_name.lower():
                    sample_value = "N'Sample Name'"
                elif param_type.lower() == 'bit':
                    sample_value = "1"
                else:
                    sample_value = "N'sample value'"
                
                script_lines.append(f"DECLARE {param_name} {param_type} = {sample_value};")
            script_lines.append("")
        
        # Add the procedure call
        script_lines.append("-- Call the procedure")
        exec_line = f"EXEC {schema_name}.{proc_name}"
        
        if params:
            param_list = []
            for param in params[:3]:
                param_list.append(f"{param['name']} = {param['name']}")
            exec_line += " " + ", ".join(param_list)
        
        script_lines.append(exec_line + ";")
        
        # Create the example
        example = {
            "example_number": i + 1,
            "procedure_name": f"{schema_name}.{proc_name}",
            "description": f"Simple example showing how to call {proc_name}",
            "sql_script": "\n".join(script_lines),
            "learning_goal": f"Learn basic usage of {proc_name}"
        }
        
        training_examples.append(example)
    
    # Save to file
    training_data = {
        "created_date": datetime.now().isoformat(),
        "total_examples": len(training_examples),
        "description": "Simple training examples for TSQL.APP framework procedures",
        "examples": training_examples
    }
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=4, default=str)
        print(f"TRAINING: Saved {len(training_examples)} examples to {output_filename}")
    except Exception as e:
        print(f"TRAINING: Error saving file: {e}")
    
    return training_examples
# --- Main Execution ---
if __name__ == "__main__":
    script_args_global = parser.parse_args()
    if script_args_global.force_full_rediscover:
        script_args_global.rediscover_schema = True
        script_args_global.rediscover_api = True
        script_args_global.refresh_action_scripts = True
    print("--- TSQL.APP Training Data Generator ---")
    if script_args_global.debug_parser: print("!!! Detailed Parser Debugging ENABLED !!!")

    if script_args_global.test_sp:
        print(f"\n--- TEST MODE: Analyzing Specific Object: {script_args_global.test_sp} ---")
        _discovered_schema_cache, _framework_api_details_cache, _action_scripts_corpus_cache = \
            {"metadata": {"source": "test_mode_init"}, "tables": {}}, \
            {"metadata": {"source": "test_mode_init"}, "api_objects": []}, \
            {"metadata": {"source": "test_mode_init"}, "scripts": []}
        current_test_args = argparse.Namespace(**vars(script_args_global))
        current_test_args.rediscover_api, current_test_args.rediscover_schema = True, True
        schema_name_to_test, object_name_to_test = ('dbo', script_args_global.test_sp)
        if '.' in script_args_global.test_sp:
            parts = script_args_global.test_sp.split('.', 1)
            if len(parts) == 2: schema_name_to_test, object_name_to_test = parts[0], parts[1]
        test_object_info_list = get_framework_objects_info([f"{schema_name_to_test}.{object_name_to_test}"], current_test_args)
        if test_object_info_list:
            test_object_info = next((obj for obj in test_object_info_list if obj['object_name'].lower() == object_name_to_test.lower() and obj['schema_name'].lower() == schema_name_to_test.lower()), None)
            if test_object_info:
                print("\n--- Parsed Object Details ---"); print(json.dumps(test_object_info, indent=4, default=str))
                print(f"\n--- Fetching Real Usage Examples (max {script_args_global.max_examples_for_test_sp}) ---")
                corpus_loaded_for_test = False
                if not current_test_args.refresh_action_scripts: corpus_loaded_for_test = load_memory_file(ACTION_SCRIPTS_CORPUS_FILE, _action_scripts_corpus_cache)
                if not _action_scripts_corpus_cache.get("scripts") or (current_test_args.refresh_action_scripts and not corpus_loaded_for_test):
                    mca, maa = 50, 20
                    _action_scripts_corpus_cache["scripts"] = (get_action_scripts_source('api_card_actions', ['unparsed_sql', 'sql_script'], current_test_args, max_scripts=mca) or []) + \
                                                              (get_action_scripts_source('api_actions', ['sql_script', 'unparsed_sql'], current_test_args, max_scripts=maa) or [])
                examples = get_real_usage_examples(object_name_to_test, current_test_args, max_examples=script_args_global.max_examples_for_test_sp)
                if examples:
                    print("\n--- Real Usage Examples ---")
                    for i, ex in enumerate(examples): print(f"Ex {i+1} (From: {ex.get('source_table')}, ID: {ex.get('action_id')}, Name: {ex.get('action_name','N/A')} ):\n---\n{ex.get('sql_source')}\n---")
                else: print("No real usage examples found.")
            else: print(f"Object {script_args_global.test_sp} not found after fetch (list was: {test_object_info_list}).")
        else: print(f"Could not retrieve info for object: {script_args_global.test_sp}")
        exit()

    if script_args_global.test_action_script_id is not None:
        print(f"\n--- TEST MODE: Analyzing Action Script ID {script_args_global.test_action_script_id} from table {script_args_global.test_action_script_table} ---")
        _discovered_schema_cache = {"metadata": {"source": "test_mode_init"}, "tables": {}}; load_memory_file(SCHEMA_MEMORY_FILE, _discovered_schema_cache)
        _framework_api_details_cache = {"metadata": {"source": "test_mode_init"}, "api_objects": []}
        api_loaded_for_test = load_memory_file(API_DETAILS_MEMORY_FILE, _framework_api_details_cache)
        current_framework_api_for_test = _framework_api_details_cache.get("api_objects", [])
        if not current_framework_api_for_test or (script_args_global.rediscover_api and not api_loaded_for_test):
            patterns_for_test = os.getenv('FRAMEWORK_OBJECT_PATTERNS', 'sp_api_%,sp_sys_%,context_%,dbo.IsEmpty,dbo.HasRole,dbo.abc%,dbo.regex_%').split(',')
            current_framework_api_for_test = get_framework_objects_info(patterns_for_test, script_args_global)
        id_col_name, sql_col_options = 'id', ['unparsed_sql', 'sql_script']
        actual_cols_info_test = get_actual_columns_for_table('dbo', script_args_global.test_action_script_table, script_args_global)
        if not actual_cols_info_test: print(f"Table {script_args_global.test_action_script_table} not found. Exiting."); exit()
        id_col_actual_test = next((c['name'] for c in actual_cols_info_test if c['name'].lower() == id_col_name.lower()), None)
        sql_col_actual_test = next((c['name'] for option in sql_col_options for c in actual_cols_info_test if c['name'].lower() == option.lower()), None)
        if not id_col_actual_test or not sql_col_actual_test: print(f"Required columns not in {script_args_global.test_action_script_table}. Exiting."); exit()
        select_spec_test = [(sql_col_actual_test, 'sql_source'), (id_col_actual_test, 'action_id')]
        name_col_actual_test = next((c['name'] for c in actual_cols_info_test if c['name'].lower() == 'name'), None)
        if name_col_actual_test: select_spec_test.append((name_col_actual_test, 'action_name'))
        query_test, _ = build_safe_select_query('dbo', script_args_global.test_action_script_table, select_spec_test, script_args_global, where_clause=f"[{id_col_actual_test}] = ?")
        if not query_test: print(f"Could not build query for specific action script. Exiting."); exit()
        script_info_test = execute_query(query_test, (script_args_global.test_action_script_id,), fetch_one=True)
        if script_info_test and script_info_test.get('sql_source'):
            print(f"\n--- Action Script Source (ID: {script_info_test.get('action_id')}, Name: {script_info_test.get('action_name','N/A')}) ---\n{script_info_test['sql_source']}\n{'-'*30}")
            if current_framework_api_for_test:
                analysis_test = analyze_action_script_content(script_info_test['sql_source'], current_framework_api_for_test)
                print("\n--- Analysis Findings ---"); print(json.dumps(analysis_test, indent=4, default=str))
            else: print("Skipping analysis: framework API details unavailable for test.")
        else: print(f"Action script ID {script_args_global.test_action_script_id} not found or no SQL source in {script_args_global.test_action_script_table}.")
        exit()

    _previous_run_summary = {}; load_memory_file(PREVIOUS_RUN_SUMMARY_FILE, _previous_run_summary)
    schema_loaded, api_loaded, corpus_loaded = False, False, False
    _discovered_schema_cache = {"metadata": {"source": "init_full_run"}, "tables": {}}
    if not script_args_global.rediscover_schema: schema_loaded = load_memory_file(SCHEMA_MEMORY_FILE, _discovered_schema_cache)
    if not _discovered_schema_cache.get("tables") or script_args_global.rediscover_schema: _discovered_schema_cache = {"metadata":{"source":"db_demand_full_run"}, "tables":{}}
    _framework_api_details_cache = {"metadata": {"source": "init_full_run"}, "api_objects": []}
    if not script_args_global.rediscover_api: api_loaded = load_memory_file(API_DETAILS_MEMORY_FILE, _framework_api_details_cache)
    current_framework_api = _framework_api_details_cache.get("api_objects", [])
    if not current_framework_api or script_args_global.rediscover_api:
        patterns = os.getenv('FRAMEWORK_OBJECT_PATTERNS', 'sp_api_%,sp_sys_%,context_%,dbo.IsEmpty,dbo.HasRole,dbo.abc%,dbo.regex_%').split(',')
        current_framework_api = get_framework_objects_info(patterns, script_args_global)
        _framework_api_details_cache["api_objects"] = current_framework_api
    _action_scripts_corpus_cache = {"metadata": {"source": "init_full_run"}, "scripts": []}
    if not script_args_global.refresh_action_scripts: corpus_loaded = load_memory_file(ACTION_SCRIPTS_CORPUS_FILE, _action_scripts_corpus_cache)
    current_action_script_corpus = _action_scripts_corpus_cache.get("scripts", [])
    if not current_action_script_corpus or script_args_global.refresh_action_scripts:
        mca, maa = int(os.getenv('MAX_CARD_ACTIONS_TO_CORPUS', '500')), int(os.getenv('MAX_API_ACTIONS_TO_CORPUS', '500'))
        print(f"ACTION_SCRIPTS_CORPUS: Fetching up to {mca} card actions and {maa} API actions...")
        current_action_script_corpus = (get_action_scripts_source('api_card_actions', ['unparsed_sql', 'sql_script'], script_args_global, max_scripts=mca) or []) + \
                                       (get_action_scripts_source('api_actions', ['sql_script', 'unparsed_sql'], script_args_global, max_scripts=maa) or [])
        _action_scripts_corpus_cache["scripts"] = current_action_script_corpus
    if current_framework_api and current_action_script_corpus:
        for api_obj in current_framework_api: api_obj['real_usage_examples'] = get_real_usage_examples(api_obj['object_name'], script_args_global, 3)
    analyzed_script_patterns_sample, all_script_findings_for_cooccurrence = [], []
    if current_action_script_corpus and current_framework_api:
        print(f"ANALYZING_SCRIPTS: Analyzing {len(current_action_script_corpus)} action scripts from corpus...")
        limit_print_sample = int(os.getenv('LIMIT_PRINT_SCRIPT_ANALYSIS_SAMPLE', '20'))
        for i, script_info in enumerate(current_action_script_corpus):
            sql_text, analysis_result = script_info.get('sql_source'), None
            if sql_text: analysis_result = analyze_action_script_content(sql_text, current_framework_api)
            if analysis_result:
                all_script_findings_for_cooccurrence.append({"analysis_findings": analysis_result})
                if i < limit_print_sample: analyzed_script_patterns_sample.append({**script_info, "analysis_findings": analysis_result, "script_snippet": sql_text[:300] + "..." if sql_text and len(sql_text) > 300 else sql_text})
        needs_cooccurrence_update = script_args_global.rediscover_api or script_args_global.refresh_action_scripts or not api_loaded or not corpus_loaded or \
                                   (current_framework_api and (not current_framework_api[0].get('co_occurrence_stats') if current_framework_api else False) )
        if needs_cooccurrence_update and all_script_findings_for_cooccurrence: 
            relationships = update_co_occurrence_stats(current_framework_api, all_script_findings_for_cooccurrence)
        # Generate simple training examples
    if current_framework_api:
        # Generate framework training materials
        if TRAINING_AVAILABLE:
            try:
                print("\nFRAMEWORK_TRAINING: Starting training data generation...")
                    
                    # If testing a specific procedure, print its details
                    if script_args_global.test_sp:
                        print(f"\n=== TESTING PROCEDURE: {script_args_global.test_sp} ===")
                        test_procedure(current_framework_api, script_args_global.test_sp)
                else:
                    print("INFO: Skipping training material generation as module is not available")
                
                # Restore original stdout
                sys.stdout = original_stdout
                print("\nFRAMEWORK_TRAINING: All files saved to 'training_output/' directory")
                print("Training generation output has been saved to training_output/training_generation_output.txt")
            
            finally:
                # Ensure original stdout is restored even if there's an error
                sys.stdout = original_stdout
                if 'output_file' in locals():
                    output_file.close()
            
        except Exception as e:
            print(f"FRAMEWORK_TRAINING: Error generating training materials: {e}")
            raise
        except Exception as e:
            print(f"FRAMEWORK_TRAINING: Error generating training materials: {e}")

    generate_simple_training_examples(current_framework_api, "simple_training_examples.json")
    current_run_summary = {"generation_timestamp": datetime.now().isoformat(), "total_framework_objects": len(current_framework_api or []),
                           "objects_with_embedded_examples": sum(1 for obj in (current_framework_api or []) if obj.get("embedded_example")),
                           "objects_with_embedded_descriptions": sum(1 for obj in (current_framework_api or []) if obj.get("embedded_description")),
                           "training_generation_status": "success" if TRAINING_AVAILABLE else "not_available", 
                           "objects_with_real_usage_examples": sum(1 for obj in (current_framework_api or []) if obj.get("real_usage_examples")),
                           "total_action_scripts_in_corpus": len(current_action_script_corpus or []),
                           "action_scripts_analyzed_in_detail_sample": len(analyzed_script_patterns_sample),
                           "total_schema_tables_processed_for_discovery": len(_discovered_schema_cache.get("tables", {})),
                           "params_total_in_api": sum(len(obj.get("parameters",[])) for obj in (current_framework_api or []) if obj.get("object_type_short") != 'TF'),
                           "params_parsed_with_defaults_from_def": sum(1 for obj in (current_framework_api or []) for p in obj.get("parameters",[]) if p.get("has_default") and p.get("name") != "[Return Value]"),
                           "params_with_type_from_def": sum(1 for obj in (current_framework_api or []) for p in obj.get("parameters",[]) if p.get("type_from_def") and p.get("name") != "[Return Value]")}
    print("\n--- Smarter Indicators (Current vs. Previous) ---")
    if _previous_run_summary and "generation_timestamp" in _previous_run_summary:
        for key, current_val in current_run_summary.items():
            if key == "generation_timestamp": continue
            prev_val, change_str = _previous_run_summary.get(key, 0), ""
            if isinstance(prev_val, (int, float)) and isinstance(current_val, (int, float)):
                change = current_val - prev_val
                change_str = f", Change: {change:+}" if change != 0 else ", Change: 0"
            print(f"  {key.replace('_',' ').title()}: {current_val} (Prev: {prev_val}{change_str})")
    else:
        print("  No valid previous run summary found to compare against, or this is the first successful summary save.")
        for key, current_val in current_run_summary.items():
            if key == "generation_timestamp": continue
            print(f"  {key.replace('_',' ').title()}: {current_val}")
    final_output_data = {"metadata": {"run_summary": current_run_summary, "schema_memory_source": _discovered_schema_cache.get("metadata",{}).get("source","init"),
                                     "api_memory_source": _framework_api_details_cache.get("metadata",{}).get("source","init"),
                                     "scripts_corpus_source": _action_scripts_corpus_cache.get("metadata",{}).get("source","init"),
                                     "previous_run_summary_was_loaded": bool(_previous_run_summary.get("generation_timestamp"))},
                         "framework_api_reference": current_framework_api,
                         "action_script_analysis_summary": {"total_scripts_in_corpus": len(current_action_script_corpus),
                                                            "scripts_analyzed_in_detail_sample_count": len(analyzed_script_patterns_sample),
                                                            "analysis_samples": analyzed_script_patterns_sample}}
    save_memory_file(TRAINING_GUIDE_OUTPUT_FILE, final_output_data)
    if script_args_global.rediscover_schema or not schema_loaded : save_memory_file(SCHEMA_MEMORY_FILE, _discovered_schema_cache)
    if script_args_global.rediscover_api or not api_loaded : save_memory_file(API_DETAILS_MEMORY_FILE, _framework_api_details_cache)
    if script_args_global.refresh_action_scripts or not corpus_loaded : save_memory_file(ACTION_SCRIPTS_CORPUS_FILE, _action_scripts_corpus_cache)
    save_memory_file(PREVIOUS_RUN_SUMMARY_FILE, current_run_summary.copy())
    print("\n--- Script Finished ---")