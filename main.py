#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from soundletter import *
import re
from uuid import uuid4
import os
from secret import TOKEN
from peewee import *
from playhouse.shortcuts import model_to_dict


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = int(os.environ.get('PORT', '8443'))

ADDRESS1, ADDRESS2, ADDRESS3, DEAR, TEXT, CONCLUSION, SIGNATURE = range(7)


db = SqliteDatabase("./main.db")


class Letter(Model):
    userid = BigIntegerField()
    address1 = TextField(null=True)
    address2 = TextField(null=True)
    address3 = TextField(null=True)
    dear = TextField(null=True)
    text = TextField(null=True)
    conclusion = TextField(null=True)
    signature = TextField(null=True)

    class Meta:
        database = db


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Visual sound waves letters generator.",
    )
    update.message.reply_text(
        "Use /new_letter to create a letter. Please keep in mind that, while we won't keep the data, it is going through some Google servers. We will however collect every end result!",
    )
    update.message.reply_photo(photo=open("example.jpg", 'rb'), caption="Here is an indication for the different parts.")
    update.message.reply_text(
        "If you have any concerns, you can contact @Stache on Telegram.",
    )
    c = _need()
    update.message.reply_text("Current number of letters:\n{}{} {}%".format("▓" * (c // 5), "░" * ((100 - c) // 5), c))


def new_letter(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    logger.info("%s (%s) is writing a letter...", user.first_name, user.id)

    try:
        letter = Letter.get(userid=user.id)
        letter.delete_instance()
    except:
        pass
    letter = Letter(userid=user.id).save()

    update.message.reply_text(
        "Let's create a sound letter together.",
    )
    update.message.reply_text(
        "I am going to ask you to send me different parts of the letter, you will have to send a piece of text corresponding to the part. You can send /skip if you don't want to fill the desired end - the letter will be adapted accordingly.",
    )
    update.message.reply_text(
        "Send /cancel to stop the creation at any time.",
    )
    update.message.reply_text(
        "Let's start with the first line of the address:",
    )

    return ADDRESS1


def address1(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.address1 = content
        letter.save()

    update.message.reply_text("Adress line 2:")

    return ADDRESS2


def address2(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.address2 = content
        letter.save()

    update.message.reply_text("Adress line 3:")

    return ADDRESS3


def address3(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.address3 = content
        letter.save()

    update.message.reply_text("Introduction (\"Dear something\"):")

    return DEAR


def dear(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.dear = content
        letter.save()

    update.message.reply_text("Text (if too long, will be cropped):")

    return TEXT


def text(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.text = content
        letter.save()

    update.message.reply_text("Conclusion (\"Best regards,\"):")

    return CONCLUSION


def conclusion(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.conclusion = content
        letter.save()

    update.message.reply_text("Signature:")

    return SIGNATURE


def signature(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        letter = Letter.get(Letter.userid == user.id)
        letter.signature = content
        letter.save()

    update.message.reply_text("It's over! Thank you for your participation.")

    result = EXAMPLE.copy()
    letter = Letter.get(Letter.userid == user.id)
    letter_dict = model_to_dict(letter)

    for k, v in letter_dict.items():
        if k in result:
            if v:
                result[k]['text'] = v
            else:
                del result[k]

    if not letter.address1 and not letter.address2 and not letter.address3:
        del result['space1']
    if not letter.dear:
        del result['space2']
    if not letter.text:
        del result['space3']

    logger.info("... Processing ...")
    update.message.reply_text("Your file is being generated, please wait a little while...")
    username = re.sub(r'[\\/*~?:"<>|]', "-", user.first_name)
    filename = os.path.join("results/", "{}_{}.pdf".format(username, str(uuid4())))
    process(result, filename=filename, verbatim=True)
    logger.info("... File saved ...")

    update.message.reply_text("It's ready!")
    update.message.reply_document(document=open(filename, 'rb'), filename="Letter from {}.pdf".format(username))
    logger.info("... File sent ...")

    letter.delete_instance()

    update.message.reply_text("Thank you for joining in. Feel free to create a new letter with /start.")
    update.message.reply_text("If you are going to print it, feel free to send me (@Stache) a little photo - if it's okay for you, of course!")

    logger.info("%s (%s) is done with their letter...", user.first_name, user.id)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("%s (%s) does not want a letter no more...", user.first_name, user.id)

    update.message.reply_text(
        'Feel free to use /new_letter to start the conversation again.'
    )
    Letter.delete().where(Letter.userid == user.id).execute()

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("""/start - Get a general knowledge on what you shall create!
/new_letter - Start the creation of a sound new letter.
/skip - Skip a specific part of the letter.
/cancel - Cancel the creation of a letter.
/help - All commands available.
/needed - Display how many letters are needed for the project.""")


def _need():
    l = len([name for name in os.listdir("./results/") if os.path.isfile(os.path.join("./results/", name))]) - 1
    t = 50
    c = int(100 * l / t) if l < t else 100
    return c


def needed(update: Update, context: CallbackContext) -> None:
    c = _need()
    update.message.reply_text("Current number of letters:\n{}{} {}%".format("▓" * (c // 5), "░" * ((100 - c) // 5), c))


def downloader(update, context) -> None:
    # writing to a custom file
    with open("./temp.json", 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)


def main() -> None:
    db.connect()
    db.create_tables([Letter])

    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new_letter', new_letter)],
        states={
            ADDRESS1: [MessageHandler(Filters.text & ~Filters.command, address1), CommandHandler('skip', address1)],
            ADDRESS2: [MessageHandler(Filters.text & ~Filters.command, address2), CommandHandler('skip', address2)],
            ADDRESS3: [MessageHandler(Filters.text & ~Filters.command, address3), CommandHandler('skip', address3)],
            DEAR: [MessageHandler(Filters.text & ~Filters.command, dear), CommandHandler('skip', dear)],
            TEXT: [MessageHandler(Filters.text & ~Filters.command, text), CommandHandler('skip', text)],
            CONCLUSION: [MessageHandler(Filters.text & ~Filters.command, conclusion), CommandHandler('skip', conclusion)],
            SIGNATURE: [MessageHandler(Filters.text & ~Filters.command, signature), CommandHandler('skip', signature)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("needed", needed))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, help_command))

    # Start the Bot
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=PORT,
    #                       url_path=TOKEN)
    # updater.bot.set_webhook("hidden-savannah-50354" + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
