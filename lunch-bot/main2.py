#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""
import logging
import json

from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, PicklePersistence

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def dbhelper_add_order(context, username, option):
    order_list = dphelper_get_list(context)
    order_list.append([username, option])
    return len(order_list)

def dbhelper_clear_order(context, username):
    order_list = dphelper_get_list(context)
    order_list = list(filter(lambda x: x[0] != username, order_list))
    dphelper_set_list(context, order_list)

def dphelper_get_list(context):
    return context.bot_data.setdefault(dbhelper_get_key(), [])    

def dphelper_set_list(context, list_):
    key = dbhelper_get_key()
    context.bot_data[key] = list_

def dphelper_get_summary(context):
    order_list = dphelper_get_list(context)
    return order_list

def dbhelper_new(context):
    key = dbhelper_get_key()
    dbhelper_drop(context)
    dbhelper_set_state(context, "OPEN")
    context.bot_data.setdefault(key, [])

def dbhelper_drop(context):
    key = dbhelper_get_key()
    if key in context.bot_data:
        del context.bot_data[key]

def dbhelper_is_exist(context):
    key = dbhelper_get_key()
    return key in context.bot_data     

def dbhelper_get_state(context):
    key = dbhelper_get_key() + "_state"
    if key in context.bot_data:
        return context.bot_data[key]
    return "CLOSE"

def dbhelper_set_state(context, state):
    key = dbhelper_get_key() + "_state"
    context.bot_data[key] = state

def dbhelper_get_key():
    return "list_{}".format(datetime.now().strftime("%Y%m%d"))

def order(update, context):

    if dbhelper_get_state(context) != "OPEN":
        update.message.reply_text("Quán cơm chưa mở cửa. Gọi anh Cường để mở!")
        return

    LOCALIZE = context.bot_data['menu']
    index = 0
    group = []
    keyboard = []
    for item in LOCALIZE.items():
        index += 1
        if index % 3 == 0 :
            keyboard.append(group)
            group = []
        group.append(InlineKeyboardButton(item[1], callback_data=item[0]))        
    if len(group) > 0:
        keyboard.append(group)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)


def button(update, context):
    LOCALIZE = context.bot_data['menu']

    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()
    chat_user_client = query.message.reply_to_message.from_user.username
    total = dbhelper_add_order(context, chat_user_client, query.data)
    query.edit_message_text(text="Chọn món: {} bởi @{} \nTổng đơn: {} , xem lại /summary".format(LOCALIZE[query.data], chat_user_client, total))

def cancel_command(update, context):
    username = update.message.from_user.username
    dbhelper_clear_order(context, username)
    update.message.reply_text("{} hủy đơn thành công".format(username))

def open_command(update, context):
    f = open("menu.txt", encoding="UTF-8")
    lines = f.readlines()
    LOCALIZE = {}
    index = 0
    for line in lines:
        index = index + 1
        LOCALIZE[str(index)] = line.replace('\n','')
    dbhelper_new(context)
    context.bot_data['menu'] = LOCALIZE
    text = "Tới giờ đặt cơm. Xin mời chọn món:\n\n{}\n\n{}".format('\n'.join(list(LOCALIZE.values())), " -> Dùng lệnh /order để đặt")    
    update.message.reply_text(text)

def summary_command(update, context):
    result = dphelper_get_list(context)
    
    data = {}
    for order in result: 
        if order[1] not in data:
            data[order[1]] = []
        data[order[1]].append(order[0])
    text = ""
    sorted_data = sorted(data.items(), key=lambda x: len(x[1]), reverse=True)
    LOCALIZE = context.bot_data['menu']
    total = 0
    for item in sorted_data:
        dishes = LOCALIZE[item[0]]
        if type(item[1])==list and len(item[1]) > 0:
            text += "- {} (SL: {}): {}\n".format(dishes, len(item[1]), ", ".join(item[1]))
            total += len(item[1])
    update.message.reply_text("Danh sách đăng ký cơm {}:\n{} \n Tổng cộng: {} suất".format(dbhelper_get_key(), text, total))

def money_command(update, context):
    result = dphelper_get_list(context)
    
    data = {}
    for order in result: 
        if order[0] not in data:
            data[order[0]] = []
        data[order[0]].append(order[0])
    text = ""
    sorted_data = sorted(data.items(), key=lambda x: len(x[1]), reverse=True)
    LOCALIZE = context.bot_data['menu']
    total = 0
    for item in sorted_data:
        text += "- {} (SL: {}): {} VND\n".format(item[0], len(item[1]), len(item[1]*35000))
        total += len(item[1])
    update.message.reply_text("Bill tính tiền {}:\n{} \n Tổng cộng: {} suất".format(dbhelper_get_key(), text, total))

def help_command(update, context):
    update.message.reply_text(" /order Đặt cơm.\n /cancel hủy cơm.\n /open /reset mở đơn mới/ mở lại ngày hôm nay \n /summary để tổng hợp\n /bill để tính tiền")    

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    pp = PicklePersistence(filename='lunch')
    updater = Updater("1104322131:AAGPE5A8Mwo8CUKejxYmGHOPw4U8on7M83g", use_context=True, persistence=pp)

    updater.dispatcher.add_handler(CommandHandler('open', open_command))
    updater.dispatcher.add_handler(CommandHandler('reset', open_command))
    updater.dispatcher.add_handler(CommandHandler('order', order))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('cancel', cancel_command))
    #updater.dispatcher.add_handler(CommandHandler('close', close_command))
    updater.dispatcher.add_handler(CommandHandler('summary', summary_command))
    updater.dispatcher.add_handler(CommandHandler('bill', money_command))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()