from lisad import *
from sys import argv
from prefilled_input import prefilled_input
from getch import getch # 1 täht korraga lugemine
from fs import open_fs
from mutagen.easyid3 import EasyID3

import os
import fs
import mutagen

extensions = (".mp3", ".aac", ".flac", ".m4a", ".mka", ".mp4", ".mxmf", ".ogg", ".wav", ".webm")
columns = { 0:'Directory', 1:'Name', 2:'Size', 3:'Modified', 4:'Created', 5:'Sample Rate', 6:'Bit Rate',
            7:'Channels', 8:'Duration', 9:'Title', 10:'Artist', 11:'Album', 12:'Album Artist',
            13:'Contributing Artists', 14:'Track Number', 15:'Year', 16:'Genre', 17:'Composer', 18:'Writer',
            19:'Key', 20:'BPM' }
#               0   1   2   3   4   5   6  7  8   9  10  11  12  13 14 15  16  17  18 19 20
column_sizes = [3, 24, 10, 16, 16, 11, 11, 8, 9, 16, 16, 10, 10, 10, 8, 5, 10, 10, 10, 4, 4]

drives = get_drives()
b_drives = [drive[0].encode() for drive in drives]

columns_visible = [0, 1, 2, 3, 6, 8, 9, 10, 11, 13, 15, 16, 17, 19, 20]
sorted_by = 1
view_lines = 32
cursor_line = 0
cursor_column = 0
view_position = 0
editing = False
current_dir = os.getcwd().replace('\\', '/') + '/'
last_dir = ''
path_prefix = current_dir[0] + ':/'
last_prefix = ''
current_dir = current_dir[2:]
message = ''
dir = []

home_fs = open_fs(path_prefix)

bell_on = True
def bell():
    if bell_on:
        print('\a')

# loob kirje failide nimekirja lisamiseks; määramata väärtustele paneb väärtuseks ''
def list_entry(**data):
    return [data.get(y, '') for x, y in columns.items()]

def pgup():
    global cursor_line, view_position
    cursor_line -= view_lines
    view_position -= view_lines
    if cursor_line < 0: cursor_line = 0
    if view_position < 0: view_position = 0

def pgdown():
    global cursor_line, view_position
    cursor_line += view_lines
    view_position += view_lines
    if cursor_line >= len(dir)-1: cursor_line = len(dir)-2
    if view_position + view_lines >= len(dir)-1: view_position = len(dir)-1-view_lines

#kui kasutaja vajutab nool üles
def up():
    global cursor_line, view_position
    if cursor_line > 0:
        cursor_line -= 1
        if view_position > cursor_line:
            view_position = cursor_line
    else:
        bell()

#kui kasutaja vajutab nool alla
def down():
    global cursor_line, view_position
    if cursor_line < len(dir)-1:
        cursor_line += 1
        if view_position + view_lines <= cursor_line:
            view_position = cursor_line - view_lines + 1
    else:
        bell()

#kui kasutaja vajutab nool paremale
def right():
    global cursor_column
    if cursor_column < len(columns_visible)-1:
        cursor_column += 1

#kui kasutaja vajutab nool vasakule
def left():
    global cursor_column
    if cursor_column > 0:
        cursor_column -= 1

def saveInfo():
    pass

def isCellEditable():
    return dir[cursor_line][7] != '' and (columns_visible[cursor_column] > 8 or columns_visible[cursor_column] == 1)

def enter():
    global current_dir, cursor_line, editing, view_position
    
    if editing:
        
        
        
        saveInfo()
        editing = False
    else:
        if dir[cursor_line][0] == 'DIR':
            if cursor_line == 0:
                current_dir = current_dir[:current_dir[:-1].rfind('/') + 1]
                if current_dir == '':
                    current_dir = '/'
            else:
                current_dir += dir[cursor_line][1] + '/'
            cursor_line = 0
            view_position = 0
        elif isCellEditable():
            pass
        elif any([dir[cursor_line][1].endswith(x, -6) for x in extensions]):
            play(path_prefix + current_dir + dir[cursor_line][1])
            
    
while True:
    cls() # tühjendab ekraani
    if message != '':
        print(message, end='')
        message = ''
    print(path_prefix + current_dir)
    
    # pealkirjad
    print(('  ' if columns_visible[cursor_column] == 0 else '') + '    ', end='')
    for col in columns_visible[1:]:
        print(('  ' if columns_visible[cursor_column] == col else '') +
            (columns[col] if len(columns[col]) < column_sizes[col] + 1 else columns[col][:column_sizes[col]-3]) +
            ('... ' if len(columns[col])-1 > column_sizes[col] else '' ) +
            ('\33[0m' if editing and cursor_line == i and cursor_column == col else '') + # värvimuutus tagasi
            ' '*(column_sizes[col] - len(columns[col]) + 1), end='')
    print()
    
    # andmete uuendamine
    if last_dir != current_dir or last_prefix != path_prefix:
        try:
            dir = [list_entry(Directory=('DIR' if file.is_dir else 'F  '),
                              Name=file.name,
                              Size=('' if file.is_dir else (metric_prefix(file.size) + 'B')),
                              Modified=datetimeToStr(file.modified),
                              Created=datetimeToStr(file.created)
                              ) for file in home_fs.scandir(current_dir, namespaces=['details'])]
            for i in range(len(dir)):
                file = dir[i]
                if file[0] != 'DIR':
                    try:
                        audio = mutagen.File(path_prefix + current_dir + file[1])
                    except mutagen.MutagenError:
                        continue
                    if audio != None:
                        if hasattr(audio.info, 'bitrate') and audio.info.bitrate: file[6] = metric_prefix(audio.info.bitrate) + 'bps'
                        if hasattr(audio.info, 'samplerate') and audio.info.samplerate: file[6] = str(audio.info.samplerate)
                        if hasattr(audio.info, 'length') and audio.info.length: file[8] = durationToStr(audio.info.length)
                        if isinstance(audio.tags, mutagen.id3.ID3):
                            audio = EasyID3(path_prefix + current_dir + file[1])
                            if audio == None:
                                continue
                        if 'title' in audio: file[9] = audio['title']
                        if 'artist' in audio: file[10] = audio['artist']
                        if 'album' in audio: file[11] = audio['album']
                        if 'albumartist' in audio: file[12] = audio['albumartist']
                        if 'contributingartists' in audio: file[13] = audio['contributingartists']
                        if 'tracknumber' in audio: file[14] = audio['tracknumber']
                        if 'date' in audio: file[15] = audio['date']
                        if 'genre' in audio: file[16] = audio['genre']
                        if 'composer' in audio: file[17] = audio['composer']
                        if 'writer' in audio: file[18] = audio['writer']
                        if 'key' in audio: file[19] = audio['key']
                        if 'bpm' in audio: file[20] = audio['bpm']
                        
                
        except (PermissionError, fs.errors.DirectoryExpected):
            message += 'Access denied.\n'
            current_dir = current_dir[:current_dir[:-1].rfind('/') + 1]
            if current_dir == '':
                    current_dir = '/'
            continue
            
        for i in range(len(dir)):
            for q in range(len(dir[i])):
                if isinstance(dir[i][q], list):
                    dir[i][q] = ', '.join(dir[i][q])
        
        if sorted_by < 2:
            dir.sort(key=lambda x: (x[0], x[1].lower()))
        else:
            dir.sort(key=lambda x: x[sorted_by].lower())
        dir.insert(0, list_entry(Directory='DIR', Name='..'))
    
    last_dir = current_dir
    last_prefix = path_prefix
    # ekraanil nähtavad read
    for i in range(view_position, min(view_position + view_lines, len(dir))):
        if cursor_line == i: print('\33[7m', end='')
        for col in columns_visible:
            print(((('> \33[6m' if editing else '> ') if cursor_line == i else '  ') if columns_visible[cursor_column] == col else '') +
                  (dir[i][col] if len(dir[i][col]) < column_sizes[col] + 1 else dir[i][col][:column_sizes[col]-3]) +
                  ('... ' if len(dir[i][col]) > column_sizes[col] else '' ) +
                  (('\33[7m' if cursor_line == i else '\33[0m') if editing and cursor_line == i and columns_visible[cursor_column] == col else '') + # värvimuutus tagasi
                  ' '*(column_sizes[col] - len(dir[i][col]) + 1), end='')
        print('\33[0m')
    
    # sisend
    ch = getch()
    special_ch = ch == b'\xe0'
    if special_ch:
        print(ch, end='')
        ch = getch()
    if ch:
        print(ch, end='')
        print()
        if ch == b'q':
            break
        elif ch in b_drives: # Kõvaketta vahetus
            home_fs = open_fs(ch.decode() + ':/')
            current_dir = '/'
            last_prefix = path_prefix
            path_prefix = ch.decode() + ':/'
            cursor_line = 0
            view_position = 0
        elif special_ch and ch == b'H':
            up()
        elif special_ch and ch == b'P':
            down()
        elif special_ch and ch == b'M':
            right()
        elif special_ch and ch == b'K':
            left()
        elif special_ch and ch == b'I':
            pgup()
        elif special_ch and ch == b'Q':
            pgdown()
        elif ch == b'+': # expand
            if columns_visible[cursor_column]+1 not in columns_visible and columns_visible[cursor_column]+1 < len(columns):
                columns_visible.insert(cursor_column+1, columns_visible[cursor_column]+1)
        elif ch == b'-': # hide
            if cursor_column > 1:
                columns_visible.pop(cursor_column)
                if cursor_column >= len(columns_visible):
                    cursor_column = len(columns_visible)-1
        elif ch == b'\x1b': # esc
            pass
        elif ch == b'\x08': # backspace
            current_dir = current_dir[:current_dir[:-1].rfind('/') + 1]
            if current_dir == '':
                    current_dir = '/'
            cursor_line = 0
            view_position = 0
        elif ch == b'\r':
            enter()
        message += 'Col='+str(cursor_column)+'; '+str(columns_visible)+'\n'








#from pynput import keyboard

# The key combination to check
#COMBINATIONS = [
#    {keyboard.Key.enter}
#]

# The currently active modifiers
#current = set()
#
#def execute(combination):
#    print ("Do Something")
#
#def on_press(key):
#    if any([key in COMBO for COMBO in COMBINATIONS]):
#        current.add(key)
#        if any(all(k in current for k in COMBO) for COMBO in COMBINATIONS):
#            execute(COMBO)
#
#def on_release(key):
#    if any([key in COMBO for COMBO in COMBINATIONS]):
#        current.remove(key)


#with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
#    listener.join()



