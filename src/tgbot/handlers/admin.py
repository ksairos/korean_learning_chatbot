import psutil
import os
from datetime import datetime
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.db.crud import add_user, get_all_users, delete_user_by_id
from src.schemas.schemas import TelegramUser
from src.tgbot.filters.admin import AdminFilter
from src.db.database import async_session

admin_router = Router()
admin_router.message.filter(AdminFilter())


def escape_markdown_v2(text: str) -> str:
    """Remove special characters that need escaping in MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, '')
    return text


@admin_router.message(CommandStart())
async def admin_start(message: Message):
    admin = TelegramUser(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        chat_id=message.chat.id
    )
    async with async_session() as session:
        await add_user(session=session, user=admin)

    await message.reply("Привет, админ! Добавил тебя в базу")


@admin_router.message(Command("users"))
async def list_users(message: Message):
    """List all users in the database with their details"""
    async with async_session() as session:
        users = await get_all_users(session)
        
        if not users:
            await message.reply("No users found in database.")
            return
        
        response = "**All Users:**\n\n"
        for user in users:
            full_name = f"{user.first_name}"
            if user.last_name:
                full_name += f" {user.last_name}"
            
            username_part = f" @{user.username}" if user.username else ""
            date_part = user.created_at.strftime("%Y-%m-%d %H:%M")
            
            response += f"👤 {full_name}{username_part}\n"
            response += f"ID: {user.id}\n"
            response += f"Added: {date_part}\n\n"
        
        await message.reply(escape_markdown_v2(response), parse_mode="MarkdownV2")


@admin_router.message(Command("deleteuser"))
async def delete_user(message: Message):
    """Delete a user by their ID"""
    try:
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await message.reply("Usage: /deleteuser <user_id>\nExample: /deleteuser 123456789")
            return
        
        user_id = int(command_parts[1])
        
        async with async_session() as session:
            success = await delete_user_by_id(session, user_id)
            
            if success == 1:
                response = f"✅ User {user_id} has been deleted successfully."
                await session.commit()
            else:
                response = f"❌ User {user_id} not found."

            await message.reply(escape_markdown_v2(response))
                
    except ValueError:
        await message.reply(escape_markdown_v2("❌ Invalid user ID. Please provide a valid number."))
    except Exception as e:
        await message.reply(escape_markdown_v2(f"❌ Error deleting user: {str(e)}"))


@admin_router.message(Command("status"))
async def bot_status(message: Message):
    """Show bot and system status"""
    try:
        current_process = psutil.Process(os.getpid())
        
        # Bot process information
        memory_info = current_process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        cpu_percent = current_process.cpu_percent()
        
        # System information
        system_memory = psutil.virtual_memory()
        system_cpu = psutil.cpu_percent(interval=1)
        
        # Uptime calculation
        process_start = datetime.fromtimestamp(current_process.create_time())
        uptime = datetime.now() - process_start
        
        status_text = f"""
🤖 **Bot Status:**

**Process Info:**
• PID: `{os.getpid()}`
• Memory Usage: `{memory_mb:.1f} MB`
• CPU Usage: `{cpu_percent:.1f}%`
• Uptime: `{str(uptime).split('.')[0]}`
• Started: `{process_start.strftime('%Y-%m-%d %H:%M:%S')}`

**System Info:**
• System Memory: `{system_memory.percent:.1f}% used`
• System CPU: `{system_cpu:.1f}%`
• Available Memory: `{system_memory.available / (1024**3):.1f} GB`

✅ Bot is running normally
        """
        
        await message.reply(escape_markdown_v2(status_text), parse_mode="MarkdownV2")
        
    except Exception as e:
        await message.reply(f"❌ Error getting bot status: {str(e)}")


@admin_router.message(Command("help"))
async def admin_help(message: Message):
    """Show available admin commands"""
    help_text = """
🔧 **Admin Commands:**

/users - List all users in the database
/deleteuser + user_id - Delete a user by their ID
/status - Show bot and system status
/help - Show this help message
    """
    await message.reply(escape_markdown_v2(help_text), parse_mode="MarkdownV2")