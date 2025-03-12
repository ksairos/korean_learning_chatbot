### **Template for Developing Telegram Bots Using aiogram v3.0+**
#### **SQLAlchemy + Alembic**

This template is designed for developing Telegram bots using the **aiogram v3.0+** library.  
It includes examples of a **User table** implemented with **SQLAlchemy 2.0** and scripts for **Alembic** (initialization, creating, and applying migrations).

If you have never worked with these tools before, please refer to their documentation to learn more.  
Additionally, I have an **English-language course** on these tools available on **Udemy**.

---

### **How to Get Started**

1. **Copy `.env.dist` to `.env` and fill in the required details.**  
2. **Create new handlers.**  

#### **Using Docker:**
- You can launch the project directly with Docker. If you don’t have Docker installed, download and install it first.
- Start the project with the command:
  ```sh
  docker-compose up
  ```

#### **Without Docker:**
- **Create a virtual environment (`venv`).**
- **Install dependencies** from `requirements.txt`:
  ```sh
  pip install -r requirements.txt --pre
  ```
- **Run the project**:
  ```sh
  python3 bot.py
  ```

---

### **Creating and Registering Handlers**

1. **Create a new module** `your_name.py` inside the `handlers` folder.
2. **Define a router** in `your_name.py`:
   ```python
   from aiogram import Router
   user_router = Router()
   ```
3. **You can create multiple routers** in the same module and attach handlers to each.
4. **Register handlers using decorators**:
   ```python
   @user_router.message(commands=["start"])
   async def user_start(message):
       await message.reply("Welcome, regular user!")
   ```
5. **Add routers to `handlers/__init__.py`**:
   ```python
   from .admin import admin_router
   from .echo import echo_router
   from .user import user_router

   routers_list = [
       admin_router,
       user_router,
       echo_router,  # echo_router must be last
   ]
   ```
6. **Integrate handlers into `bot.py`**:
   ```python
   from tgbot.handlers import routers_list

   async def main():
       dp.include_routers(*routers_list)
   ```

---

### **Setting Up the Database and Running the First Migration**

1. Open the `.env` file and **fill in database connection details** if not already done.
2. Edit **`docker-compose.yml`**:  
   - **Uncomment the sections:** `api`, `pg_database`, and `volumes` to activate database support.
3. Modify **`config.py`**:  
   - Complete the **TODO** in the `construct_sqlalchemy_url` function.
   - Locate the `load_config` function and **uncomment the line** responsible for initializing the database configuration:
     ```python
     db = DbConfig.from_env(env)
     ```
4. **Restart Docker** with the new configurations:
   ```sh
   docker-compose up --build
   ```
5. **Run the database migration**:
   ```sh
   docker-compose exec api alembic upgrade head
   ```

---

### **aiogram v3 Tutorials**
Currently, there are no video tutorials available, but **@Groosha** has started working on a guide. Stay tuned! 🚀