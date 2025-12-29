# 🏋️ Personal Fitness Tracking App

**Personal Fitness Tracking App** is a terminal-based fitness management application developed in **Python**
as part of a course assignment. The application allows users to log workouts, track nutrition,
monitor health metrics, and analyze progress toward personal fitness goals.

The system is designed as an **offline CLI application** and stores all data locally using **JSON files**.

---

## ✨ Features

### 👤 User Management
- User registration and login using email and PIN
- Personal fitness goal management

### 🎯 Goal Types
- Weight loss
- Muscle gain
- Endurance improvement
- Maintenance

### 🏋️ Workout Tracking
- Strength, cardio, and flexibility workouts
- Weekly workout summaries
- Automatic **Personal Record (PR)** detection

### 🍽️ Nutrition Tracking
- Daily calorie intake tracking
- Macronutrient tracking (protein, carbohydrates, fat)

### 📊 Health Metrics
- Weight tracking
- Sleep duration
- Water intake
- Mood tracking
- Body measurements

### 💾 Data Management
- Local JSON-based data storage
- Automatic backup and restore functionality

---
```
## 🗂️ Project Structure
fitness_tracking_app/
├── main.py  # CLI entry point and menu handling
├── storage.py  # JSON storage, backups, and restore logic
├── profiles.py  # User profiles, authentication, and goals
├── workouts.py  # Workout logging and summaries
├── nutrition.py  # Meal logging and calorie tracking
├── metrics.py  # Health metrics and progress analysis
├── README.md  # Project documentation
├── data/  # Runtime data files
│ ├── users.json  # User profile data
│ ├── workouts.json  # Workout records
│ ├── nutrition.json  # Nutrition logs
│ └── metrics.json  # Health metric data
├── backups/  # Automatic backup files
└── tests/  # Automated test files
├── test_workouts.py  # Workout-related tests
├── test_nutrition.py  # Nutrition-related tests
└── test_metrics.py  # Metrics and goal tests
```

---

## ▶️ How to Run

Make sure **Python 3.10+** is installed.

```bash
python main.py
```

The application runs entirely in the terminal.

## ℹ️ Notes

This project is developed for educational purposes.
No external APIs or databases are used.
The application runs completely offline.


---
