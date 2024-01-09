from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
import datetime
import bmwhandler
import globalDefs
from globalDefs import BMWCreds, ChargeJob
from tgbot import send_reply, send_reply_with_keyboard, send_message

async def check_login(update: Update, context: ContextTypes.DEFAULT_TYPE)->bool:
    if globalDefs.userdata_creds in context.user_data:
        bmwcreds: BMWCreds = context.user_data[globalDefs.userdata_creds]
        if len(bmwcreds.vin) > 0:
            return True
    await send_message(update, context, "Please login first using /login")
    return False
        
async def charge_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_login(update, context):
        return
    await send_reply(update, context, "Please enter a from time")
    context.user_data["state"] = "charge_1"

async def stop_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_login(update, context):
        return
    job = ChargeJob()
    job.bmwCreds = context.user_data[globalDefs.userdata_creds]
    job.chatContext = context
    job.chatUpdate = update
    await bmwhandler.end_charge(job)
    if globalDefs.userdata_jobs in context.user_data:
        for job2 in context.user_data[globalDefs.userdata_jobs]:
            job2.startJob.remove()
            job2.endJob.remove()
        context.user_data[globalDefs.userdata_jobs].clear()
    context.user_data["state"] = "0"

async def cancel_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data["state"] == "0":
        await send_reply(update, context, "Nothing to cancel")
    else:
        await send_reply(update, context, "Cancled current operation")
    context.user_data["state"] = "0"

async def handle_state(update: Update, context: ContextTypes.DEFAULT_TYPE)->bool:
    found = await handle_charging_states(update, context)
    if not found:
        found = await handle_login_states(update, context)
    
    return found

async def handle_login_states(update: Update, context: ContextTypes.DEFAULT_TYPE)->bool:
    if context.user_data["state"] == "login_1":
        bmwcreds = BMWCreds()
        bmwcreds.mail = update.message.text
        context.user_data[globalDefs.userdata_creds] = bmwcreds
        await send_reply(update, context, "Please enter your password")
        context.user_data["state"] = "login_2"

    elif context.user_data["state"] == "login_2":
        bmwcreds: BMWCreds = context.user_data[globalDefs.userdata_creds]
        bmwcreds.password = update.message.text
        await update.message.delete()
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="CN - China"), KeyboardButton(text="NA - North America")], [KeyboardButton(text="RW - Rest of the world")]])
        await send_reply_with_keyboard(update, context, "Please select a region", markup)
        context.user_data["state"] = "login_3"

    elif context.user_data["state"] == "login_3":
        bmwcreds: BMWCreds = context.user_data[globalDefs.userdata_creds]
        bmwcreds.region = update.message.text[0:2]
        bmwcreds.account = await bmwhandler.login(bmwcreds.mail, bmwcreds.password, bmwcreds.region)
        success = False
        try:
            await bmwcreds.account.get_vehicles()
            success = True
        except (Exception) as ex:
            await send_reply(update, context, "Login failed, please try again by running /login again")
            context.user_data["state"] = "0"
        if success:
            await send_reply(update, context, "Logged in successfully")
            keyboard = []
            for vehicle in bmwcreds.account.vehicles:
                vin = vehicle.vin
                model = vehicle.name
                keyboard.append([InlineKeyboardButton(vin + " - " + model, callback_data=vin)])
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await send_reply_with_keyboard(update, context, "Please choose a car", markup)
            context.user_data["state"] = "login_4"

    else:
        return False
    return True

async def handle_vin_select(update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery):
    if context.user_data["state"] != "login_4":
         await send_message(update, context, "Please run /login again to change the VIN")
    else:
        bmwcreds: BMWCreds = context.user_data[globalDefs.userdata_creds]
        bmwcreds.vin = query.data
        await send_message(update, context, "You selected VIN " + bmwcreds.vin + "\nSetup is now complete")
        context.user_data["state"] = "0"

async def handle_job_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, query: CallbackQuery):
    if context.user_data["state"] != "jobs_1":
         await send_message(update, context, "Please run /jobs again to manage your charging jobs")
    else:
        job: ChargeJob
        job = context.user_data[globalDefs.userdata_jobs][int(query.data)]
        job.startJob.remove()
        if job.endCharge:
            job.endJob.remove()
        context.user_data[globalDefs.userdata_jobs].remove(job)
        await send_message(update, context, "Removed job")
        context.user_data["state"] = "0"

async def handle_charging_states(update: Update, context: ContextTypes.DEFAULT_TYPE)->bool:
    if context.user_data["state"] == "charge_1":
        time = datetime.datetime.strptime(update.message.text, "%H:%M")
        currentTime = datetime.datetime.today()
        time = time.replace(day=currentTime.day, month=currentTime.month, year=currentTime.year)
        if currentTime.hour > time.hour:
            time += datetime.timedelta(days=1)
        context.user_data["fromTime"] = time
        await send_reply(update, context, "Please enter a to time")
        context.user_data["state"] = "charge_2"

    elif context.user_data["state"] == "charge_2":
        time = datetime.datetime.strptime(update.message.text, "%H:%M")
        currentTime = datetime.datetime.today()
        time = time.replace(day=currentTime.day, month=currentTime.month, year=currentTime.year)
        if currentTime.hour > time.hour:
            time += datetime.timedelta(days=1)
        context.user_data["toTime"] = time
        markup = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Yes", ), KeyboardButton(text="No")]])
        await send_reply_with_keyboard(update, context, "You entered a charge time from " + datetime.datetime.strftime(context.user_data["fromTime"], "%d.%m.%Y %H:%M") + " to " + datetime.datetime.strftime(context.user_data["toTime"], "%d.%m.%Y %H:%M") + ". Is this correct?", markup)
        context.user_data["state"] = "charge_3"

    elif context.user_data["state"] == "charge_3":
        if update.message.text.upper() == "YES":
            chargeJob = ChargeJob()
            chargeJob.chatUpdate = update
            chargeJob.chatContext = context
            chargeJob.startTime = context.user_data["fromTime"]
            chargeJob.endTime = context.user_data["toTime"]
            chargeJob.startJob = globalDefs.jobs.add_job(bmwhandler.start_charge, "date", run_date=context.user_data["fromTime"], args=[chargeJob])
            chargeJob.endJob = globalDefs.jobs.add_job(bmwhandler.end_charge, "date", run_date=context.user_data["toTime"], args=[chargeJob])
            chargeJob.endCharge = True
            chargeJob.bmwCreds = context.user_data[globalDefs.userdata_creds]
            if globalDefs.userdata_jobs not in context.user_data:
                context.user_data[globalDefs.userdata_jobs] = []
            context.user_data[globalDefs.userdata_jobs].append(chargeJob)
            await send_reply(update, context, "Added charging job")
        context.user_data["state"] = "0"

    else:
        return False
    return True