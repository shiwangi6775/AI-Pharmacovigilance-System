# Patient Data Comparison and Collection System

## Overview

This system compares your main SYOMS CSV file with a missing data file, identifies missing information for each patient, generates specific questions to collect the missing data, and stores everything in a database for easy management.

## Features

- **Automatic Data Comparison**: Compares main CSV with missing data CSV
- **Patient Matching**: Matches patients using Case ID and PHN (Contact No)
- **Question Generation**: Creates specific questions for each missing data field
- **Database Storage**: Stores all comparison results and patient responses
- **Interactive Interface**: User-friendly interface for data collection
- **Progress Tracking**: Tracks completion status for each patient

## Files Structure

```
/home/shaluchan/ai-docker/pharma-covigilance/
├── syoms1.csv                    # Main complete patient data
├── missed_converted.csv           # Patient data with missing fields
├── patient_data_comparator.py     # Main comparison and analysis script
├── patient_interface.py           # Interactive patient interface
├── requirements.txt               # Python dependencies
├── venv/                          # Virtual environment
└── AI-Pharmacovigilance-System/
    └── pv.db                      # SQLite database
```

## Setup

1. **Install Dependencies**:
   ```bash
   cd /home/shaluchan/ai-docker/pharma-covigilance
   python3 -m venv venv
   source venv/bin/activate
   pip install pandas
   ```

2. **Run Initial Comparison**:
   ```bash
   source venv/bin/activate
   python patient_data_comparator.py
   ```

## Usage

### 1. Data Comparison Script (`patient_data_comparator.py`)

This script:
- Loads both CSV files
- Compares them to identify missing data
- Generates specific questions for each missing field
- Stores results in the database

**Run it**:
```bash
python patient_data_comparator.py
```

### 2. Interactive Patient Interface (`patient_interface.py`)

This script provides:
- View all patients and their progress
- Start data collection sessions for specific patients
- Track completion status
- Submit and validate patient responses

**Run it**:
```bash
python patient_interface.py
```

**Interface Options**:
1. **View all patients** - Shows progress for all patients
2. **Start session for specific patient** - Begin data collection
3. **View patient summary** - Check individual patient status
4. **Exit** - Close the application

## Database Schema

### `patient_comparisons` Table
- `case_id`: Unique case identifier
- `patient_initials`: Patient initials
- `contact_no`: PHN (Patient Health Number)
- `missing_fields`: JSON data of missing fields
- `questions`: JSON array of generated questions
- `complete_data`: Complete patient data from main file
- `incomplete_data`: Patient data with missing fields
- `status`: Processing status
- `created_at`: Timestamp

### `patient_responses` Table
- `case_id`: Related case identifier
- `field_name`: Name of the data field
- `question`: Generated question for the field
- `patient_answer`: Patient's response
- `expected_answer`: Correct answer from main file
- `is_correct`: Whether answer matches expected
- `responded_at`: Response timestamp

## Example Questions Generated

The system generates specific questions like:
- "What is the age of patient OH (PHN: 9811965645)?"
- "Was the adverse reaction serious for patient KF (PHN: 9718321079)? (Y/N)"
- "What was the first concomitant drug for patient ZO (PHN: 9718321078)?"
- "When did the therapy start for patient IM (PHN: 7835994166)?"

## System Results

Based on your data:
- **Total Patients**: 113
- **Total Missing Fields**: 1,066
- **Generated Questions**: 780
- **Patients with Missing Data**: All 113 patients

## Key Features

### Patient Matching Logic
- Matches patients by Case ID and Contact No (PHN)
- Handles duplicate patient names with different PHNs
- Ensures accurate data mapping

### Question Generation
- Creates context-specific questions for each field type
- Includes patient identification (initials + PHN)
- Provides expected answers for validation

### Data Validation
- Compares patient responses with expected answers
- Tracks correct/incorrect responses
- Provides immediate feedback

### Progress Tracking
- Real-time completion percentage
- Pending questions count
- Individual patient summaries

## Security and Privacy

- All data stored locally in SQLite database
- Patient identification uses initials and PHN only
- No external data transmission
- Secure data handling practices

## Future Enhancements

- Web-based interface for easier access
- Automated SMS/email reminders for patients
- Data export functionality
- Advanced reporting and analytics
- Integration with existing pharmacovigilance system

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure virtual environment is activated
   ```bash
   source venv/bin/activate
   ```

2. **Database locked**: Close other database connections
3. **CSV not found**: Check file paths in the script

### Logs and Debugging

The system provides detailed console output including:
- Number of records loaded
- Missing field counts
- Question generation status
- Database operation results

## Support

For issues or questions about the system, refer to the console output or check the database tables for detailed information about the comparison results and patient responses.
