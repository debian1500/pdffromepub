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
   / __ \____/ / __/ ____/________  ____ ___  / ____/___  __  __/ /_ 
  / /_/ / __  / /_/ /_  / ___/ __ \/ __ `__ \/ __/ / __ \/ / / / __ \
 / ____/ /_/ / __/ __/ / /  / /_/ / / / / / / /___/ /_/ / /_/ / /_/ /
/_/    \__,_/_/ /_/   /_/   \____/_/ /_/ /_/_____/ .___/\__,_/_.___/ 
                                                /_/         v1.1            
"""
logo = logo.replace("v1.1", f"{Fore.YELLOW}v1.1{Style.RESET_ALL}")
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
oebps_path = os.path.join(unzp, 'oebps')
if not os.path.exists(oebps_path):
    for root, dirs, files in os.walk(unzp):
        for dir in dirs:
            if dir.lower() == "oebps":
                oebps_path = os.path.join(root, dir)
                break
        if oebps_path:
            break

# Переход в папку oebps или оставаться в текущей
os.chdir(oebps_path)

# Переименовываем только страницы контента
content_files = [file_name for file_name in os.listdir(oebps_path) if file_name.lower() not in ('toc.html', 'toc.xhtml') and file_name.lower().endswith(('.html', '.xhtml'))]

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
    old_path = os.path.join(oebps_path, file_name)
    new_path = os.path.join(oebps_path, new_name)
    os.rename(old_path, new_path)
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
        image_path = os.path.join(jpg, file_name)
        image = Image.open(image_path)
        cropped_image = image.crop((0, 0, a, b))
        cropped_image.save(image_path)
elif a==2:
    counter = 1

    for file_name in os.listdir(jpg):
        if file_name.endswith(".jpg"):
            image = Image.open(os.path.join(jpg, file_name))
            width, height = image.size
            left_half = image.crop((0, 0, width//2, height))
            right_half = image.crop((width//2, 0, width, height))
            left_half.save(os.path.join(jpg, str(counter) + ".jpg"))
            right_half.save(os.path.join(jpg, str(counter+1) + ".jpg"))
            counter += 2
            image.close()        
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