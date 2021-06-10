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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

ADDRESS1, ADDRESS2, ADDRESS3, DEAR, TEXT, CONCLUSION, SIGNATURE = range(7)


def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user

    logger.info("%s (%s) is writing a letter...", user.first_name, user.id)
    context.user_data[user.id] = EXAMPLE.copy()

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
        "If you have any concerns, you can contact @Stache on Telegram.",
    )
    update.message.reply_text(
        "Let's start with the first line of the address.",
    )

    return ADDRESS1


def address1(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['address1']['text'] = content
    else:
        del context.user_data[user.id]['address1']

    update.message.reply_text("address2.")

    return ADDRESS2


def address2(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['address2']['text'] = content
    else:
        del context.user_data[user.id]['address2']

    update.message.reply_text("address3.")

    return ADDRESS3


def address3(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['address3']['text'] = content
    else:
        del context.user_data[user.id]['address3']

    try:
        a, b, c = context.user_data[user.id]['address1'], context.user_data[user.id]['address2'], context.user_data[user.id]['address3']
    except:
        del context.user_data[user.id]['space1']

    update.message.reply_text("dear.")

    return DEAR


def dear(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['dear']['text'] = content
    else:
        del context.user_data[user.id]['dear']
        del context.user_data[user.id]['space2']

    update.message.reply_text("text.")

    return TEXT


def text(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['text']['text'] = content
    else:
        del context.user_data[user.id]['text']
        del context.user_data[user.id]['space3']

    update.message.reply_text("conclusion.")

    return CONCLUSION


def conclusion(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['conclusion']['text'] = content
    else:
        del context.user_data[user.id]['conclusion']

    update.message.reply_text("signature.")

    return SIGNATURE


def signature(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    content = update.message.text

    if content != '/skip':
        context.user_data[user.id]['signature']['text'] = content
    else:
        del context.user_data[user.id]['signature']

    update.message.reply_text("It's over! Thank you for your participation.")

    logger.info("... Processing ...")
    update.message.reply_text("Your file is being generated, please wait a little while...")
    username = re.sub(r'[\\/*?:"<>|]', "-", user.first_name)
    filename = os.path.join("results/", "{}_{}.pdf".format(username, str(uuid4())))
    process(context.user_data[user.id], filename=filename, verbatim=True)
    logger.info("... File saved ...")

    update.message.reply_text("It's ready!")
    update.message.reply_document(document=open(filename, 'rb'), filename="Letter from {}.pdf".format(username))
    logger.info("... File sent ...")

    context.user_data[user.id].clear()

    update.message.reply_text("Thank you for joining in. Feel free to create a new letter with /start.")
    update.message.reply_text("If you are going to print it, feel free to send me (@Stache) a little photo - if it's okay for you, of course!")

    logger.info("%s (%s) is done with their letter...", user.first_name, user.id)

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("%s (%s) does not want a letter no more...", user.first_name, user.id)

    update.message.reply_text(
        'Feel free to use /start to start the conversation again.'
    )
    context.user_data[user.id].clear()

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text("To start creating a letter, use /start.")


def downloader(update, context) -> None:
    # writing to a custom file
    with open("./temp.json", 'wb') as f:
        context.bot.get_file(update.message.document).download(out=f)


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
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

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
