## HBase Testing and Data Reading Guide

This document outlines three essential utilities for interacting with HBase in the Formula 1 data platform: connection testing, operations testing, and data reading.

### 1. Connection Testing Utility (`hbase_test_connection.py`)

**Purpose:** Verifies connectivity to the HBase cluster.

**Features:**

| Feature                   | Description                                                        |
| ------------------------- | ------------------------------------------------------------------ |
| Connection Verification | Establishes connection to the configured HBase host.              |
| Table Listing             | Retrieves and displays a list of existing HBase tables.           |
| Configurable Host         | Allows specifying the HBase host.                                  |
| Error Logging             | Provides detailed error messages for connection failures.        |

**Usage Scenarios:**

*   **Initial Setup Verification:** Confirm HBase availability, SSH tunnel functionality, and network connectivity.
*   **Troubleshooting:** Diagnose connection issues and verify configuration.

**Usage Example:**

```bash
python hbase_test_connection.py
```

**Example Output (Success):**

```
Connection successful!
List of tables: ['f1_data', 'f1_reports', ...]
```

**Example Output (Failure):**

```
Error connecting to HBase: [Errno 111] Connection refused
```

### 2. Operations Testing Utility (`hbase_test_operations.py`)

**Purpose:** Validates basic CRUD operations on HBase tables.

**Features:**

| Feature                   | Description                                                              |
| ------------------------- | ------------------------------------------------------------------------ |
| Table Creation Testing    | Verifies the creation of new tables with specified column families.       |
| Data Insertion Verification | Tests the insertion of records into HBase tables.                        |
| Read Operation Validation | Confirms data retrieval from HBase tables.                               |
| Column Family Management  | Demonstrates the creation and use of multiple column families.          |
| Automated Cleanup         | Deletes the test table after completion.                               |

**Testing Workflow:**

1. **Connection Phase:** Establish connection and prepare the environment.
2. **Table Management:** Create a test table (`test_table`) with `driver` and `car` column families.
3. **Data Operations:**
    *   **Insertion:** Insert test records.
    *   **Verification:** Read back inserted data.
    *   **Reading:** Perform various read operations.
    *   **Validation:** Compare retrieved data with inserted data.
4. **Cleanup:** Delete the `test_table` and close the connection.

**Usage Example:**

```bash
python hbase_test_operations.py
```

**Example Output (Success):**

```
Connection successful!
Creating table 'test_table'...
Table 'test_table' created successfully.
Inserting data...
Data inserted successfully.
Reading data...
Row 1, Column driver:name: Verstappen
Row 1, Column car:number: 1
...
Data read and verified successfully.
Deleting table 'test_table'...
Table 'test_table' deleted successfully.
```

### 3. Data Reading Utility (`hbase_read.py`)

**Purpose:** Provides a tool for accessing and retrieving Formula 1 data from HBase.

**Features:**

| Category        | Feature                          | Description                                                                   |
| --------------- | -------------------------------- | ----------------------------------------------------------------------------- |
| **Data Access** | Meeting Information Retrieval    | Fetches race meeting details (location, date, name).                          |
|                 | Session Data Access              | Retrieves information about race sessions (Practice, Qualifying, Race).        |
|                 | Driver Information Extraction    | Accesses driver data (code, name, team).                                      |
|                 | Telemetry Data Reading           | Retrieves telemetry data (speed, RPM, gear).                                  |
| **Output Formatting** | Colored Console Output         | Uses color coding for readability.                                          |
|                 | Structured Data Presentation     | Organizes data into clear sections with headers.                               |
|                 | Clear Section Organization       | Divides output into logical sections (meetings, sessions, drivers, telemetry). |
|                 | Human-Readable Formatting        | Presents data in a user-friendly format.                                     |
| **Data Selection**  | Random Record Sampling         | Allows retrieval of a random sample of records.                              |
|                 | Driver-Specific Queries          | Enables fetching data for specific drivers.                                   |
|                 | Session-Based Filtering        | Supports filtering data by session key.                                       |
|                 | Column Family Selection          | Allows selecting specific column families for retrieval.                       |

**Components:**

*   **`F1DataReader` Class:**
    *   **Initialization:** Establishes connection, selects the target table (`f1_data`).
    *   **Data Retrieval Methods:** `get_meeting_info()`, `get_session_info()`, `get_driver_data()`, `get_telemetry_data()`.
    *   **Formatting Utilities:** `convert_binary_data()`, `pretty_print_meeting()`, `pretty_print_session()`, `pretty_print_driver()`, `pretty_print_telemetry()`.

**Usage Example:**

```bash
python hbase_read.py
```

**Example Output (Partial):**

```
####################
#        MEETING       #
####################
Meeting Key: 1120
Official Event Name: FORMULA 1 ROLEX AUSTRALIAN GRAND PRIX 2024
Event Format: conventional
Location: Albert Park
Country: Australia
...
####################
#        SESSION       #
####################
Session Key: 1120_1_1
Session Name: Practice 1
Session Type: Practice
...
####################
#        DRIVER        #
####################
Driver Code: VER
Driver Number: 1
Team Name: Red Bull Racing
...
####################
#     TELEMETRY      #
####################
Time: 17:33:27.508000
RPM: 10890
Speed: 278
Gear: 8
...
```

### 4. Operational Guidelines

**Setup Requirements:**

| Requirement           | Details                                                        |
| --------------------- | -------------------------------------------------------------- |
| **System Prerequisites** | Python 3.8+, HBase Thrift Server, SSH Tunnel (if remote)       |
| **Python Packages**   | `happybase`, `colorama`                                        |
| **Configuration**     | Host address, port (default: 9090), logging levels, table names |

**Usage Procedures:**

| Step             | Command                        | Verification Points                                                              |
| ---------------- | ------------------------------ | -------------------------------------------------------------------------------- |
| **Connection**   | `python hbase_test_connection.py` | Successful connection, table list, no errors.                                    |
| **Operations**   | `python hbase_test_operations.py` | `test_table` creation, data insertion/reading, `test_table` deletion.         |
| **Data Reading** | `python hbase_read.py`          | Output formatting, color coding, expected data retrieval and display.           |

**Troubleshooting Guide:**

| Issue                  | Symptom                             | Solution                                                                                             |
| ---------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Connection Problems** | `Connection refused`, `Timeout`     | Verify Thrift server, host/port config, SSH tunnel, firewall rules.                               |
| **Data Access Issues**  | `Table does not exist`, `Column family does not exist` | Verify table/column family existence in HBase, check names in scripts, confirm user permissions. |
| **Output Problems**    | Incorrect formatting, missing colors | Check terminal ANSI support, verify `colorama` initialization, monitor output size.                   |
