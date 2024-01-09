from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bimmer_connected.account import MyBMWAccount
import datetime
from apscheduler.job import Job
from telegram import Update
from telegram.ext import ContextTypes

userdata_jobs = "charging_job"
userdata_creds = "bmw_creds"

class BMWCreds:
    password : str
    mail : str
    region : str
    vin : str
    account : MyBMWAccount

class ChargeJob:
    startTime: datetime
    endTime: datetime
    chatUpdate: Update
    chatContext: ContextTypes.DEFAULT_TYPE
    bmwCreds: BMWCreds
    startJob: Job
    endJob: Job
    endCharge: bool

jobs: AsyncIOScheduler