# 🐞 QA Assist

**QA Assist** is a production-ready, AI-powered quality engineering companion built with Python and Streamlit. It leverages Google's cutting-edge **Gemini 2.5 Flash** model to drastically reduce the time QA engineers spend writing test cases and automation scripts.

---

## ✨ Features

- **📸 Generate from Screenshot**: Upload a UI screenshot, wireframe, or mockup. The vision AI analyzes the layout, buttons, and fields to instantly generate comprehensive test cases.
- **📝 Generate from Requirements**: Paste user stories, Jira tickets, or acceptance criteria to receive structured test suites covering positive, negative, and edge cases.
- **🤖 Automation Script Generator**: Link a Git repository (or local folder) so the AI can learn your project's framework structure (POM, selectors, assertions). It then generates ready-to-run automation scripts for:
  - Selenium (Python)
  - Playwright (Python & JS/TS)
  - WebdriverIO (JS)
  - Cucumber (JS/WDIO & Java/Selenium)
- **📊 Advanced Exporting**: Download generated test cases as heavily formatted, production-ready Excel (`.xlsx`) files or UTF-8 compatible CSV files.
- **👥 User Management**: Built-in, secure local authentication system with an admin dashboard for user lifecycle management.
- **💅 Premium UI**: A highly responsive, glassmorphic dark-mode interface built for speed (using advanced in-memory data caching).

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your machine:
1. **[Python 3.10+](https://www.python.org/downloads/)**
2. **[Git](https://git-scm.com/downloads)** (Required for the Automation Script repo-cloning feature)
3. A **Google Gemini API Key**. You can get one for free from Google AI Studio.

---

## 🚀 Installation & Setup

**1. Clone the repository (or download the folder)**
```bash
git clone https://github.com/your-username/qa-assist.git
cd qa-assist
```

**2. Create a virtual environment (Recommended)**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Mac/Linux
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your Environment Variables**
Create a new file named `.env` in the root directory of the project, and add your Gemini API key:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

---

## 💻 Running the App

Start the Streamlit server with the following command:
```bash
python -m streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`.

### Default Login
On your first run, an admin account is automatically generated:
- **Username:** `admin`
- **Password:** `admin123`

*(You can change this password or add new users from the "Users" tab once logged in).*

---

## 🏗️ Project Structure

```text
qa-assist/
├── app.py                  # Main application, routing, auth, and Test Case generation UI
├── automation_page.py      # Logic & UI for the Automation Script Generator
├── styles.py               # Custom CSS injection for the premium dark-theme UI
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (API Key) - YOU MUST CREATE THIS
└── users.json              # Auto-generated local database for user authentication
```

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! 
If you find a bug or want to suggest a feature, please feel free to open an issue or submit a pull request.

![image1](/img/image.png)

![image2](/img/image-1.png)

![image3](/img/image-2.png)

![image4](/img/image-3.png)

![image5](/img/image-4.png)