# Подключаем библиотеки
import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'google_module/token.json'  # Имя файла с закрытым ключом

# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

# Запрос к таблице
def get(spreadsheetId:str, range_g):
    """
    Запрашиваем данные из таблицы
    spreadsheetId - url таблицы
    range_g - лист + диапозон, с которого нужно данные подгружать
    """
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 

    resp = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=range_g).execute() # Запрашиваем данные
    return resp


# async def check_table(url:str):
#     resp = get(url, f"'Отдел развития'!A1:A100000")
#     answer = 1

#     if "values" not in resp:
#         return answer
    
#     if resp["values"] != []:
#         answer = len(resp["values"])

#     return answer


async def put_values(url:str, values:list):
    """
    Помещаем данные в таблицу
    values - список с данными. Его будем изменять
    url - часть ссылки на гугл таблицу    
    """
    del values[2]
    # Извеняем под таблицу данные
    body = {
        'values' : [
            [values[1]["text"]] + [values[4]] + values[3:1:-1] + [values[-1]]
        ]
    }
    httpAuth = credentials.authorize(httplib2.Http()) # Авторизуемся в системе
    service = apiclient.discovery.build('sheets', 'v4', http = httpAuth) # Выбираем работу с таблицами и 4 версию API 
    
    # Пытаемся засунуть данные с таблицу
    while True:
        try:
            resp = service.spreadsheets().values().append(
                spreadsheetId=url, 
                range=f"'{values[0]}'!A1", 
                valueInputOption="RAW", 
                body=body).execute()
            break
        except:
            await asyncio.sleep(5)

    return resp
