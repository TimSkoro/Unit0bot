import telebot
from telebot import types
from telebot.types import Message
from utils import save_user_data, get_user_list, get_user_by_username, print_user_data
import qrcode
import io
import speech_recognition as sr
from pydub import AudioSegment

SECRET_KEY = 'Your-Secret-Key'

bot = telebot.TeleBot(SECRET_KEY, parse_mode=None)


@bot.message_handler(commands=['menu', 'start'])
def menu(message: Message):
    if message.text == '/start':
        print_user_data(message)
        save_user_data(message)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    button1 = types.KeyboardButton('/send_message')
    button2 = types.KeyboardButton('/user_list')
    button3 = types.KeyboardButton('/generate_qr_code')
    markup.add(button1, button2, button3)
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)


@bot.message_handler(commands=['generate_qr_code'])
def start_qrcode_generation(message: Message):
    bot.send_message(message.chat.id, "Send data for qr code creation:")
    bot.register_next_step_handler(message, qr_code_create)


def qr_code_create(message: Message):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(message.text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # We need to convert the image into BytesIO object
    with io.BytesIO() as output:
        img.save(output)
        output.seek(0)  # rewind file pointer to beginning
        bot.send_photo(message.chat.id, output)


@bot.message_handler(commands=['user_list'])
def user_list(message: Message):
    user_list = get_user_list()
    for user in user_list:
        bot.send_message(message.chat.id, user['username'])


@bot.message_handler(func=lambda message: "send" in message.text.lower() and "user" in message.text.lower())
def send_message_for_user(message: Message):
    clear_split_data = message.text.split(' ')
    split_data = message.text.lower().split(' ')
    send_index = split_data.index('send') + 1
    user_index = split_data.index('user') + 1
    username = clear_split_data[user_index]
    letter = " ".join(clear_split_data[send_index: user_index - 1])
    users = get_user_by_username(username)
    if users:
        user = users[0]
        bot.send_message(user['id'], f"Message from {message.from_user.first_name}: {letter}")
        bot.send_message(message.chat.id, f"Send '{letter}' for user {user['first_name']}")


@bot.message_handler(commands=['send_message'])
def send_message_first_step(message):
    user_list = get_user_list()

    markup = types.ReplyKeyboardMarkup(row_width=5)
    buttons = [types.KeyboardButton(user['username']) for user in user_list]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Choose user.", reply_markup=markup)
    bot.register_next_step_handler(message, send_message_step_two)


def send_message_step_two(message):
    many = True if " " in message.text or "," in message.text else False
    users = get_user_by_username(message.text, many=many)
    if not users:
        bot.reply_to(message, f"User {message.text} not found")
    else:
        bot.send_message(message.chat.id, 'Write your message:')
        bot.register_next_step_handler(message, send_message_finally, users)


def send_message_finally(message, users):
    letter = message.text
    for user in users:
        bot.send_message(user['id'], f"Message from {message.from_user.first_name}: {letter}")
        bot.send_message(message.chat.id, f"Send '{letter}' for user {user['first_name']}")


@bot.message_handler(content_types=['voice'])
def voice_processing(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open('voices/voice.ogg', 'wb') as new_file:
        new_file.write(downloaded_file)

    # Convert from ogg to wav using pydub
    AudioSegment.from_ogg("voices/voice.ogg").export("voices/voice.wav", format="wav")

    # Initialize recognizer
    r = sr.Recognizer()

    with sr.AudioFile('voices/voice.wav') as source:
        audio_data = r.record(source)
        text = r.recognize_google(audio_data, language='en-US')
        bot.reply_to(message, text)


bot.infinity_polling()
