import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, Message, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, InlineQueryHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers import date
import bmwhandler
import commands
import globalDefs
import credentials
from datetime import datetime
from globalDefs import ChargeJob
from tgmethods import send_message, send_reply, send_reply_with_keyboard

globalDefs.jobs = AsyncIOScheduler()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ("state" not in context.user_data):
        context.user_data["state"] = "0"
    
    if (update.message.text.upper() == "CANCEL"):
        if context.user_data["state"].startswith("login"):
            if "bmw_creds" in context.user_data:
                del context.user_data["bmw_creds"]
        context.user_data["state"] = "0"
        await send_reply(update, context, "Operation was canceled")
        return

    if (update.message.text.upper() == "CHARGE"):
        await commands.charge_prompt(update, context)
        return

    if (update.message.text.upper() == "STOP"):
        await commands.stop_prompt(update, context)
        return
    
    else:
        handled = await commands.handle_state(update, context)
        if not handled:
            await send_reply(update, context, "Unknown command")

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if context.user_data["state"].startswith("login"):
        await commands.handle_vin_select(update, context, query)
    elif context.user_data["state"].startswith("jobs"):
        await commands.handle_job_delete(update, context, query)

async def login_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update, context, "Please enter your Mail")
    context.user_data["state"] = "login_1"

async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await commands.check_login(update, context):
        return
    
    if globalDefs.userdata_jobs not in context.user_data or len(context.user_data[globalDefs.userdata_jobs]) < 1:
        await send_reply(update, context, "You don't have any jobs")
        return
    
    text = "These are your charging jobs.\nClick one to cancel it."
    keyboard = []
    
    for job in context.user_data[globalDefs.userdata_jobs]:
        buttonText = ""
        if job.endCharge:
            buttonText += datetime.strftime(job.startTime, "%d.%m.%Y %H:%M") + " -> " + datetime.strftime(job.endTime, "%d.%m.%Y %H:%M")
        else:
            buttonText += datetime.strftime(job.startTime, "%d.%m.%Y %H:%M")
        keyboard.append([InlineKeyboardButton(buttonText, callback_data=context.user_data[globalDefs.userdata_jobs].index(job))])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await send_reply_with_keyboard(update, context, text, markup)
    context.user_data["state"] = "jobs_1"

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_reply(update, context, "BMW timed charging bot\nFirst, you have to login to your BMW Connected drive account. These credentials are only stored in RAM on the server, so you may have to enter them again later. Enter /login to get the login-promt.\nAfter that, enter /charge to schedule a new charging job\nEnter /jobs to get all planned charging jobs\nWith /stop you can stop charging and remove all scheduled jobs\n\nThis bot can't do anything else.\n\nYou can cancel any operation by typing 'cancel' btw.")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await commands.check_login(update, context):
        return
    await commands.stop_prompt(update, context)

async def charge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await commands.check_login(update, context):
        return
    await commands.charge_prompt(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(credentials.telegram_api_bot_token).build()
    
    start_handler = CommandHandler('start', start_cmd)
    charge_handler = CommandHandler('charge', charge_cmd)
    stop_handler = CommandHandler('stop', stop_cmd)
    login_handler = CommandHandler('login', login_cmd)
    jobs_handler = CommandHandler('jobs', jobs_cmd)

    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), cmd)
    application.add_handler(start_handler)
    application.add_handler(charge_handler)
    application.add_handler(stop_handler)
    application.add_handler(login_handler)
    application.add_handler(jobs_handler)
    application.add_handler(message_handler)
    application.add_handler(CallbackQueryHandler(handle_button))

    globalDefs.jobs.start()

    application.run_polling()