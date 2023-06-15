import json
import redis

database = redis.Redis(host='localhost', port=6379, db=0)


def print_user_data(message):
    template = """
    ----------------------------------------
    id: {id}
    first name: {first_name}
    last name: {last_name}
    username: {username}
    language: {language}
    is bot: {is_bot}
    """.format(
        username=message.chat.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        is_bot=message.from_user.is_bot,
        language=message.from_user.language_code,
        id=message.from_user.id,
    )
    print(template)


def save_user_data(message):
    user_data = message.from_user.to_dict()
    user_data['chat_id'] = message.chat.id
    users = json.loads(database.get('users') or '[]')
    if user_data not in users:
        users.append(user_data)
        database.set('users', json.dumps(users))


def get_user_list():
    users = json.loads(database.get('users') or '[]')
    return users


def get_user_names_from_string(user_name_string):
    if " " in user_name_string:
        return user_name_string.split(" ")
    elif "," in user_name_string:
        return user_name_string.split(",")
    else:
        return [user_name_string]


def get_user_by_username(usernames, many=False):
    user_list = get_user_list()
    user_names_list = get_user_names_from_string(usernames)
    users = list(filter(lambda user: user['username'] in user_names_list, user_list))
    if users and not many:
        return users[:1]
    elif users and many:
        return users
