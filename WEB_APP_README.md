# 🏥 Patient Data Collection Web Application

## 🎯 Overview

A comprehensive web-based system for comparing patient CSV files and collecting missing data through an interactive interface. This system integrates with your existing AI Pharmacovigilance System.

## ✨ Features

### 📊 Data Management
- **CSV Comparison**: Automatically compares main SYOMS file with missing data file
- **Patient Matching**: Uses Case ID and PHN (Contact No) for accurate matching
- **Question Generation**: Creates specific questions for each missing data field
- **Database Storage**: Stores all data in SQLite database

### 🖥️ Web Interface
- **Dashboard**: Real-time overview of all patients and progress
- **Patient Sessions**: Interactive question-answer interface
- **Progress Tracking**: Visual progress bars and completion percentages
- **Responsive Design**: Works on desktop and mobile devices

### 🔧 Backend Features
- **FastAPI**: RESTful API with automatic documentation
- **SQLAlchemy**: Database ORM for data management
- **Real-time Updates**: Live progress tracking
- **Data Validation**: Answer validation against expected values

## 🚀 Quick Start

### Method 1: Using the Start Script (Recommended)
```bash
cd /home/shaluchan/ai-docker/pharma-covigilance
./start_web_app.sh
```

### Method 2: Manual Setup

#### Backend Setup
```bash
cd AI-Pharmacovigilance-System/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run CSV comparison
python patient_data_comparator.py

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd AI-Pharmacovigilance-System/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🌐 Access Points

Once started, access the application at:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 Using the Web Application

### 1. System Overview
- View total patients, completed cases, and overall progress
- Click "Run CSV Comparison" to refresh data from CSV files

### 2. Patient List
- See all patients with their completion status
- Visual progress bars for each patient
- Click "Start Session" to begin data collection

### 3. Question Session
- Answer questions one by one
- Immediate feedback on answers
- Automatic progression through questions
- Real-time progress updates

## 🗂️ File Structure

```
AI-Pharmacovigilance-System/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── patient_data_comparator.py   # CSV comparison logic
│   ├── database.py                 # Database configuration
│   ├── models/
│   │   └── patient_comparison_model.py  # Database models
│   ├── routes/
│   │   └── patient_routes.py       # API endpoints
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Main application
│   │   ├── PatientDashboard.jsx   # Patient interface
│   │   └── styles.css           # Styling
│   └── package.json             # Node.js dependencies
└── pv.db                       # SQLite database
```

## 🔌 API Endpoints

### Patient Management
- `POST /api/patients/run-comparison` - Run CSV comparison
- `GET /api/patients/` - Get all patients
- `GET /api/patients/{contact_no}/questions` - Get patient questions
- `POST /api/patients/submit-response` - Submit patient answer
- `GET /api/patients/summary` - Get system summary

### Documentation
Visit http://localhost:8000/docs for interactive API documentation.

## 📊 Database Schema

### Patient Comparisons
- Stores comparison results between CSV files
- Tracks completion status and progress

### Patient Responses
- Individual question-answer pairs
- Validation results and timestamps

## 🎨 UI Features

### Dashboard
- Real-time statistics cards
- Patient grid with progress indicators
- Responsive design for all screen sizes

### Question Interface
- Clean, accessible question display
- Large text areas for answers
- Immediate feedback on responses
- Progress tracking

### Visual Design
- Modern, clean interface
- Consistent color scheme
- Smooth animations and transitions
- Mobile-responsive layout

## 🔍 Data Flow

1. **CSV Processing**: Compare files to identify missing data
2. **Question Generation**: Create specific questions for gaps
3. **Web Interface**: Display questions to users
4. **Answer Collection**: Validate and store responses
5. **Progress Tracking**: Update completion status
6. **Data Storage**: Persist in SQLite database

## 🛠️ Configuration

### File Paths
Update these paths in `patient_data_comparator.py`:
```python
main_csv_path = "/path/to/syoms1.csv"
missing_csv_path = "/path/to/missed_converted.csv"
db_path = "/path/to/pv.db"
```

### Database
The system uses SQLite by default. The database file is created automatically.

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill processes on ports 8000 and 5173
   sudo lsof -ti:8000 | xargs kill -9
   sudo lsof -ti:5173 | xargs kill -9
   ```

2. **Virtual Environment Issues**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Frontend Dependencies**
   ```bash
   # Clear and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

### Logs
- Backend logs appear in terminal
- Frontend logs appear in browser console
- Database operations logged to console

## 📈 System Statistics

Based on your data:
- **113 patients** with missing data
- **1,066 missing fields** identified
- **780 questions** generated
- **Real-time progress** tracking

## 🔒 Security

- All data stored locally
- No external data transmission
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy

## 🚀 Future Enhancements

- User authentication system
- Advanced reporting and analytics
- Export functionality
- SMS/email notifications
- Multi-language support
- Advanced search and filtering

## 📞 Support

For issues or questions:
1. Check the console logs
2. Verify file paths
3. Ensure all dependencies are installed
4. Check API documentation at /docs

---

**🎉 Your Patient Data Collection System is ready to use!**
