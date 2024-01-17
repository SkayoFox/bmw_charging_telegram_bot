from telegram import Update, ReplyKeyboardMarkup, Message, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from screens import Screen
import globalDefs 

async def send_reply_with_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, markup: ReplyKeyboardMarkup)->Message:
    context.user_data["last_markup_message"] = await context.bot.send_message(context._chat_id, text, reply_markup=markup)

async def send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str)->Message:
    context.user_data["last_message"] = await update.message.reply_html(text, reply_markup=ReplyKeyboardRemove())

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str)->Message:
    context.user_data["last_message"] = await context.bot.send_message(update.effective_chat.id, text, reply_markup=ReplyKeyboardRemove())

def setScreen(context: ContextTypes.DEFAULT_TYPE, screen: Screen) -> Screen:
    context.user_data[globalDefs.userdata_screen] = screen
    return screen

def getScreen(context: ContextTypes.DEFAULT_TYPE)->Screen:
    if globalDefs.userdata_screen in context.user_data:
        return context.user_data[globalDefs.userdata_screen]
    return None

async def getOrCreateLastMessage(context: ContextTypes.DEFAULT_TYPE)->Message:
    if "last_markup_message" in context.user_data:
        return context.user_data["last_markup_message"]
    else:
        await send_reply_with_keyboard(None, context, ".", None)
    return context.user_data["last_markup_message"]