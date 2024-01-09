from bimmer_connected.account import MyBMWAccount
from bimmer_connected.api.regions import Regions
from bimmer_connected.vehicle.fuel_and_battery import ChargingState
import globalDefs
from globalDefs import ChargeJob, BMWCreds, userdata_jobs
from tgmethods import send_message, send_reply, send_reply_with_keyboard

async def login(mail: str, pw: str, region: str)->MyBMWAccount:
    bmw_region: str
    if region.upper() == "NA":
        bmw_region = Regions.NORTH_AMERICA
    elif region.upper() == "CN":
        bmw_region = Regions.CHINA
    else:
        bmw_region = Regions.REST_OF_WORLD
    
    return MyBMWAccount(mail, pw, bmw_region)

async def get_vehicle_state_str(bmwCreds: BMWCreds) -> str:
    await bmwCreds.account.get_vehicles()
    vehicle = bmwCreds.account.get_vehicle(bmwCreds.vin)
    return "Couldn't start charging.\nSoC: " + str(vehicle.fuel_and_battery.remaining_battery_percent) + "%\nTarget: " + str(vehicle.fuel_and_battery.charging_target) + "%\nCharging state: " + str(vehicle.fuel_and_battery.charging_status) + "\nCharger connected: " + str(vehicle.fuel_and_battery.is_charger_connected)

async def start_charge(job: ChargeJob):
    await job.bmwCreds.account.get_vehicles()
    vehicle = job.bmwCreds.account.get_vehicle(job.bmwCreds.vin)
    if vehicle.fuel_and_battery.is_charger_connected and vehicle.fuel_and_battery.charging_target > vehicle.fuel_and_battery.remaining_battery_percent:
        await vehicle.remote_services.trigger_charge_start()
        await send_message(job.chatUpdate, job.chatContext, "Started charging vehicle.\nSoC: " + str(vehicle.fuel_and_battery.remaining_battery_percent) + "%\nTarget: " + str(vehicle.fuel_and_battery.charging_target) + "%")
    else:
        await send_message(job.chatUpdate, job.chatContext, "Couldn't start charging.\nSoC: " + str(vehicle.fuel_and_battery.remaining_battery_percent) + "%\nTarget: " + str(vehicle.fuel_and_battery.charging_target) + "%\nCharging state: " + str(vehicle.fuel_and_battery.charging_status) + "\nCharger connected: " + str(vehicle.fuel_and_battery.is_charger_connected))
    if not job.endCharge:
        if userdata_jobs in job.chatContext.user_data:
            if job in job.chatContext.user_data[userdata_jobs]:
                job.chatContext.user_data[userdata_jobs].remove(job)

async def end_charge(job: ChargeJob):
    await job.bmwCreds.account.get_vehicles()
    vehicle = job.bmwCreds.account.get_vehicle(job.bmwCreds.vin)
    if vehicle.fuel_and_battery.is_charger_connected and vehicle.fuel_and_battery.charging_target > vehicle.fuel_and_battery.remaining_battery_percent and vehicle.fuel_and_battery.charging_status == ChargingState.CHARGING:
        await vehicle.remote_services.trigger_charge_stop()
        await send_message(job.chatUpdate, job.chatContext, "Stopped charging vehicle.\nSoC: " + str(vehicle.fuel_and_battery.remaining_battery_percent) + "%\nTarget: " + str(vehicle.fuel_and_battery.charging_target) + "%")
    else:
        await send_message(job.chatUpdate, job.chatContext, "Couldn't stop charging.\nSoC: " + str(vehicle.fuel_and_battery.remaining_battery_percent) + "%\nTarget: " + str(vehicle.fuel_and_battery.charging_target) + "%\nCharging state: " + str(vehicle.fuel_and_battery.charging_status) + "\nCharger connected: " + str(vehicle.fuel_and_battery.is_charger_connected))
    if userdata_jobs in job.chatContext.user_data:
        if job in job.chatContext.user_data[userdata_jobs]:
            job.chatContext.user_data[userdata_jobs].remove(job)