from telegram import InlineKeyboardButton, Update, Message, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes
import uuid
from collections.abc import Callable

class Screen:
    text: str
    buttons: [[InlineKeyboardButton]]
    buttonActions: dict
    update: Update
    context: ContextTypes.DEFAULT_TYPE

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
        self.text = None
        self.buttons = [[]]
        self.buttonActions = dict()
    
    async def render(self, message: Message):
        print(message)
        await message.edit_text(self.text)
        markup: InlineKeyboardMarkup = InlineKeyboardMarkup(self.buttons)
        await message.edit_reply_markup(markup)
        #await self.context.bot.send_message(self.context._chat_id, self.text, reply_markup=markup)

    async def buttonClicked(self, query: CallbackQuery):
        actionId: str = query.data
        self.buttonActions[actionId]()
        await query.answer()

    def newButton(self, text: str, func: Callable)->InlineKeyboardButton:
        actionId: str = str(uuid.uuid4())
        self.buttonActions[actionId] = func
        return InlineKeyboardButton(text, callback_data=actionId)

class MainScreen(Screen):
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        super().__init__(update, context)
        self.text = "Main Screen test"
        self.buttons = [[self.newButton("Test Button 1", self.testButton_click)]]
    
    def testButton_click(self):
        print("Test 1 clicked - " + str(self.context._chat_id) + " " + str(self.context._user_id))