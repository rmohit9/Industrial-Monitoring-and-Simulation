# Industrial Monitoring and Fault Detection

## Overview

This project simulates an industrial monitoring system that stores equipment information and sensor telemetry, simulates fault scenarios, detects abnormal readings using rule-based thresholds, and evaluates detection results.

The project uses synthetic data for development and testing. Its evaluation results should not be interpreted as validated real-world industrial performance.

## Features

- Models industrial facilities, equipment, pumps, tanks, valves, pipes, and sensors.
- Generates synthetic sensor telemetry.
- Simulates leak, blockage, pump degradation, and sensor fault scenarios.
- Generates normal control readings for comparison.
- Detects anomalies using percentage deviation thresholds.
- Generates alarms from detection results.
- Evaluates detection performance and exports reports.
- Validates database quality and integrity.
- Includes automated tests for reproducibility and synthetic detection behavior.

## Technology Stack

- Python
- SQLAlchemy
- SQLite
- NumPy
- Pytest

See `requirements.txt` for the project's Python dependencies.

## Project Structure

```text
Industrial_Monitoring/
├── data/
├── notebooks/
├── reports/
│   ├── detection_evaluation.csv
│   ├── evaluation_summary.json
│   ├── ground_truth.csv
│   └── project_summary.json
├── sql/
├── src/
│   ├── detection/
│   ├── evaluation/
│   ├── generators/
│   ├── simulator/
│   ├── validation/
│   ├── database.py
│   └── models.py
├── tests/
│   ├── test_production_thresholds.py
│   ├── test_realistic_detection.py
│   └── test_reproducibility.py
├── generate_data.py
├── generate_scenarios.py
├── run_detection.py
├── run_fault_simulation.py
├── requirements.txt
└── README.md
```

## Setup

Activate the virtual environment on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```cmd
python -m pip install -r requirements.txt
```

## Running the Project

Run these commands from the project root in the order appropriate for your database state.

Generate the initial dataset:

```cmd
python generate_data.py
```

Generate fault scenarios:

```cmd
python generate_scenarios.py
```

Run the fault simulation:

```cmd
python run_fault_simulation.py
```

Run anomaly detection:

```cmd
python run_detection.py
```

Evaluate detection performance:

```cmd
python -m src.evaluation.evaluate_detection
```

Validate data quality:

```cmd
python -m src.validation.data_quality
```

Run the automated tests:

```cmd
python -m pytest tests -v
```

**Important:** The data-generation and simulation commands may behave differently when records already exist. Back up the database before regenerating data or rerunning scripts that modify stored records.

### Launch the Dashboard

The project includes a Streamlit dashboard for viewing equipment metrics, exploring recent sensor telemetry, and reviewing the latest alarms.

Start the dashboard from the project root:

```cmd
python -m streamlit run dashboard\app.py
```

Streamlit will display a local URL in the terminal, usually:

```text
http://localhost:8501
```

**Note:** Ensure the virtual environment is activated, the required dependencies are installed, and the existing database file `data/industrial_monitoring.db` is available before launching the dashboard. The dashboard reads the existing database and does not generate or modify the database tables.

## Current Synthetic Dataset

The validated database currently contains:

- 3 facilities
- 20 pumps
- 30 tanks
- 60 valves
- 60 pipes
- 100 sensors
- 100,000 original telemetry readings

The current evaluation includes 916 simulated fault readings and 10,000 normal-control readings.

## Detection Method

The rule engine calculates the absolute percentage deviation between the recorded baseline and the simulated observation. It compares this deviation against the configured sensor threshold.

The current configured threshold is 8% for flow, pressure, and level sensors.

## Testing and Limitations

The current automated test suite contains four passing tests covering random-seed behavior and synthetic anomaly-detection scenarios.

The reported evaluation metrics are based on synthetic data. Normal controls use unchanged baseline readings, and simulated faults use predefined changes. Consequently, perfect scores on this dataset do not establish real-world accuracy or reliability.

Further validation with representative industrial telemetry, realistic sensor noise, drift, and independently verified fault labels is needed before operational use.