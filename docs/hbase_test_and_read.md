# HBase Testing and Data Reading Guide

## 1. Introduction

This document provides a comprehensive guide to testing and interacting with HBase within the context of the Formula 1 data analytics platform. It covers three essential utilities:

1. **Connection Testing Utility**: Verifies the ability to establish a connection to the HBase cluster.
2. **Operations Testing Utility**: Tests basic CRUD (Create, Read, Update, Delete) operations on HBase tables.
3. **Data Reading Utility**: Demonstrates how to access and retrieve Formula 1 data stored in HBase, with options for formatted output and selective data retrieval.

These utilities are crucial for ensuring the proper functioning of the HBase infrastructure, validating data integrity, and providing a practical way to access the stored Formula 1 data for analysis and visualization.

## 2. Connection Testing Utility

### 2.1. Purpose

The connection testing utility (`hbase_test_connection.py`) serves as a fundamental tool for verifying the connectivity to the HBase cluster. It's typically the first step in troubleshooting connection issues and ensuring that the HBase setup is accessible.

### 2.2. Features

-   **Basic Connection Verification**: Establishes a connection to the configured HBase host using the Thrift protocol.
-   **Table Listing**: Retrieves and displays a list of existing tables in the HBase database, confirming successful communication.
-   **Configurable Host Settings**: Allows users to specify the HBase host, making it adaptable to different cluster configurations.
-   **Comprehensive Error Logging**: Provides detailed error messages in case of connection failures, aiding in troubleshooting.

### 2.3. Usage Scenarios

#### 2.3.1. Initial Setup Verification

-   **Confirming HBase Availability**: After setting up the EMR cluster and HBase, this utility can be used to verify that the HBase service is running and accessible.
-   **Verifying SSH Tunnel Functionality**: When connecting to a remote HBase instance through an SSH tunnel, this utility helps confirm that the tunnel is correctly configured.
-   **Checking Network Connectivity**: It can be used to diagnose basic network connectivity issues between the client machine and the HBase cluster.

#### 2.3.2. Troubleshooting

-   **Connection Issues Diagnosis**: When encountering problems connecting to HBase from other applications or scripts, this utility can isolate whether the issue lies in the connection setup or elsewhere.
-   **Configuration Verification**: It helps verify that the correct hostname and port are being used to connect to HBase.
-   **Network Problems Identification**: By attempting a connection and observing the outcome, users can identify if network issues are preventing access to HBase.

### 2.4. Implementation Details

The utility follows a simple yet effective process:

1. **Connection Establishment**: It attempts to establish a connection to the HBase host specified in the configuration.
2. **Table Retrieval**: Upon successful connection, it retrieves a list of all tables present in the HBase instance.
3. **Feedback**: It prints a success message along with the list of tables or an error message if the connection fails.
4. **Connection Closure**: It ensures that the connection is properly closed, regardless of the outcome.

### 2.5. Usage Example

```bash
python hbase_test_connection.py
```

**Expected Output (Successful Connection):**

```
Connection successful!
List of tables: ['f1_data', 'f1_reports', ...]
```

**Expected Output (Connection Failure):**

```
Error connecting to HBase: [Errno 111] Connection refused
```

## 3. Operations Testing Utility

### 3.1. Purpose

The operations testing utility (`hbase_test_operations.py`) is designed to validate the fundamental CRUD (Create, Read, Update, Delete) operations on HBase tables. It ensures that data can be correctly written to, read from, updated in, and deleted from HBase.

### 3.2. Features

-   **Table Creation Testing**: Verifies the ability to create new tables in HBase with specified column families.
-   **Data Insertion Verification**: Tests the insertion of records into HBase tables, ensuring data is written correctly.
-   **Read Operation Validation**: Confirms that data can be retrieved from HBase tables using various read operations.
-   **Column Family Management**: Demonstrates the creation and use of multiple column families within a table.
-   **Automated Cleanup**: Deletes the test table after the tests are completed, maintaining a clean HBase environment.

### 3.3. Testing Workflow

The utility follows a structured workflow to comprehensively test HBase operations:

1. **Connection Phase**:
    -   Establishes a connection to the HBase cluster.
    -   Verifies the connection status.
    -   Prepares the testing environment.

2. **Table Management**:
    -   Creates a test table (`test_table`) if it doesn't exist.
    -   Configures two column families: `driver` and `car`.
    -   Implements error handling for table creation issues.

3. **Data Operations**:
    -   **Insertion**: Inserts test records into the `test_table` with data distributed across the `driver` and `car` column families.
    -   **Verification**: Immediately reads back the inserted data to verify its integrity.
    -   **Reading**: Performs various read operations, including fetching specific columns and entire rows.
    -   **Validation**: Compares the retrieved data with the originally inserted data to ensure consistency.

4. **Cleanup**:
    -   Deletes the `test_table` after the tests are completed.
    -   Closes the HBase connection.

### 3.4. Implementation Details

The utility employs a systematic approach to testing:

-   **Dedicated Test Table**: Uses a dedicated table (`test_table`) for testing, preventing interference with production data.
-   **Multiple Column Families**: Implements two column families (`driver` and `car`) to demonstrate realistic data organization.
-   **Meaningful Test Data**: Uses sample Formula 1 data (driver names, car numbers) for testing, providing context and relevance.
-   **Detailed Logging**: Logs each operation's success or failure, providing a clear audit trail of the test execution.

### 3.5. Usage Example

```bash
python hbase_test_operations.py
```

**Expected Output (Successful Test):**

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

## 4. Data Reading Utility

### 4.1. Purpose

The F1 data reading utility (`hbase_read.py`) provides a comprehensive tool for accessing and retrieving Formula 1 race data stored in HBase. It offers a range of features for selective data retrieval, formatted output, and structured data presentation.

### 4.2. Features

#### 4.2.1. Data Access

-   **Meeting Information Retrieval**: Fetches details about race meetings, such as location, date, and official name.
-   **Session Data Access**: Retrieves information about specific race sessions (e.g., Practice, Qualifying, Race).
-   **Driver Information Extraction**: Accesses driver-specific data, including driver code, name, and team.
-   **Telemetry Data Reading**: Retrieves detailed telemetry data, including speed, RPM, gear, and other car-related metrics.

#### 4.2.2. Output Formatting

-   **Colored Console Output**: Uses color coding to enhance readability and highlight important information.
-   **Structured Data Presentation**: Organizes data into clear sections with appropriate headers and labels.
-   **Clear Section Organization**: Divides the output into logical sections for meetings, sessions, drivers, and telemetry data.
-   **Human-Readable Formatting**: Presents data in a user-friendly format, converting timestamps and other raw data into easily understandable representations.

#### 4.2.3. Data Selection

-   **Random Record Sampling**: Allows retrieval of a random sample of records for quick inspection and analysis.
-   **Driver-Specific Queries**: Enables fetching data for specific drivers based on their driver code or number.
-   **Session-Based Filtering**: Supports filtering data by session key, allowing analysis of specific race sessions.
-   **Column Family Selection**: Provides the ability to select specific column families for retrieval, optimizing data access.

### 4.3. Components

#### 4.3.1. Data Reader Class

The `F1DataReader` class encapsulates the logic for accessing and retrieving F1 data from HBase:

1. **Initialization**:
    -   Establishes a connection to the HBase cluster.
    -   Selects the target table (`f1_data`).
    -   Handles configuration parameters.

2. **Data Retrieval Methods**:
    -   `get_meeting_info()`: Retrieves information about a specific race meeting.
    -   `get_session_info()`: Fetches details about a particular race session.
    -   `get_driver_data()`: Retrieves data for a specific driver.
    -   `get_telemetry_data()`: Accesses telemetry data for a given driver and session.

3. **Formatting Utilities**:
    -   `convert_binary_data()`: Converts binary data retrieved from HBase into appropriate data types.
    -   `pretty_print_meeting()`, `pretty_print_session()`, `pretty_print_driver()`, `pretty_print_telemetry()`: Format and print data in a human-readable and color-coded manner.

### 4.4. Implementation Details

#### 4.4.1. Data Access Patterns

1. **Meeting Access**:
    -   Performs sequential scans with filtering based on meeting keys.
    -   Extracts relevant metadata about each meeting.

2. **Session Management**:
    -   Uses prefix-based scanning to efficiently retrieve session data.
    -   Maps session keys to human-readable session names.
    -   Links related data across different tables based on session keys.

3. **Driver Data Access**:
    -   Accesses multiple column families to retrieve comprehensive driver information.
    -   Implements random sampling for quick inspection of driver data.
    -   Supports filtering based on driver code or number for targeted analysis.

### 4.5. Usage Example

```bash
python hbase_read.py
```

**Expected Output (Partial):**

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

## 5. Operational Guidelines

### 5.1. Setup Requirements

#### 5.1.1. System Prerequisites

-   **Python 3.8+**: The scripts are written in Python and require a compatible version.
-   **HBase Thrift Server**: The HBase Thrift server must be running and accessible.
-   **SSH Tunnel (if remote)**: If connecting to a remote HBase instance, an SSH tunnel may be required for secure access.
-   **Required Python Packages**:
    -   `happybase`: For interacting with HBase.
    -   `colorama`: For colored console output.

#### 5.1.2. Configuration Settings

-   **Host Configuration**: The HBase host address needs to be correctly configured in the scripts.
-   **Port Settings**: The Thrift server port (default: 9090) should be correctly specified.
-   **Logging Parameters**: Logging levels can be adjusted for different verbosity levels.
-   **Table Names**: The scripts assume the default table names (`f1_data`, `f1_reports`). These can be modified if necessary.

### 5.2. Usage Procedures

#### 5.2.1. Initial Testing

1. **Connection Verification**:
    ```bash
    python hbase_test_connection.py
    ```
    -   Verify that the connection is successful.
    -   Check the list of tables to ensure HBase is accessible.
    -   Confirm that there are no error messages.

2. **Operations Testing**:
    ```bash
    python hbase_test_operations.py
    ```
    -   Monitor the creation of the `test_table`.
    -   Verify that data is inserted and read back correctly.
    -   Confirm that the `test_table` is deleted after the test.

3. **Data Reading**:
    ```bash
    python hbase_read.py
    ```
    -   Check the formatting of the output.
    -   Verify that the color coding is applied correctly.
    -   Review the sample data to ensure it's being retrieved and displayed as expected.

### 5.3. Troubleshooting Guide

#### 5.3.1. Common Issues

1. **Connection Problems**:
    -   **Symptom**: `Connection refused` or `Timeout` errors.
    -   **Solution**:
        -   Verify that the HBase Thrift server is running.
        -   Check the hostname and port configuration in the scripts.
        -   Ensure that the SSH tunnel is correctly established if connecting remotely.
        -   Check for any firewall rules that might be blocking the connection.

2. **Data Access Issues**:
    -   **Symptom**: `Table does not exist` or `Column family does not exist` errors.
    -   **Solution**:
        -   Verify that the table and column families exist in HBase.
        -   Check the table and column family names in the scripts for typos.
        -   Confirm that the user has the necessary permissions to access the table.

3. **Output Problems**:
    -   **Symptom**: Incorrect formatting, missing colors, or truncated output.
    -   **Solution**:
        -   Check if the terminal supports ANSI color codes.
        -   Verify that `colorama` is correctly initialized.
        -   Monitor the output size and implement buffering or pagination if necessary.