import os,zipfile,re,http.server,socketserver,threading,concurrent.futures as cf,img2pdf,subprocess,time,shutil
# from elevate import elevate
# elevate()
from PIL import Image,ImageOps
from colorama import init
init()
from colorama import Fore, Back, Style
os.system('cls')
logo= r"""
    ____      ____________                     ______            __  
   / __ \____/ / __/ ____/________  ________  / ____/___  __  __/ /_ 
  / /_/ / __  / /_/ /_  / ___/ __ \/ __  __ \/ __/ / __ \/ / / / __ \
 / ____/ /_/ / __/ __/ / /  / /_/ / / / / / / /___/ /_/ / /_/ / /_/ /
/_/    \____/_/ /_/   /_/   \____/_/ /_/ /_/_____/ .___/\____/_____/ 
                                                /_/         v1.3            
"""
logo = logo.replace("v1.3", f"{Fore.YELLOW}v1.3{Style.RESET_ALL}")
print(Fore.GREEN+logo)
time.sleep(1)
os.system('cls')
epub = input('Введите полный путь к EPUB файлу, с расширением: ')
while not epub.endswith(".epub") or epub.strip() == "":
    print("Неверный путь. Убедитесь, что он заканчивается на .epub")
    epub = input("Введите полный путь для сохранения EPUB файла, с расширением: ")


pdf = input("Введите полный путь для сохранения PDF файла, с расширением: ")
while not pdf.endswith(".pdf") or pdf.strip() == "":
    print("Неверный путь. Убедитесь, что он заканчивается на .pdf")
    pdf = input("Введите полный путь для сохранения PDF файла, с расширением: ")

wk = input('Введите полный путь к программе wkhtmltoimage (по умолчанию - C:\Program Files\wkhtmltopdf\\bin\wkhtmltoimage.exe): ')
if wk == '' or ' ' in wk:
    wk = 'C:\Progra~1\wkhtmltopdf\\bin\wkhtmltoimage.exe'

os.system('cls') # Очищаем экран

# Распаковка epub файла    
unzp = 'C:\epub'
jpg = 'C:\epub\jpg'
if os.path.exists(unzp):
    shutil.rmtree(unzp)
if not os.path.exists(unzp):
    os.makedirs(unzp)  
with zipfile.ZipFile(epub, 'r') as epub_zip:
    epub_zip.extractall(unzp)

# Поиск папки с xhtml и\или html файлами    
htmfolder = os.path.join(unzp, 'oebps')
if not os.path.exists(htmfolder):
    for root, dirs, files in os.walk(unzp):
        for dir in dirs:
            if dir.lower() == "oebps":
                htmfolder = os.path.join(root, dir)
                break
        if htmfolder:
            break

# Переход в папку oebps или оставаться в текущей
os.chdir(htmfolder)

# Переименовываем только страницы контента
content_files = [file_name for file_name in os.listdir(htmfolder) if file_name.lower() not in ('toc.html', 'toc.xhtml') and file_name.lower().endswith(('.html', '.xhtml'))]

# Определение функции для сортировки по числовой части имени
def sort_by_number(file_name):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', file_name)]

content_files.sort(key=sort_by_number)  # Сортируем файлы по числовой части имени

c = 1
for file_name in content_files:
    if file_name.lower().endswith('.xhtml'):
        new_extension = '.html'  # Меняем расширение на .html, если изначально .xhtml
    else:
        new_extension = '.html'  # Оставляем расширение .html
    new_name = f"{c}{new_extension}" 
    old_jpg = os.path.join(htmfolder, file_name)
    new_jpg = os.path.join(htmfolder, new_name)
    os.rename(old_jpg, new_jpg)
    c += 1

htmcount = c - 1  # Вычисляем количество переименованных файлов

if not os.path.exists(jpg):
    os.makedirs(jpg)

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/":  # Обрабатываем корневой запрос
                self.path = self.find_index_file()

            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        except Exception as e:
            self.send_error(404, f"File not found: {e}")

    @staticmethod
    def has_number(s):
        return any(char.isdigit() for char in s)

    def find_index_file(self):
        pattern = re.compile(r"1.html")
        for filename in os.listdir(self.directory):
            if re.match(pattern, filename):
                return "/" + filename

        return "/404.html"  # Вернуть страницу 404, если не найдено ни одного подходящего файла


Handler = CustomHTTPRequestHandler

httpd = socketserver.TCPServer(("localhost", 8000), Handler)
server_thread = threading.Thread(target=httpd.serve_forever)  # Создать поток для запуска сервера
server_thread.daemon = True  # Сделать поток демоническим, чтобы он завершился при завершении основного потока
server_thread.start()  # Запуск сервера в фоновом режиме
print(f"Запускаю локальный сервер.")
print(f'Начинаю конвертацию в JPG.')
for i in range(1, htmcount + 1):
    command = f"{wk} --zoom 2.5 --log-level none localhost:8000/{i}.html {jpg}/{i}.jpg"
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
    process.wait()  # Добавьте вызов метода wait()
    print(f'Конвертировано в JPG страниц: {i} из {htmcount}.')
    if i==htmcount:
        httpd.shutdown()
        httpd.server_close()
        print('Все страницы конвертированы в JPG.')

# Останавливаем сервер после создания всех изображений:
httpd.shutdown()
httpd.server_close()
a=0
os.system(f'explorer.exe {jpg}')

while a not in [1, 2, 3]:
    a = int(input('Обрезать изображения?\n       1. Ввести ширину и высоту\n       2. Обрезать пополам, сохранить оба изображения\n       3. Нет\n       Ваш выбор: '))

if a==1:
    a,b=list(map(int, input('Введите ширину и высоту через пробел: ').split()))
    files = os.listdir(jpg)

    def extract_number(file_name):
        number = ''.join(filter(str.isdigit, file_name))
        return (int(number) if number else -1, file_name)
    sorted_files = sorted(files, key=extract_number)
    for file_name in sorted_files:
        image_jpg = os.path.join(jpg, file_name)
        image = Image.open(image_jpg)
        jpgped_image = image.jpg((0, 0, a, b))
        jpgped_image.save(image_jpg)
elif a==2:
    def extract_number(file_name):
        number = ''.join(filter(str.isdigit, file_name))
        return int(number) if number else -1
    os.makedirs(jpg, exist_ok=True)
    imglist = [f for f in os.listdir(jpg) if f.endswith('.jpg')]
    sorted_imglist = sorted(imglist, key=lambda f: extract_number(os.path.basename(f)))
    counter = 1
    for i, filename in enumerate(sorted_imglist):
        img = Image.open(os.path.join(jpg, filename))
        width, height = img.size
        mid = width // 2
        left_half = img.crop((0, 0, mid, height))
        right_half = img.crop((mid, 0, width, height))

        base_filename, ext = os.path.splitext(filename)
        left_filename = f"{base_filename}{ext}"
        right_filename = f"{base_filename}_R{ext}"

        left_half.save(os.path.join(jpg, left_filename))
        right_half.save(os.path.join(jpg, right_filename))

elif a==3:
    pass

def extract_number(file_name):
    number = ''.join(filter(str.isdigit, file_name))
    return int(number) if number else -1

imglist = [os.path.join(jpg, f) for f in os.listdir(jpg) if f.endswith('.jpg')]
imglist = sorted(imglist, key=lambda f: extract_number(os.path.basename(f)))
opened_images = [open(image, 'rb') for image in imglist]
with open(pdf, 'wb') as f:
    f.write(img2pdf.convert(opened_images))
for image in opened_images:
    image.close()

print(f"Ваш PDF-файл готов: {pdf}")
os.system(f'explorer.exe /select,"{pdf}"')