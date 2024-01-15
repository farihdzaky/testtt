from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, InlineQueryHandler, CallbackContext, CommandHandler
import logging
import random
import re
import html
from brainly_api import brainly
from telegram.constants import ParseMode

app = Flask(__name__)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.dispatcher.process_update(update)
    return jsonify({'status': 'ok'})

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat.id

    welcome_text = (
        "Halo! Aku bisa membantu kamu mencari jawaban di Brainly. "
        "Cukup ketikkan pertanyaanmu disini atau gunakan tombol inline dibawah! 😊"
    )

    inline_buttons = [
        InlineKeyboardButton("Channel 📢", url="https://t.me/nekozu2"),
        InlineKeyboardButton("Donate ☕", url="https://ko-fi.com/nekozu"),
        InlineKeyboardButton("Gunakan Inline 🚀", switch_inline_query="")
    ]

    keyboard = InlineKeyboardMarkup.from_row(inline_buttons)

    await update.message.reply_text(welcome_text, reply_markup=keyboard)

async def jawab(update: Update, context: CallbackContext) -> None:
    await handle_message(update)

async def cari(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type == 'group' or update.message.chat.type == 'supergroup':
        await handle_message(update)
    elif update.message.chat.type == 'private':
        await update.message.reply_text("Command hanya bisa digunakan di groups atau supergroups. 😅")

async def handle_inline(update: Update, context: CallbackContext) -> None:
    if len(update.inline_query.query) == 0:
        return

    inline_buttons = [
        InlineKeyboardButton("Channel 📢", url="https://t.me/nekozu2"),
        InlineKeyboardButton("Donate ☕", url="https://ko-fi.com/nekozu"),
    ]

    keyboard = InlineKeyboardMarkup.from_row(inline_buttons)

    user_id = update.inline_query.from_user.id
    scrap = brainly(update.inline_query.query, 20)
    results = []

    for i, selected in enumerate(scrap):
        question_text = f"<b>Pertanyaan:</b> {html.escape(selected.question.content)}\n"
        answer_text = f"{question_text}<b>Jawaban:</b> {html.escape(selected.answers[0].content)}\n"
        answer_text = re.sub(r'\n\s*\n', '\n', answer_text)
        combined_text = answer_text + question_text

        if len(combined_text) > 1024:
            continue

        thumburl = selected.question.attachments[0].url if selected.question.attachments else None

        escaped_title = f"Jawaban {i + 1} untuk: {html.escape(update.inline_query.query)}"

        if thumburl:
            result = {
                'type': 'photo',
                'id': str(i + 1),
                'photo_url': thumburl,
                'thumb_url': thumburl,
                'caption': combined_text,
                'parse_mode': 'HTML',
                'description': combined_text,
                'reply_markup':keyboard.to_dict()
            }
        else:
            result = {
                'type': 'article',
                'id': str(i + 1),
                'title': escaped_title,
                'input_message_content': {
                    'message_text': combined_text,
                    'parse_mode': 'HTML'
                },
                'description': combined_text,
                'reply_markup': keyboard.to_dict()
            }

        results.append(result)

    await update.inline_query.answer(results)

async def handle_message(update: Update) -> None:
    answer_text = ''
    text = ''
    inline_buttons = [
        InlineKeyboardButton("Channel 📢", url="https://t.me/nekozu2"),
        InlineKeyboardButton("Donate ☕", url="https://ko-fi.com/nekozu"),
        InlineKeyboardButton("Gunakan Inline 🚀", switch_inline_query="")
    ]
    keyboard = InlineKeyboardMarkup.from_row(inline_buttons)
    try:
        scrap = brainly(update.message.text, 50)
        selected = random.choice(scrap)

        text = f"*Pertanyaan:* {selected.question.content} \n"
        for i, answer in enumerate(selected.answers):
            text += f"\n*Jawaban {i + 1}:*\n{answer.content} \n"

        text = re.sub(r'\n\s*\n', '\n', text)
        text = text[:1024]
        text = re.sub(r'\\([^\\]+)\\', r'\1', text)
        text = text.replace('\\\\', '\\')
        text = re.sub(r'\\frac\{(.*?)\}\{(.*?)\}', r'(\1)/(\2)', text)
        text = text.replace('*', '')
        text = text.replace('_', '')

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

        for attachment in selected.question.attachments:
            await update.message.reply_photo(attachment.url, caption=text, parse_mode=ParseMode.MARKDOWN,
                                             reply_markup=keyboard)

        for answer in selected.answers:
            for attachment in answer.attachments:
                answer_text = f"*Jawaban:* {answer.content} \n"
                answer_text = re.sub(r'\n\s*\n', '\n', answer_text)
                answer_text = answer_text[:1024]
                answer_text = re.sub(r'\\([^\\]+)\\', r'\1', answer_text)
                answer_text = answer_text.replace('\\\\', '\\')
                answer_text = re.sub(r'\\frac\{(.*?)\}\{(.*?)\}', r'(\1)/(\2)', answer_text)
                answer_text = text.replace('*', '')
                answer_text = text.replace('_', '')
                await update.message.reply_photo(attachment.url, caption=answer_text, parse_mode=ParseMode.MARKDOWN,
                                                 reply_markup=keyboard)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"Answer Text: {answer_text}")
        logger.error(f"Text: {text}")

def main() -> None:
    try:
        # Set up the Updater and pass it the bot's token
        application = Application.builder().token("YOUR_BOT_TOKEN").build()

        # Get the dispatcher to register handlers

        # Register command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.ChatType.PRIVATE, jawab))
        application.add_handler(CommandHandler("cari", cari))

        # Register inline query handler
        application.add_handler(InlineQueryHandler(handle_inline))

        # Set the webhook for the Flask app
        #application.bot.setWebhook(url="https://yourdomain.com/webhook")

        # Run the Flask app
        app.run(port=5000, debug=True)

    except Exception as e:
        logger.error(f"An error occurred in main function: {e}")

if __name__ == '__main__':
    main()
