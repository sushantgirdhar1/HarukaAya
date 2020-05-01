from typing import Optional

from telegram import Message, Update, Bot, User
from telegram import MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

from haruka import dispatcher
from haruka.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from haruka.modules.sql import dnd_sql as sql
from haruka.modules.users import get_user_id

from haruka.modules.translations.strings import tld

DND_GROUP = 7
DND_REPLY_GROUP = 8


@run_async
def dnd(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = ""

    sql.set_dnd(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    update.effective_message.reply_text(tld(chat.id, f"{fname} is now on DND Mode 📵 . Studying Maybe 🤷🏻‍♀️🤷🏻‍♂️ . Do not Disturb him Please 😌📚."))


@run_async
def no_longer_dnd(bot: Bot, update: Update):
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    if not user:  # ignore channels
        return

    res = sql.rm_dnd(user.id)
    if res:
        firstname = update.effective_user.first_name
        try:
            update.effective_message.reply_text(tld(chat.id, f"{firstname} is now back online .📝!"))
        except:
            return

@run_async
def reply_dnd(bot: Bot, update: Update):
    message = update.effective_message  # type: Optional[Message]
    if message.entities and message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION])
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

            elif ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset + ent.length])
                if not user_id:
                    # Should never happen, since for a user to become dnd they must have spoken. Maybe changed username?
                    return
                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for dnd module".format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_dnd(bot, update, user_id, fst_name)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_dnd(bot, update, user_id, fst_name)


def check_dnd(bot, update, user_id, fst_name):
    chat = update.effective_chat  # type: Optional[Chat]
    if sql.is_dnd(user_id):
        user = sql.check_dnd_status(user_id)
        if not user.reason:
            res = tld(chat.id, f"{fst_name} is on DND Mode 📵 .")
        else:
            res = tld(chat.id, f"{fst_name} is now on DND Mode 📵 .He Says 👉🏻:\n{user.reason}")
        update.effective_message.reply_text(res)


__help__ = """
 - /dnd <reason>: mark yourself as DND.
 - brb <reason>: same as the dnd command - but not a command.
When marked as DND , any mentions will be replied to with a message to say that you're on DND Mode .
"""

__mod_name__ = "DND"

DND_HANDLER = DisableAbleCommandHandler("dnd", dnd)
DND_REGEX_HANDLER = DisableAbleRegexHandler("(?i)brb", dnd, friendly="dnd")
NO_DND_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_dnd)
DND_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_dnd)

dispatcher.add_handler(DND_HANDLER, DND_GROUP)
dispatcher.add_handler(DND_REGEX_HANDLER, DND_GROUP)
dispatcher.add_handler(NO_DND_HANDLER, DND_GROUP)
dispatcher.add_handler(DND_REPLY_HANDLER, DND_REPLY_GROUP)
