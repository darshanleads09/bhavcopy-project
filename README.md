Here is a well-structured **README.md** file for your **bhavcopy-project** repository on GitHub. This document provides an overview, installation steps, usage instructions, and troubleshooting tips.

---

## **BhavCopy Project 📊**
### **Stock Market Data Processing with Django**
This project is a **Django-based web application** that fetches, processes, and displays BhavCopy data from multiple stock exchanges (**NSE, BSE, MCX**). It provides **data visualization, filtering, pagination, and automatic downloading** of historical stock data.

---

## **🚀 Features**
- Fetch BhavCopy data from **NSE, BSE, and MCX**.
- **Dynamic Filtering**: Filter by date, segment, status, and source.
- **Pagination Support**: Large datasets are displayed efficiently.
- **MCX Integration**: Added support for MCX BhavCopy processing.
- **Automatic Downloads**: Reload functionality to update data.
- **Database Storage**: MySQL backend for data persistence.
- **Django Admin Panel**: Manage records via Django Admin.
- **ngrok Integration**: Expose local Django server to the internet.

---

## **📂 Folder Structure**
```
bhavcopy-project/
│── bhavcopy_project/        # Django project settings & URLs
│── bhavcopy_app/            # Main Django app with views & models
│   ├── templates/           # HTML templates (index.html, mcx.html)
│   ├── static/              # CSS, JS, images
│   ├── views.py             # Business logic for data processing
│   ├── models.py            # Database models (NSE, BSE, MCX)
│   ├── urls.py              # URL routing
│   ├── reload_script.py     # Data fetch & insert logic
│   ├── mcxdownloader.py     # MCX-specific data processing
│── db.sqlite3               # Default SQLite database (optional)
│── manage.py                # Django CLI tool
│── README.md                # Project documentation
│── requirements.txt         # Dependencies list
```

---

## **🛠 Installation & Setup**
### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/darshanleads09/bhavcopy-project.git
cd bhavcopy-project
```

### **2️⃣ Create & Activate a Virtual Environment**
```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```

### **3️⃣ Install Dependencies**
```sh
pip install -r requirements.txt
```

### **4️⃣ Configure MySQL Database**
Update your **`settings.py`**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'bhavcopynew',
        'USER': 'root',
        'PASSWORD': 'Newday@123',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### **5️⃣ Apply Migrations**
```sh
python manage.py makemigrations
python manage.py migrate
```

### **6️⃣ Start Django Server**
```sh
python manage.py runserver
```
Access the app at: **`http://127.0.0.1:8000/`**

---

## **🌍 Expose Django Server with ngrok**
If you want to make your Django app accessible over the internet, use **ngrok**.

### **1️⃣ Install ngrok**
Download and install **[ngrok](https://ngrok.com/download)**.

### **2️⃣ Start a Tunnel**
```sh
ngrok http 8000
```
This will generate a public URL like:
```
https://your-ngrok-url.ngrok-free.app -> http://127.0.0.1:8000
```
### **3️⃣ Update `ALLOWED_HOSTS` in `settings.py`**
```python
ALLOWED_HOSTS = [
    '127.0.0.1', 
    'localhost', 
    'your-ngrok-url.ngrok-free.app'
]
```
Restart Django and access the app using the ngrok URL.

---

## **📜 API Endpoints**
| **Endpoint**               | **Method** | **Description**                         |
|----------------------------|-----------|-----------------------------------------|
| `/`                        | GET       | Load the main dashboard                 |
| `/mcx/`                    | GET       | Load the MCX BhavCopy data               |
| `/data/?params`            | GET       | Fetch filtered NSE/BSE data              |
| `/data/mcx/?params`        | GET       | Fetch filtered MCX data                 |
| `/reload/<date>/`          | POST      | Reload data for a specific date         |

---

## **💡 Troubleshooting**
### **1️⃣ Database Connection Issues**
- Make sure **MySQL service** is running:
  ```sh
  systemctl start mysql  # Linux
  net start mysql        # Windows
  ```
- Verify **DB credentials** in `settings.py`.

### **2️⃣ Ngrok Not Recognized**
- Ensure **ngrok** is installed and accessible via:
  ```sh
  ngrok version
  ```
- If missing, add ngrok to **system PATH**.

### **3️⃣ `django.db.utils.OperationalError: Unknown column 'bhav_mcx.weekday'`**
- Run database migrations:
  ```sh
  python manage.py makemigrations
  python manage.py migrate
  ```

---

## **👨‍💻 Author**
**Darshan Leads**  
📧 **darshanleads09@gmail.com**  
🔗 **[GitHub](https://github.com/darshanleads09/)**  

---

## **📜 License**
This project is **open-source** and available under the **MIT License**.

---
