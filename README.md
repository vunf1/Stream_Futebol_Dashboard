
# ⚽ Goal Score Manager

**Goal Score Manager** is a desktop application built with Python and CustomTkinter, designed to simplify live score management for football matches — perfect for OBS streaming, local tournaments, or manual scoreboard control.

---
## ✨ What’s New

- **Dynamic Window Layout**: Buttons and score panels resize fluidly with the window.
- **Real-Time Swap**: Instantly swap home/away scores with a single click.
- **Lock/Unlock Decrement**: Disable the “–1” buttons to prevent accidental score reductions.
- **Custom Button Styling**: +1 in green, –1 in red; uniform bottom-control buttons with gaps.
- **Improved UI Padding**: Frames pack tightly with no unwanted margins.

---

## ✨ Features

- ✅ Create multiple fields (independent windows)
- 🏷️ Assign full team names and abbreviations  
- 📦 Save and sync teams with **MongoDB Atlas (Free Tier)**
- 🎯 Score control (increment and decrement)
- 🔒 Decrement lock and reset button with confirmation
- 🧠 Smart team name suggestions from database
- 🔐 Admin screen with PIN protection to **edit or delete** saved teams
- 🌙 Dark mode with smooth bottom-right toast notifications 
- 🎥 OBS integration via `.txt` file export

---

## 🧩 Technologies Used

- [Python 3.10+](https://www.python.org)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [MongoDB Atlas (Free Tier)](https://www.mongodb.com/cloud/atlas)
- [Pymongo](https://pypi.org/project/pymongo/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## 📁 Project Structure

```
.
├── goal_score.py        # Entry point and UI orchestration
├── config_editor.py     # Configuration editor launcher
├── src/
│   ├── config/          # Configuration system
│   │   ├── settings.py  # Application settings
│   │   └── config_editor.py  # Configuration UI
│   ├── core/            # Core functionality
│   ├── ui/              # User interface components
│   ├── licensing/       # License management
│   ├── notification/    # Notification system
│   ├── performance/     # Performance monitoring
│   ├── security/        # Security utilities
│   └── utils/           # Utility functions
├── build.py             # PyInstaller builder script
├── assets/icons/        # Application icons (ICO, PNG)
├── version.txt          # Project version
└── .env                 # Environment variables (MONGO_URI, PIN)
```
## 🔧 Requirements

```bash
python build.py
```
Create a .env file with the following variables:

```
MONGO_URI=mongodb+srv://<usuario>:<senha>@<cluster>.mongodb.net/
MONGO_DB=
MONGO_COLLECTION=
PIN=
```

### 🎨 Customization

The application supports comprehensive configuration through a centralized settings system. You can customize various aspects of the application:

#### **Configuration Editor**
Launch the configuration editor to easily modify settings:
```bash
python config_editor.py
```

#### **Key Configuration Areas**
- **Window Settings**: Opacity, dimensions, and positioning
- **Performance Settings**: UI updates, caching, and buffer management
- **Animation Settings**: Loading animations and timing
- **Field Settings**: Maximum fields, cascade offsets, and grid spacing
- **UI Settings**: Fonts, colors, and themes

#### **Configuration File**
Settings are stored in `performance_config.json` (created automatically):
- **Default**: 0.95 (95% opacity, slight transparency)
- **Range**: 0.0 (completely transparent) to 1.0 (fully opaque)
- **Location**: `performance_config.json` file (created automatically)

#### **Environment Variables**
Some settings can be configured via environment variables in `.env`:
- `MONGO_URI` - MongoDB connection string
- `MONGO_DB` - Database name
- `MONGO_COLLECTION` - Collection name
- `PIN` - Admin PIN for team management
- `DEBUG_MODE` - Enable debug mode (true/false)

---

## ▶️ How to Run

There are several ways to run the application:

### Option 1: Using the PowerShell launcher script (Recommended for Windows)
```powershell
.\run.ps1
```

### Option 2: Using the batch file (Windows)
```cmd
run.bat
```

### Option 3: Using the Python launcher script
```bash
python run.py
```

### Option 4: Using Python module syntax
```bash
python -m src.goal_score
```

### Option 5: Direct execution (from root directory)
```bash
python src/goal_score.py
```

When launched, the app will prompt how many fields you want to open. Each will function independently.

---

## 📦 Build Executable

```bash
python build.py
```

> A .exe file will be created in the dist/ folder.

---

## 🗃️ About the Database

Originally, the project used `teams.json` files. Now all teams are stored in MongoDB Atlas, with optional automatic local backup.

---

## 📸 Interface
> Compact, fast-access interface tailored for live sports events and OBS integration.

---

## 📦 License Summary

This project is offered under a **dual license model**:

### 1. **Business Source License (BSL) 1.1** *(default)*
- You can **view, modify, and use** the code.
- You **may not use** it to offer **a paid or commercial service** without a commercial license.
- After a set date (see below), this project will automatically relicense to **Apache 2.0**.

### 2. **Commercial License** *(optional)*
- Companies may obtain a commercial license that **permits SaaS, distribution, or integration** without triggering the BSL restrictions.
- This license requires **royalties** or a **usage fee**, negotiated individually.

---

## 🔐 Key Licensing Terms

| Term | Description |
|------|-------------|
| **License Type** | Business Source License v1.1 |
| **Usage Limitation** | You **may not** use this software to provide a paid or hosted service without a commercial license. |
| **Change License** | Apache License 2.0 |

---

## 💼 Commercial License
To use this project in a way **not permitted by the BSL**, such as:
- Integrating into a **paid product**
- Hosting the software as a **SaaS or cloud service**
- Avoiding code disclosure obligations

You must obtain a **commercial license**.

📩 Contact: **epg.joaomaia@gmail.com** 

---

## 📁 Files

- `LICENSE` — BSL 1.1 terms
- `COMMERCIAL.md` — Commercial licensing details

---

## 🔓 Example Open Usage
You can freely use this project for:
- Personal experiments
- Non-commercial internal tools
- Open-source contributions

---

## 🔒 Prohibited without Commercial License
- Hosting this as a paid API/service
- Bundling in commercial/closed-source apps

---

## 🧾 Royalties
Royalties for commercial use are negotiated based on:
- Scope of use (e.g., users, deployments, integrations)
- Revenue or licensing volume

---

## ❤️ Contributing
You’re welcome to contribute under the terms of the BSL. Contributions remain under the same license unless otherwise agreed.

---

## 📚 References

- [CustomTkinter Documentation](https://github.com/TomSchimansky/CustomTkinter)  
- [MongoDB Atlas Free Tier](https://www.mongodb.com/cloud/atlas)  
- [Business Source License FAQ](https://mariadb.com/bsl-faq-adopting/)  
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)