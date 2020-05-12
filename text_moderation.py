def format_ingredients(text):
    data = {'1/2 ч.лож.': 'половина чайной ложки',
            '1 ч.лож.': 'чайная ложка',
            'ч.лож.': 'чайные ложки',
            '1/2 ст.лож.': 'половина столовой ложки',
            '1 ст.лож.': 'столовая ложка',
            'ст.лож.': 'столовые ложеки',
            '1/2': 'половина',
            'гр.': 'г', ' -': ' - ', '.': ''}
    for i in data.keys():
        if i in text:
            text = text.replace(i, data[i])
    t = ''
    for i in text.split('!'):
        t += '\n'.join(list(map(lambda x: x.strip().capitalize(), i.split(', ')))) + '\n'
    return t


def format_name(text):
    text = text.strip()
    if '*' in text:
        c = text.count('*')
        text = text.replace('*' * c, ' - Версия ' + str(c))
    print(text)
