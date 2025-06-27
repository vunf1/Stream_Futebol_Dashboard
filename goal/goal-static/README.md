
# ⚽ Goal Score Manager

**Goal Score Manager** is a desktop application built with Python and CustomTkinter, designed to simplify live score management for football matches — perfect for OBS streaming, local tournaments, or manual scoreboard control.

---

## ✨ Features

- ✅ Create multiple fields (independent windows)
- 🏷️ Assign team names and abbreviations
- 📦 Save and sync teams with **MongoDB Atlas (Free Tier)**
- 🎯 Score control (increment and decrement)
- 🔒 Decrement lock and reset button with confirmation
- 🧠 Smart team name suggestions from database
- 🔐 Admin screen with PIN protection to **edit or delete** saved teams
- 🌙 Modern dark mode interface with smooth **bottom-right toast notifications**
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

| File/Folder         | Description |
|---------------------|-------------|
| `goal_score.py`     | Main file containing UI and field logic |
| `mongodb.py`        | MongoDB operations (save, update, list, delete teams) |
| `helpers.py`        | Toast notifications, visual effects, and utilities |
| `team_names.py`     | Legacy JSON functions (still used as fallback) |
| `assets/icons`      | App icons, e.g., `icon_soft.ico` |
| `build.py`          | PyInstaller script to create an executable |
| `.env`              | Environment variables like MongoDB URI |
| `version.txt`       | Current project version number |

---

## 🔧 Requirements

```bash
pip install -r requirements.txt

```
Create a .env file with the following variables:

```
MONGO_URI=mongodb+srv://<usuario>:<senha>@<cluster>.mongodb.net/
MONGO_DB=nome_do_banco
MONGO_COLLECTION=nome_da_colecao
PIN=1234
```

---

## ▶️ How to Run

```bash
python goal_score.py
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
| **Change Date** | January 1, 2028 |
| **Change License** | Apache License 2.0 |

---

## 💼 Commercial License
To use this project in a way **not permitted by the BSL**, such as:
- Integrating into a **paid product**
- Hosting the software as a **SaaS or cloud service**
- Avoiding code disclosure obligations

You must obtain a **commercial license**.

📩 Contact: **vunf1@example.com** 

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
- [Business Source License (BSL) FAQ](https://mariadb.com/bsl-faq-adopting/)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)
