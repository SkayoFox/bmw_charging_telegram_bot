from telegram import Update, ReplyKeyboardMarkup, Message, ReplyKeyboardRemove
from telegram.ext import ContextTypes

async def send_reply_with_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, markup: ReplyKeyboardMarkup)->Message:
    context.user_data["last_markup_message"] = await update.message.reply_html(text, reply_markup=markup)

async def send_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str)->Message:
    context.user_data["last_message"] = await update.message.reply_html(text, reply_markup=ReplyKeyboardRemove())

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str)->Message:
    context.user_data["last_message"] = await context.bot.send_message(update.effective_chat.id, text, reply_markup=ReplyKeyboardRemove())