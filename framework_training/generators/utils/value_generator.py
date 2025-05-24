from typing import Dict, List, Optional
import random
import string


def generate_sample_value(param_name: str, param_type: str) -> str:
    """Generate realistic sample values based on parameter name and type."""
    # Base types
    base_types = {
        'int': random.randint(1, 1000),
        'bigint': random.randint(1, 1000000),
        'smallint': random.randint(1, 100),
        'tinyint': random.randint(1, 255),
        'bit': random.choice([0, 1]),
        'decimal': round(random.uniform(1, 1000), 2),
        'numeric': round(random.uniform(1, 1000), 2),
        'float': round(random.uniform(1, 1000), 2),
        'real': round(random.uniform(1, 1000), 2),
        'money': round(random.uniform(1, 1000), 2),
        'smallmoney': round(random.uniform(1, 1000), 2),
        'date': random_date(),
        'datetime': random_datetime(),
        'datetime2': random_datetime(),
        'datetimeoffset': random_datetime(),
        'smalldatetime': random_datetime(),
        'time': random_time()
    }
    
    # Generate value based on type
    if param_type.lower() in base_types:
        return str(base_types[param_type.lower()])
    
    # Handle string types
    if 'char' in param_type.lower() or 'varchar' in param_type.lower():
        return generate_string_value(param_name)
    
    if 'nchar' in param_type.lower() or 'nvarchar' in param_type.lower():
        return generate_unicode_string(param_name)
    
    if 'binary' in param_type.lower() or 'varbinary' in param_type.lower():
        return generate_binary_value()
    
    # Handle special cases based on parameter name
    if 'id' in param_name.lower():
        return str(random.randint(1, 1000))
    
    if 'name' in param_name.lower():
        return generate_name()
    
    if 'email' in param_name.lower():
        return generate_email()
    
    if 'address' in param_name.lower():
        return generate_address()
    
    if 'phone' in param_name.lower():
        return generate_phone_number()
    
    # Default to string if all else fails
    return generate_string_value(param_name)


def random_date() -> str:
    """Generate a random date."""
    year = random.randint(2000, 2025)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Safe to avoid month-specific days
    return f"{year}-{month:02d}-{day:02d}"


def random_datetime() -> str:
    """Generate a random datetime."""
    year = random.randint(2000, 2025)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"


def random_time() -> str:
    """Generate a random time."""
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"


def generate_string_value(param_name: str) -> str:
    """Generate a generic string value."""
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_unicode_string(param_name: str) -> str:
    """Generate a unicode string value."""
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_letters + string.digits + 'äöüß', k=length))


def generate_binary_value() -> str:
    """Generate a binary value."""
    length = random.randint(1, 16)
    return '0x' + ''.join(random.choices('0123456789ABCDEF', k=length*2))


def generate_name() -> str:
    """Generate a realistic name."""
    first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Sarah', 'Mike', 'Emily']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Taylor', 'Anderson']
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_email() -> str:
    """Generate a realistic email address."""
    domains = ['example.com', 'company.com', 'mail.com', 'gmail.com']
    return f"{generate_string_value('email')}@{random.choice(domains)}"


def generate_address() -> str:
    """Generate a realistic address."""
    street_names = ['Main St', 'Park Ave', 'Oak St', 'Maple Ave', 'Elm St']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    states = ['NY', 'CA', 'IL', 'TX', 'AZ']
    
    street_number = random.randint(1, 9999)
    return f"{street_number} {random.choice(street_names)}, {random.choice(cities)}, {random.choice(states)}"


def generate_phone_number() -> str:
    """Generate a realistic phone number."""
    area_code = random.randint(200, 999)
    first_part = random.randint(200, 999)
    second_part = random.randint(1000, 9999)
    return f"({area_code}) {first_part}-{second_part}"
