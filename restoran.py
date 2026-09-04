import html
from datetime import datetime
from functools import wraps
import requests
from flask import Flask, jsonify, render_template, request, Response, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
# Session şifrələməsi üçün məxfi açar
app.secret_key = "Qrenki2026_Super_Secret_Session_Key"

# NFC çiplərinə yazılacaq gizli təhlükəsizlik kodu
NFC_SECRET_TOKEN = "QRENKI_2026_SECURE"

# ==========================================
# 1. TƏHLÜKƏSİZLİK VƏ ŞİFRƏLƏMƏ TƏNZİMLƏMƏLƏRİ
# ==========================================
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Qrenki2026!"


def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def authenticate():
    return Response(
        'Giriş üçün admin məlumatlarını daxil edin.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


# Rate Limiting (Spam sifarişlərin və zərərli sorğuların qarşısını almaq üçün)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per day", "100 per hour"],
    storage_uri="memory://"
)

# ==========================================
# TELEGRAM BOT TƏNZİMLƏMƏLƏRİ
# ==========================================
TELEGRAM_BOT_TOKEN = "8874314422:AAGAzZCSyM7-tvZJkvpQIOxcD82mPflIAlI"
TELEGRAM_CHAT_ID = "5599765464"


def send_telegram_notification(message):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Telegram xətası: {e}")


# ==========================================
# BAZA (MENYU, SİFARİŞLƏR VƏ SİSTEM VƏZİYYƏTİ)
# ==========================================
SYSTEM_ACTIVE = True
ORDERS = []

MENU = {
    "PİVƏ QƏLYANALTILARI": [
        {"id": 1, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qrenki Sadə", "ru": "Гренки простые", "en": "Plain Garlic Bread"}, "qiymət": 5.0, "təsvir": ""},
        {"id": 2, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qrenki Pendir və Sous ilə", "ru": "Гренки с сыром и соусом", "en": "Garlic Bread with Cheese & Sauce"}, "qiymət": 7.5, "təsvir": ""},
        {"id": 3, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qrenki Şprot ilə", "ru": "Гренки со шпротами", "en": "Garlic Bread with Sprats"}, "qiymət": 6.9, "təsvir": ""},
        {"id": 4, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qrenki Cheese Sousu ilə", "ru": "Гренки с соусом Чиз", "en": "Garlic Bread with Cheese Sauce"}, "qiymət": 9.3, "təsvir": ""},
        {"id": 5, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qrenki Özel Turşu", "ru": "Гренки Особые соления", "en": "Special Pickled Garlic Bread"}, "qiymət": 4.7, "təsvir": ""},
        {"id": 6, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Noxud Sadə", "ru": "Нут простой", "en": "Plain Chickpeas"}, "qiymət": 3.4, "təsvir": ""},
        {"id": 7, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Noxud Suxarıda", "ru": "Нут в сухарях", "en": "Crispy Breaded Chickpeas"}, "qiymət": 4.9, "təsvir": ""},
        {"id": 8, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Edamame", "ru": "Эдамаме", "en": "Edamame"}, "qiymət": 7.0, "təsvir": ""},
        {"id": 9, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Püstə", "ru": "Фисташки", "en": "Pistachios"}, "qiymət": 8.5, "təsvir": ""},
        {"id": 10, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Toyuq BBQ", "ru": "Курица BBQ", "en": "BBQ Chicken"}, "qiymət": 7.8, "təsvir": ""},
        {"id": 11, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Günəbaxan Tumu", "ru": "Семечки подсолнуха", "en": "Sunflower Seeds"}, "qiymət": 3.9, "təsvir": ""},
        {"id": 12, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Çipsi (Lays)", "ru": "Чипсы (Lays)", "en": "Crisps (Lays)"}, "qiymət": 4.4, "təsvir": ""},
        {"id": 13, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Makaron Çipsi", "ru": "Макаронные чипсы", "en": "Pasta Chips"}, "qiymət": 2.8, "təsvir": ""},
        {"id": 14, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Kolbasa Çipsi", "ru": "Колбасные чипсы", "en": "Salami Chips"}, "qiymət": 7.1, "təsvir": ""},
        {"id": 15, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Saçaq Pendiri Sadə", "ru": "Сыр чечил простой", "en": "String Cheese Plain"}, "qiymət": 4.7, "təsvir": ""},
        {"id": 16, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Saçaq Pendiri Qızartma", "ru": "Сыр чечил жареный", "en": "Fried String Cheese"}, "qiymət": 4.9, "təsvir": ""},
        {"id": 17, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Fimi Saçaq Pendiri ilə", "ru": "Фими с сыром чечил", "en": "Fimi with String Cheese"}, "qiymət": 5.6, "təsvir": ""},
        {"id": 18, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Fimi Çipsi ilə", "ru": "Фими с чипсами", "en": "Fimi with Chips"}, "qiymət": 6.1, "təsvir": ""},
        {"id": 19, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Donuz Qabırğaları BBQ", "ru": "Свиные ребрышки BBQ", "en": "BBQ Pork Ribs"}, "qiymət": 10.7, "təsvir": ""},
        {"id": 20, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Naços Pendir ilə", "ru": "Начос с сыром", "en": "Nachos with Cheese"}, "qiymət": 12.7, "təsvir": ""},
        {"id": 21, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Naços Toyuq Əti ilə", "ru": "Начос с курицей", "en": "Nachos with Chicken"}, "qiymət": 16.5, "təsvir": ""},
        {"id": 22, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Soğan Həlqələri", "ru": "Луковые кольца", "en": "Onion Rings"}, "qiymət": 5.0, "təsvir": ""},
        {"id": 23, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qovrulmuş Göbələk Papaqları", "ru": "Жареные шляпки грибов", "en": "Roasted Mushroom Caps"}, "qiymət": 6.8, "təsvir": ""},
        {"id": 24, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Toyuq Boğazları", "ru": "Копченые куриные шейки", "en": "Smoked Chicken Necks"}, "qiymət": 4.6, "təsvir": ""},
        {"id": 25, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq Boğazları (Acılı/Sadə)", "ru": "Куриные шейки (Острые/Простые)", "en": "Chicken Necks (Spicy/Plain)"}, "qiymət": 4.9, "təsvir": ""},
        {"id": 26, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq Pətənəkləri", "ru": "Куриные пупки", "en": "Chicken Gizzards"}, "qiymət": 5.9, "təsvir": ""},
        {"id": 27, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qızardılmış Toyuq Ürəyi", "ru": "Жареные куриные сердечки", "en": "Fried Chicken Hearts"}, "qiymət": 6.4, "təsvir": ""},
        {"id": 28, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq Popkorn", "ru": "Куриный попкорн", "en": "Chicken Popcorn"}, "qiymət": 7.1, "təsvir": ""},
        {"id": 29, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Bildirçin", "ru": "Копченый перепел", "en": "Smoked Quail"}, "qiymət": 7.5, "təsvir": ""},
        {"id": 30, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qurudulmuş Ət", "ru": "Сушеное мясо (Джерки)", "en": "Jerky / Dried Meat"}, "qiymət": 7.9, "təsvir": ""},
        {"id": 31, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Duzlu Qara Ciyər", "ru": "Соленая печень", "en": "Salted Liver"}, "qiymət": 5.9, "təsvir": ""},
        {"id": 32, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Göbələk Çipsləri", "ru": "Грибные чипсы", "en": "Mushroom Chips"}, "qiymət": 5.8, "təsvir": ""},
        {"id": 33, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Qızardılmış Suluquni", "ru": "Жареный сулугуни", "en": "Fried Sulguni Cheese"}, "qiymət": 8.7, "təsvir": ""},
        {"id": 34, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Quşbaşı-Pendir Qızartması", "ru": "Жареный сыр с кубиками мяса", "en": "Diced Meat & Cheese Fry"}, "qiymət": 6.4, "təsvir": ""},
        {"id": 35, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq Qanadları BBQ", "ru": "Куриные крылышки BBQ", "en": "BBQ Chicken Wings"}, "qiymət": 6.9, "təsvir": ""},
        {"id": 36, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq Zoğal Turşusunda", "ru": "Курица в кизиловом соусе", "en": "Chicken in Cornelian Cherry Sauce"}, "qiymət": 7.1, "təsvir": ""},
        {"id": 37, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Dəniz Krevetləri", "ru": "Морские креветки", "en": "Sea Shrimps"}, "qiymət": 14.9, "təsvir": ""},
        {"id": 38, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Çay Krevetləri", "ru": "Речные креветки", "en": "River Shrimps"}, "qiymət": 14.9, "təsvir": ""},
        {"id": 39, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Krevetka Suxarıda", "ru": "Креветки в панировке", "en": "Crispy Breaded Shrimps"}, "qiymət": 16.6, "təsvir": ""},
        {"id": 40, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Kalmar Həlqələri", "ru": "Кольца кальмара", "en": "Squid Rings"}, "qiymət": 7.7, "təsvir": ""},
        {"id": 41, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Dorado", "ru": "Копченая дорадо", "en": "Smoked Dorado"}, "qiymət": 19.7, "təsvir": ""},
        {"id": 42, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Forel", "ru": "Копченая форель", "en": "Smoked Trout"}, "qiymət": 12.6, "təsvir": ""},
        {"id": 43, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Şamayka", "ru": "Копченая шамая", "en": "Smoked Shemaya Fish"}, "qiymət": 5.7, "təsvir": ""},
        {"id": 44, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Hisə Verilmiş Kilkə", "ru": "Копченая килька", "en": "Smoked Sprat"}, "qiymət": 3.9, "təsvir": ""},
        {"id": 45, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Hamsi Balığı", "ru": "Хамса", "en": "Anchovy Fish"}, "qiymət": 10.3, "təsvir": ""},
        {"id": 46, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Siyənək Soyutma Kartof ilə", "ru": "Сельдь с отварным картофелем", "en": "Herring with Boiled Potatoes"}, "qiymət": 9.0, "təsvir": ""},
        {"id": 47, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Düşbərə Qızartma", "ru": "Жареная дюшбара", "en": "Fried Dushbara (Dumplings)"}, "qiymət": 5.1, "təsvir": ""},
        {"id": 48, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Krevetka Popkorn", "ru": "Попкорн из креветок", "en": "Shrimp Popcorn"}, "qiymət": 13.7, "təsvir": ""},
        {"id": 49, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Toyuq 'Cersi'", "ru": "Курица 'Джерси'", "en": "Chicken 'Jersey'"}, "qiymət": 9.3, "təsvir": ""},
        {"id": 50, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"}, "adı": {
            "az": "Sosiska Konfet", "ru": "Сосиски 'Конфеты'", "en": "Mini Candy Sausages"}, "qiymət": 7.6, "təsvir": ""},
        {"id": 51, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Toyuq Çipsi", "ru": "Куриные чипсы", "en": "Chicken Chips"}, "qiymət": 6.2, "təsvir": ""},
        {"id": 52, "category_translated": {"az": "PİVƏ QƏLYANALTILARI", "ru": "ЗАКУСКИ К ПИВУ", "en": "BEER SNACKS"},
            "adı": {"az": "Aydaho Çipsi", "ru": "Чипсы Айдахо", "en": "Idaho Chips"}, "qiymət": 6.3, "təsvir": ""},
    ],
    "SOYUQ QƏLYANALTILAR VƏ SALATLAR": [
        {"id": 53, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Pendir Çeşidləri", "ru": "Сырное ассорти", "en": "Cheese Platter"}, "qiymət": 9.2, "təsvir": ""},
        {"id": 54, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Turşu Çeşidləri", "ru": "Соленья ассорти", "en": "Pickle Platter"}, "qiymət": 7.1, "təsvir": ""},
        {"id": 55, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Zeytun", "ru": "Оливки", "en": "Olives"}, "qiymət": 3.6, "təsvir": ""},
        {"id": 56, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Ağ Pendir", "ru": "Белый сыр", "en": "White Cheese"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 57, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Motal Pendiri", "ru": "Сыр Мотал", "en": "Motal Cheese"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 58, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Tərəvəz Buketi", "ru": "Овощной букет", "en": "Fresh Vegetable Platter"}, "qiymət": 5.9, "təsvir": ""},
        {"id": 59, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Ton Balıq Salatı", "ru": "Салат с тунцом", "en": "Tuna Salad"}, "qiymət": 12.5, "təsvir": ""},
        {"id": 60, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Sezar Salatı Toyuq ilə", "ru": "Цезарь с курицей", "en": "Chicken Caesar Salad"}, "qiymət": 11.6, "təsvir": ""},
        {"id": 61, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Sezar Salatı Krevet ilə", "ru": "Цезарь с креветками", "en": "Shrimp Caesar Salad"}, "qiymət": 17.9, "təsvir": ""},
        {"id": 62, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Badımcan-Pomidor Salatı", "ru": "Салат из баклажанов и томатов", "en": "Eggplant & Tomato Salad"}, "qiymət": 8.7, "təsvir": ""},
        {"id": 63, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Çoban Salatı", "ru": "Салат Чобан", "en": "Choban (Shepherd) Salad"}, "qiymət": 6.9, "təsvir": ""},
        {"id": 64, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"}, "adı": {
            "az": "Nar Salatı Can Əti ilə", "ru": "Салат с гранатом и вырезкой", "en": "Pomegranate Salad with Tenderloin"}, "qiymət": 14.0, "təsvir": ""},
        {"id": 65, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Şəfin Xüsusi Salatı", "ru": "Фирменный салат от Шефа", "en": "Chef's Special Salad"}, "qiymət": 17.3, "təsvir": ""},
        {"id": 66, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"}, "adı": {
            "az": "Albalı Sousunda Pomidor Salatı", "ru": "Салат из томатов в вишневом соусе", "en": "Tomato Salad in Cherry Sauce"}, "qiymət": 9.3, "təsvir": ""},
        {"id": 67, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Russkiy Set", "ru": "Русский Сет", "en": "Russian Set"}, "qiymət": 39.0, "təsvir": ""},
        {"id": 68, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Ət Salatı", "ru": "Мясной салат", "en": "Meat Salad"}, "qiymət": 19.1, "təsvir": ""},
        {"id": 69, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Gavurdağ Salatı", "ru": "Салат Гавурдаг", "en": "Gavurdagi Salad"}, "qiymət": 5.6, "təsvir": ""},
        {"id": 70, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Brusketta Rostbiflə", "ru": "Брускетта с ростбифом", "en": "Roast Beef Bruschetta"}, "qiymət": 15.7, "təsvir": ""},
        {"id": 71, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Brusketta Qızılbalıq ilə", "ru": "Брускетта с семгой", "en": "Salmon Bruschetta"}, "qiymət": 18.1, "təsvir": ""},
        {"id": 72, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ", "en": "COLD APPETIZERS & SALADS"},
            "adı": {"az": "Brusketta Siyənək ilə", "ru": "Брускетта со сельдью", "en": "Herring Bruschetta"}, "qiymət": 7.1, "təsvir": ""},
        {"id": 73, "category_translated": {"az": "SOYUQ QƏLYANALTILAR VƏ SALATLAR", "ru": "ХОЛОДНЫЕ ЗАКУСКИ И САЛАТЫ",
                                           "en": "COLD APPETIZERS & SALADS"}, "adı": {"az": "Humus", "ru": "Хумус", "en": "Hummus"}, "qiymət": 6.4, "təsvir": ""},
    ],
    "ŞORBALAR": [
        {"id": 74, "category_translated": {"az": "ŞORBALAR", "ru": "СУПЫ", "en": "SOUPS"}, "adı": {
            "az": "Borş Mal Əti", "ru": "Борщ с говядиной", "en": "Beef Borscht"}, "qiymət": 12.5, "təsvir": ""},
        {"id": 75, "category_translated": {"az": "ŞORBALAR", "ru": "СУПЫ", "en": "SOUPS"}, "adı": {
            "az": "Xarço", "ru": "Харчо", "en": "Kharcho Soup"}, "qiymət": 8.1, "təsvir": ""},
        {"id": 76, "category_translated": {"az": "ŞORBALAR", "ru": "СУПЫ", "en": "SOUPS"}, "adı": {
            "az": "Toyuq Şorbası", "ru": "Куриный суп", "en": "Chicken Soup"}, "qiymət": 7.2, "təsvir": ""},
        {"id": 77, "category_translated": {"az": "ŞORBALAR", "ru": "СУПЫ", "en": "SOUPS"}, "adı": {
            "az": "Düşbərə", "ru": "Дюшбара", "en": "Dushbara Soup"}, "qiymət": 7.2, "təsvir": ""},
    ],
    "SOSİSLƏR VƏ KOLBASALAR": [
        {"id": 78, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"},
            "adı": {"az": "Sardelka", "ru": "Сарделька", "en": "Sardelka Sausage"}, "qiymət": 7.2, "təsvir": ""},
        {"id": 79, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "İveriya Sosisləri", "ru": "Сосиски Иверия", "en": "Iveria Sausages"}, "qiymət": 6.0, "təsvir": ""},
        {"id": 80, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"},
            "adı": {"az": "Südlü Sosis", "ru": "Молочные сосиски", "en": "Milk Sausages"}, "qiymət": 6.0, "təsvir": ""},
        {"id": 81, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"},
            "adı": {"az": "Közləmə Sosis", "ru": "Сосиски на углях", "en": "Grilled Sausages"}, "qiymət": 6.0, "təsvir": ""},
        {"id": 82, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "Vinçester Sosisi", "ru": "Сосиска Винчестер", "en": "Winchester Sausage"}, "qiymət": 11.6, "təsvir": ""},
        {"id": 83, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "Ovçu Kolbasası Qızardılmış", "ru": "Охотничьи колбаски жареные", "en": "Fried Hunting Sausages"}, "qiymət": 6.1, "təsvir": ""},
        {"id": 84, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "Krakov Kolbasası Pomidor Sousu ilə", "ru": "Краковская колбаса в томатном соусе", "en": "Krakow Sausage in Tomato Sauce"}, "qiymət": 10.9, "təsvir": ""},
        {"id": 85, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "Krakov Kolbasası Pendirli", "ru": "Краковская колбаса с сыром", "en": "Krakow Sausage with Cheese"}, "qiymət": 12.5, "təsvir": ""},
        {"id": 86, "category_translated": {"az": "SOSİSLƏR VƏ KOLBASALAR", "ru": "СОСИСКИ И КОЛБАСЫ", "en": "SAUSAGES"}, "adı": {
            "az": "Sosis Çeşidləri", "ru": "Сосисочное ассорти", "en": "Assorted Sausages Platter"}, "qiymət": 25.7, "təsvir": ""},
    ],
    "FAST FOOD": [
        {"id": 87, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Toyuq Nagetləri", "ru": "Куриные наггетсы", "en": "Chicken Nuggets"}, "qiymət": 7.2, "təsvir": ""},
        {"id": 88, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Mozzarella Çubuqları", "ru": "Палочки моцарелла", "en": "Mozzarella Sticks"}, "qiymət": 6.4, "təsvir": ""},
        {"id": 89, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Çizburger", "ru": "Чизбургер", "en": "Cheeseburger"}, "qiymət": 11.6, "təsvir": ""},
        {"id": 90, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Klab Sendviç", "ru": "Клаб сэндвич", "en": "Club Sandwich"}, "qiymət": 9.8, "təsvir": ""},
        {"id": 91, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Meksika Sayağı Roll", "ru": "Ролл по-мексикански", "en": "Mexican Style Roll"}, "qiymət": 10.3, "təsvir": ""},
        {"id": 92, "category_translated": {"az": "FAST FOOD", "ru": "ФАСТ ФУД", "en": "FAST FOOD"}, "adı": {
            "az": "Toyuqlu Roll", "ru": "Ролл с курицей", "en": "Chicken Roll"}, "qiymət": 10.2, "təsvir": ""},
    ],
    "QARNİRLƏR": [
        {"id": 93, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {"az": "Kənd Sayağı Kartof Tavada",
                                                                                                             "ru": "Картофель по-деревенски на сковороде", "en": "Home-style Skillet Potatoes"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 94, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {
            "az": "Tərəvəz Qrildə", "ru": "Овощи на гриле", "en": "Grilled Vegetables"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 95, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {
            "az": "Soyutma Kartof", "ru": "Отварной картофель", "en": "Boiled Potatoes"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 96, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {
            "az": "Püre", "ru": "Картофельное пюре", "en": "Mashed Potatoes"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 97, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"},
            "adı": {"az": "Düyü", "ru": "Рис", "en": "Rice"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 98, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {
            "az": "Kartof Fri", "ru": "Картофель фри", "en": "French Fries"}, "qiymət": 4.1, "təsvir": ""},
        {"id": 99, "category_translated": {"az": "QARNİRLƏR", "ru": "ГАРНИРЫ", "en": "SIDE DISHES"}, "adı": {
            "az": "Tərəvəzli Sote", "ru": "Овощное соте", "en": "Sautéed Vegetables"}, "qiymət": 10.0, "təsvir": ""},
    ],
    "BUYNUZLU LƏZZƏTLƏR": [
        {"id": 100, "category_translated": {"az": "BUYNUZLU LƏZZƏTLƏR", "ru": "БЛЮДА ИЗ ОЛЕНИНЫ", "en": "VENISON DISHES"}, "adı": {
            "az": "Maral Ətindən Küftələr", "ru": "Тефтели из оленины", "en": "Venison Meatballs"}, "qiymət": 24.5, "təsvir": ""},
        {"id": 101, "category_translated": {"az": "BUYNUZLU LƏZZƏTLƏR", "ru": "БЛЮДА ИЗ ОЛЕНИНЫ", "en": "VENISON DISHES"}, "adı": {
            "az": "Maral Əti Xüsusi Sousda", "ru": "Оленина в особом соусе", "en": "Venison in Special Sauce"}, "qiymət": 32.3, "təsvir": ""},
        {"id": 102, "category_translated": {"az": "BUYNUZLU LƏZZƏTLƏR", "ru": "БЛЮДА ИЗ ОЛЕНИНЫ", "en": "VENISON DISHES"}, "adı": {
            "az": "Maral Ətindən Krakov Sayağı Kolbasa", "ru": "Колбаса из оленины по-краковски", "en": "Krakow-style Venison Sausage"}, "qiymət": 17.4, "təsvir": ""},
    ],
    "ƏSAS YEMƏKLƏR": [
        {"id": 103, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Forel (Tavada)", "ru": "Форель (на сковороде)", "en": "Pan-fried Trout"}, "qiymət": 18.2, "təsvir": ""},
        {"id": 104, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Medalyon Steyk", "ru": "Стейк Медальон", "en": "Medallion Steak"}, "qiymət": 24.8, "təsvir": ""},
        {"id": 105, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Çolpa Limonlu Sousda", "ru": "Цыпленок в лимонном соусе", "en": "Chicken in Lemon Sauce"}, "qiymət": 20.1, "təsvir": ""},
        {"id": 106, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Can Ətindən Nar Qovurma", "ru": "Нар Говурма из вырезки", "en": "Tenderloin Roasted with Pomegranate"}, "qiymət": 24.7, "təsvir": ""},
        {"id": 107, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Ev Sayağı Ət Tuşonkası", "ru": "Домашняя тушенка", "en": "Homemade Stewed Beef"}, "qiymət": 17.4, "təsvir": ""},
        {"id": 108, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Beef Stroganoff Can Əti ilə", "ru": "Бефстроганов из вырезки", "en": "Beef Stroganoff"}, "qiymət": 20.8, "təsvir": ""},
        {"id": 109, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Bakı Qovurması Can Əti ilə", "ru": "Бакинская говурма из вырезки", "en": "Baku Style Tenderloin Fry"}, "qiymət": 20.6, "təsvir": ""},
        {"id": 110, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Faxitos Can Əti ilə", "ru": "Фахитос с вырезкой", "en": "Tenderloin Fajitas"}, "qiymət": 20.5, "təsvir": ""},
        {"id": 111, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Monastr Sayağı Can Əti", "ru": "Мясо по-монастырски", "en": "Monastery Style Beef"}, "qiymət": 19.7, "təsvir": ""},
        {"id": 112, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Monastr Sayağı Toyuq", "ru": "Курица по-монастырски", "en": "Monastery Style Chicken"}, "qiymət": 13.1, "təsvir": ""},
        {"id": 113, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Steyk Xüsusi Qarnir ilə", "ru": "Стейк с особым гарниром", "en": "Steak with Special Side Dish"}, "qiymət": 27.7, "təsvir": ""},
        {"id": 114, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Çolpa Albalı ilə", "ru": "Цыпленок с вишней", "en": "Chicken with Cherry"}, "qiymət": 25.9, "təsvir": ""},
        {"id": 115, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {"az": "Can Əti İspanaq və Qaymaqlı Sousda",
                                                                                                                         "ru": "Вырезка со шпинатом в сливочном соусе", "en": "Tenderloin in Spinach & Cream Sauce"}, "qiymət": 25.1, "təsvir": ""},
        {"id": 116, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Çolpa Çığırtması", "ru": "Чигиртма из цыпленка", "en": "Chicken Chigirtma"}, "qiymət": 22.6, "təsvir": ""},
        {"id": 117, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Çoban Qovurması Can Əti ilə", "ru": "Чобан говурма из вырезки", "en": "Shepherd's Roast Beef"}, "qiymət": 23.3, "təsvir": ""},
        {"id": 118, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"},
            "adı": {"az": "Ət Langeti", "ru": "Лангет из мяса", "en": "Beef Languet"}, "qiymət": 17.9, "təsvir": ""},
        {"id": 119, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Tabaka Ev Sayağı Kartof ilə", "ru": "Табака с домашним картофелем", "en": "Chicken Tabaka with Homemade Potatoes"}, "qiymət": 21.5, "təsvir": ""},
        {"id": 120, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Qaymaqlı Toyuq", "ru": "Курица в сливочном соусе", "en": "Creamy Chicken"}, "qiymət": 14.9, "təsvir": ""},
        {"id": 121, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Toyuq Langeti", "ru": "Куриный лангет", "en": "Chicken Languet"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 122, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Toyuq Şnitzeli", "ru": "Куриный шницель", "en": "Chicken Schnitzel"}, "qiymət": 8.0, "təsvir": ""},
        {"id": 123, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Pomidor-Yumurta", "ru": "Помидор-юмурта", "en": "Tomato & Eggs"}, "qiymət": 6.6, "təsvir": ""},
        {"id": 124, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Şah Qovurma Can Əti ilə", "ru": "Шах Говурма из вырезки", "en": "Shah Govurma Beef"}, "qiymət": 26.8, "təsvir": ""},
        {"id": 125, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Krevetlər Sarımsaqlı Sousda", "ru": "Креветки в чесночном соусе", "en": "Garlic Butter Shrimps"}, "qiymət": 19.7, "təsvir": ""},
        {"id": 126, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Meksika Sayağı Can Əti", "ru": "Мясо по-мексикански", "en": "Mexican Style Beef"}, "qiymət": 20.0, "təsvir": ""},
        {"id": 127, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Sümüksüz Çolpa Xüsusi Sousda", "ru": "Цыпленок без костей в особом соусе", "en": "Boneless Chicken in Special Sauce"}, "qiymət": 18.6, "təsvir": ""},
        {"id": 128, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Medalyon Albalı Sousunda", "ru": "Медальоны в вишневом соусе", "en": "Medallions in Cherry Sauce"}, "qiymət": 26.8, "təsvir": ""},
        {"id": 129, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Qaymaqlı Qızılbalıq", "ru": "Семга в сливочном соусе", "en": "Salmon in Cream Sauce"}, "qiymət": 33.6, "təsvir": ""},
        {"id": 130, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"},
            "adı": {"az": "Şirəli Dana", "ru": "Сочная телятина", "en": "Juicy Veal"}, "qiymət": 18.7, "təsvir": ""},
        {"id": 131, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Quzu Qolu Sobada (Sifariş ilə)", "ru": "Запеченная баранья лопатка (по предзаказу)", "en": "Baked Lamb Shoulder (Pre-order)"}, "qiymət": 94.2, "təsvir": ""},
        {"id": 132, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Tava Kababı", "ru": "Тава кебаб", "en": "Tava Kebab"}, "qiymət": 13.1, "təsvir": ""},
        {"id": 133, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Qızılbalıq Sırdağı", "ru": "Сырдаг из семги", "en": "Salmon Syrdag"}, "qiymət": 30.3, "təsvir": ""},
        {"id": 134, "category_translated": {"az": "ƏSAS YEMƏKLƏR", "ru": "ГОPЯЧИЕ БЛЮДА", "en": "MAIN COURSES"}, "adı": {
            "az": "Dəniz Məhsulları Şərab Sousunda", "ru": "Морепродукты в винном соусе", "en": "Seafood in Wine Sauce"}, "qiymət": 33.6, "təsvir": ""},
    ],
    "PİVƏ": [
        {"id": 135, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Carlsberg Zero 450ml", "ru": "Carlsberg Zero 450мл", "en": "Carlsberg Zero 450ml"}, "qiymət": 6.0, "təsvir": ""},
        {"id": 136, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Xırdalan Zero 450ml", "ru": "Xırdalan Zero 450мл", "en": "Xirdalan Zero 450ml"}, "qiymət": 5.4, "təsvir": ""},
        {"id": 137, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {"az": "Xırdalan Buğda Zero 450ml",
                                                                                               "ru": "Xırdalan Buğda Zero 450мл", "en": "Xirdalan Wheat Zero 450ml"}, "qiymət": 5.4, "təsvir": ""},
        {"id": 138, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Efes Zero 330ml", "ru": "Efes Zero 330мл", "en": "Efes Zero 330ml"}, "qiymət": 5.4, "təsvir": ""},
        {"id": 139, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Corona 330ml", "ru": "Corona 330мл", "en": "Corona 330ml"}, "qiymət": 9.9, "təsvir": ""},
        {"id": 140, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Miller 330ml", "ru": "Miller 330мл", "en": "Miller 330ml"}, "qiymət": 8.7, "təsvir": ""},
        {"id": 141, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Erdinger Qara 500ml", "ru": "Erdinger Темное 500мл", "en": "Erdinger Dark 500ml"}, "qiymət": 10.3, "təsvir": ""},
        {"id": 142, "category_translated": {"az": "PİVƏ", "ru": "ПИВО", "en": "BEER"}, "adı": {
            "az": "Erdinger Zero 330ml", "ru": "Erdinger Zero 330мл", "en": "Erdinger Zero 330ml"}, "qiymət": 7.0, "təsvir": ""},
    ],
    "ÇƏLLƏK PİVƏ": [
        {"id": 143, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Grimbergen", "ru": "Grimbergen", "en": "Grimbergen"},
            "təsvir": "", "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 4.2}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 7.0}]},
        {"id": 144, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Carlsberg", "ru": "Carlsberg", "en": "Carlsberg"},
            "təsvir": "", "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 4.3}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 5.3}]},
        {"id": 145, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {
            "az": "Carlsberg Xüsusi Qablaşmada 3L", "ru": "Carlsberg в специальной таре 3л", "en": "Carlsberg Special Tower 3L"}, "qiymət": 36.0, "təsvir": ""},
        {"id": 146, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Alivaria", "ru": "Аливария", "en": "Alivaria"}, "təsvir": "",
            "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 3.9}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 6.5}]},
        {"id": 147, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Xırdalan", "ru": "Xırdalan", "en": "Xirdalan"}, "təsvir": "",
            "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 3.6}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 3.8}]},
        {"id": 148, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Xırdalan NF", "ru": "Xırdalan Нефильтрованное", "en": "Xirdalan Unfiltered"},
            "təsvir": "", "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 3.6}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 4.5}]},
        {"id": 149, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Blanche", "ru": "Blanche", "en": "Blanche"}, "təsvir": "",
            "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 6.9}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 8.9}]},
        {"id": 150, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Erdinger", "ru": "Erdinger", "en": "Erdinger"}, "təsvir": "",
            "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 6.9}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 8.9}]},
        {"id": 151, "category_translated": {"az": "ÇƏLLƏK PİVƏ", "ru": "РАЗЛИВНОЕ ПИВО", "en": "DRAFT BEER"}, "adı": {"az": "Prazacka", "ru": "Prazacka", "en": "Prazacka"}, "təsvir": "",
            "options": [{"label": {"az": "330 ml", "ru": "330 мл", "en": "330 ml"}, "qiymət": 6.9}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 8.9}]},
    ],
    "QIRMIZI ŞƏRAB": [
        {"id": 152, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Chabiant Kəmşirin", "ru": "Chabiant Полусладкое", "en": "Chabiant Semi-Sweet"}, "qiymət": 39.0, "təsvir": ""},
        {"id": 153, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Meysəri Mərcan", "ru": "Meysəri Mərcan", "en": "Meysari Marjan"}, "qiymət": 40.0, "təsvir": ""},
        {"id": 154, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Meysəri Məxməri", "ru": "Meysəri Məxməri", "en": "Meysari Makhmari"}, "qiymət": 43.0, "təsvir": ""},
        {"id": 155, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"},
            "adı": {"az": "Rubai", "ru": "Рубаи", "en": "Rubai"}, "qiymət": 24.0, "təsvir": ""},
        {"id": 156, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Badaqoni Kindzmarauli", "ru": "Бадагони Киндзмараули", "en": "Badagoni Kindzmarauli"}, "qiymət": 51.0, "təsvir": ""},
        {"id": 157, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Savalan Cabernet Merlot", "ru": "Savalan Cabernet Merlot", "en": "Savalan Cabernet Merlot"}, "qiymət": 43.0, "təsvir": ""},
        {"id": 158, "category_translated": {"az": "QIRMIZI ŞƏRAB", "ru": "КРАСНОЕ ВИНО", "en": "RED WINE"}, "adı": {
            "az": "Savalan Merlot", "ru": "Savalan Merlot", "en": "Savalan Merlot"}, "qiymət": 43.0, "təsvir": ""},
    ],
    "AĞ ŞƏRAB": [
        {"id": 159, "category_translated": {"az": "AĞ ŞƏRAB", "ru": "БЕЛОЕ ВИНО", "en": "WHITE WINE"}, "adı": {"az": "Chabiant Kəmşirin", "ru": "Chabiant Полусладкое", "en": "Chabiant Semi-Sweet"},
            "təsvir": "", "options": [{"label": {"az": "Qədəh", "ru": "Бокал", "en": "Glass"}, "qiymət": 10.0}, {"label": {"az": "Şüşə", "ru": "Бутылка", "en": "Bottle"}, "qiymət": 39.0}]},
        {"id": 160, "category_translated": {"az": "AĞ ŞƏRAB", "ru": "БЕЛОЕ ВИНО", "en": "WHITE WINE"}, "adı": {"az": "Meysəri Sədəf", "ru": "Meysəri Sədəf", "en": "Meysari Sadaf"},
            "təsvir": "", "options": [{"label": {"az": "Qədəh", "ru": "Бокал", "en": "Glass"}, "qiymət": 10.0}, {"label": {"az": "Şüşə", "ru": "Бутылка", "en": "Bottle"}, "qiymət": 39.0}]},
        {"id": 161, "category_translated": {"az": "AĞ ŞƏRAB", "ru": "БЕЛОЕ ВИНО", "en": "WHITE WINE"}, "adı": {
            "az": "Cinandali", "ru": "Цинандали", "en": "Tsinandali"}, "qiymət": 51.0, "təsvir": ""},
        {"id": 162, "category_translated": {"az": "AĞ ŞƏRAB", "ru": "БЕЛОЕ ВИНО", "en": "WHITE WINE"}, "adı": {
            "az": "Savalan Chardonnay", "ru": "Savalan Chardonnay", "en": "Savalan Chardonnay"}, "qiymət": 43.0, "təsvir": ""},
    ],
    "ÇƏHRAYI ŞƏRAB": [
        {"id": 163, "category_translated": {"az": "ÇƏHRAYI ŞƏRAB", "ru": "РОЗОВОЕ ВИНО", "en": "ROSE WINE"}, "adı": {"az": "Chabiant Çəhrayı Turş", "ru": "Chabiant Розовое Сухое", "en": "Chabiant Rose Dry"},
            "təsvir": "", "options": [{"label": {"az": "Qədəh", "ru": "Бокал", "en": "Glass"}, "qiymət": 10.0}, {"label": {"az": "Şüşə", "ru": "Бутылка", "en": "Bottle"}, "qiymət": 38.7}]},
        {"id": 164, "category_translated": {"az": "ÇƏHRAYI ŞƏRAB", "ru": "РОЗОВОЕ ВИНО", "en": "ROSE WINE"}, "adı": {"az": "Meysəri Sənəm", "ru": "Meysəri Sənəm", "en": "Meysari Sanam"},
            "təsvir": "", "options": [{"label": {"az": "Qədəh", "ru": "Бокал", "en": "Glass"}, "qiymət": 10.0}, {"label": {"az": "Şüşə", "ru": "Бутылка", "en": "Bottle"}, "qiymət": 38.7}]},
    ],
    "OYNAQ ŞƏRABLAR": [
        {"id": 165, "category_translated": {"az": "OYNAQ ŞƏRABLAR", "ru": "ИГРИСТЫЕ ВИНА", "en": "SPARKLING WINE"},
            "adı": {"az": "Martini Asti", "ru": "Martini Asti", "en": "Martini Asti"}, "qiymət": 101.0, "təsvir": ""},
        {"id": 166, "category_translated": {"az": "OYNAQ ŞƏRABLAR", "ru": "ИГРИСТЫЕ ВИНА", "en": "SPARKLING WINE"}, "adı": {
            "az": "Bottega Prosecco", "ru": "Bottega Prosecco", "en": "Bottega Prosecco"}, "qiymət": 92.0, "təsvir": ""},
        {"id": 167, "category_translated": {"az": "OYNAQ ŞƏRABLAR", "ru": "ИГРИСТЫЕ ВИНА", "en": "SPARKLING WINE"},
            "adı": {"az": "Abrau Durso", "ru": "Абрау Дюрсо", "en": "Abrau Durso"}, "qiymət": 35.0, "təsvir": ""},
    ],
    "SPİRTSİZ KOKTEYLLƏR": [
        {"id": 168, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"},
            "adı": {"az": "Oreo Şeyk", "ru": "Орео Шейк", "en": "Oreo Shake"}, "qiymət": 10.6, "təsvir": ""},
        {"id": 169, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ",
                                            "en": "MOCKTAILS"}, "adı": {"az": "Smuzi", "ru": "Смузи", "en": "Smoothie"}, "qiymət": 9.1, "təsvir": ""},
        {"id": 170, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"},
            "adı": {"az": "Təzə Limonad", "ru": "Свежий Лимонад", "en": "Fresh Lemonade"}, "qiymət": 7.2, "təsvir": ""},
        {"id": 171, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"},
            "adı": {"az": "Mojito", "ru": "Мохито Б/А", "en": "Virgin Mojito"}, "qiymət": 8.0, "təsvir": ""},
        {"id": 172, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"}, "adı": {
            "az": "Mojito Energy", "ru": "Мохито Энерджи Б/А", "en": "Virgin Mojito Energy"}, "qiymət": 13.8, "təsvir": ""},
        {"id": 173, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"},
            "adı": {"az": "Energy Blue", "ru": "Энерджи Блю", "en": "Energy Blue"}, "qiymət": 12.6, "təsvir": ""},
        {"id": 174, "category_translated": {"az": "SPİRTSİZ KOKTEYLLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "MOCKTAILS"},
            "adı": {"az": "Milkşeyk", "ru": "Молочный коктейль", "en": "Milkshake"}, "qiymət": 10.0, "təsvir": ""},
    ],
    "SPİRTLİ KOKTEYLLƏR": [
        {"id": 175, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"}, "adı": {
            "az": "Mojito Klassik", "ru": "Мохито Классический", "en": "Classic Mojito"}, "qiymət": 12.1, "təsvir": ""},
        {"id": 176, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Mojito Energy", "ru": "Мохито Энерджи", "en": "Mojito Energy"}, "qiymət": 17.5, "təsvir": ""},
        {"id": 177, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Cosmopolitan", "ru": "Космополитан", "en": "Cosmopolitan"}, "qiymət": 11.4, "təsvir": ""},
        {"id": 178, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Sangria", "ru": "Сангрия", "en": "Sangria"}, "qiymət": 9.3, "təsvir": ""},
        {"id": 179, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Aperol Spritz", "ru": "Апероль Шприц", "en": "Aperol Spritz"}, "qiymət": 11.3, "təsvir": ""},
        {"id": 180, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Long Island", "ru": "Лонг Айленд", "en": "Long Island Iced Tea"}, "qiymət": 19.1, "təsvir": ""},
        {"id": 181, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Margarita", "ru": "Маргарита", "en": "Margarita"}, "qiymət": 12.1, "təsvir": ""},
        {"id": 182, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Tequila Sunrise", "ru": "Текила Санрайз", "en": "Tequila Sunrise"}, "qiymət": 10.3, "təsvir": ""},
        {"id": 183, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Sex on the Beach", "ru": "Секс на пляже", "en": "Sex on the Beach"}, "qiymət": 12.5, "təsvir": ""},
        {"id": 184, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Bullfrog", "ru": "Буллфрог", "en": "Bullfrog"}, "qiymət": 19.4, "təsvir": ""},
        {"id": 185, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Cuba Libre", "ru": "Куба Либре", "en": "Cuba Libre"}, "qiymət": 13.2, "təsvir": ""},
        {"id": 186, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Gin Tonic", "ru": "Джин Тоник", "en": "Gin Tonic"}, "qiymət": 13.9, "təsvir": ""},
        {"id": 187, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Negroni", "ru": "Негрони", "en": "Negroni"}, "qiymət": 12.5, "təsvir": ""},
        {"id": 188, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Mai Tai", "ru": "Май Тай", "en": "Mai Tai"}, "qiymət": 16.0, "təsvir": ""},
        {"id": 189, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Jager Moon", "ru": "Егер Мун", "en": "Jager Moon"}, "qiymət": 17.2, "təsvir": ""},
        {"id": 190, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Green Shot Set", "ru": "Грин Шот Сет", "en": "Green Shot Set"}, "qiymət": 17.3, "təsvir": ""},
        {"id": 191, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Blue Shot Set", "ru": "Блю Шот Сет", "en": "Blue Shot Set"}, "qiymət": 18.6, "təsvir": ""},
        {"id": 192, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Red Shot Set", "ru": "Ред Шот Сет", "en": "Red Shot Set"}, "qiymət": 20.8, "təsvir": ""},
        {"id": 193, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ", "en": "COCKTAILS"},
            "adı": {"az": "Dark Shot Set", "ru": "Дарк Шот Сет", "en": "Dark Shot Set"}, "qiymət": 22.6, "təsvir": ""},
        {"id": 194, "category_translated": {"az": "SPİRTLİ KOKTEYLLƏR", "ru": "АЛКОГОЛЬНЫЕ КОКТЕЙЛИ",
                                            "en": "COCKTAILS"}, "adı": {"az": "B-52", "ru": "Б-52", "en": "B-52"}, "qiymət": 10.4, "təsvir": ""},
    ],
    "EASY MIX": [
        {"id": 195, "category_translated": {"az": "EASY MIX", "ru": "EASY MIX", "en": "EASY MIX"}, "adı": {"az": "Johnnie Walker Black Label & Cola",
                                                                                                           "ru": "Johnnie Walker Black Label & Cola", "en": "Johnnie Walker Black Label & Cola"}, "qiymət": 12.9, "təsvir": ""},
        {"id": 196, "category_translated": {"az": "EASY MIX", "ru": "EASY MIX", "en": "EASY MIX"}, "adı": {"az": "Johnnie Walker Black Label & Redbull",
                                                                                                           "ru": "Johnnie Walker Black Label & Redbull", "en": "Johnnie Walker Black Label & Redbull"}, "qiymət": 16.1, "təsvir": ""},
        {"id": 197, "category_translated": {"az": "EASY MIX", "ru": "EASY MIX", "en": "EASY MIX"}, "adı": {
            "az": "Gordon's & Tonic", "ru": "Gordon's & Tonic", "en": "Gordon's & Tonic"}, "qiymət": 10.9, "təsvir": ""},
        {"id": 198, "category_translated": {"az": "EASY MIX", "ru": "EASY MIX", "en": "EASY MIX"}, "adı": {
            "az": "Captain Morgan & Cola", "ru": "Captain Morgan & Cola", "en": "Captain Morgan & Cola"}, "qiymət": 12.1, "təsvir": ""},
    ],
    "GİN": [
        {"id": 199, "category_translated": {"az": "GİN", "ru": "ДЖИН", "en": "GIN"}, "adı": {
            "az": "Gordon's", "ru": "Gordon's", "en": "Gordon's"}, "qiymət": 7.5, "təsvir": ""},
        {"id": 200, "category_translated": {"az": "GİN", "ru": "ДЖИН", "en": "GIN"}, "adı": {
            "az": "Bombay Sapphire", "ru": "Bombay Sapphire", "en": "Bombay Sapphire"}, "qiymət": 8.6, "təsvir": ""},
        {"id": 201, "category_translated": {"az": "GİN", "ru": "ДЖИН", "en": "GIN"}, "adı": {
            "az": "Hendrick's", "ru": "Hendrick's", "en": "Hendrick's"}, "qiymət": 11.5, "təsvir": ""},
    ],
    "KONYAK": [
        {"id": 202, "category_translated": {"az": "KONYAK", "ru": "КОНЬЯК", "en": "COGNAC"}, "adı": {
            "az": "Martell V.S.", "ru": "Martell V.S.", "en": "Martell V.S."}, "qiymət": 15.4, "təsvir": ""},
        {"id": 203, "category_translated": {"az": "KONYAK", "ru": "КОНЬЯК", "en": "COGNAC"}, "adı": {
            "az": "Martell X.O.", "ru": "Martell X.O.", "en": "Martell X.O."}, "qiymət": 49.1, "təsvir": ""},
        {"id": 204, "category_translated": {"az": "KONYAK", "ru": "КОНЬЯК", "en": "COGNAC"}, "adı": {
            "az": "Remy Martin V.S.O.P", "ru": "Remy Martin V.S.O.P", "en": "Remy Martin V.S.O.P"}, "qiymət": 22.9, "təsvir": ""},
        {"id": 205, "category_translated": {"az": "KONYAK", "ru": "КОНЬЯК", "en": "COGNAC"}, "adı": {
            "az": "Remy Martin X.O.", "ru": "Remy Martin X.O.", "en": "Remy Martin X.O."}, "qiymət": 46.5, "təsvir": ""},
    ],
    "LİKOR VƏ BİTTER": [
        {"id": 206, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Baileys", "ru": "Baileys", "en": "Baileys"}, "qiymət": 9.2, "təsvir": ""},
        {"id": 207, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Drambuie", "ru": "Drambuie", "en": "Drambuie"}, "qiymət": 7.5, "təsvir": ""},
        {"id": 208, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Kahlua", "ru": "Kahlua", "en": "Kahlua"}, "qiymət": 8.7, "təsvir": ""},
        {"id": 209, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"}, "adı": {"az": "Kilda Strawberry", "ru": "Kilda Strawberry", "en": "Kilda Strawberry"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 7.5}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 110.0}]},
        {"id": 210, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"}, "adı": {"az": "Kilda Lemon", "ru": "Kilda Lemon", "en": "Kilda Lemon"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 7.5}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 110.0}]},
        {"id": 211, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"}, "adı": {"az": "Jagermeister", "ru": "Jagermeister", "en": "Jagermeister"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 8.9}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 135.6}]},
        {"id": 212, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Yeni Raki", "ru": "Yeni Raki", "en": "Yeni Raki"}, "qiymət": 8.9, "təsvir": ""},
        {"id": 213, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Sambuca", "ru": "Самбука", "en": "Sambuca"}, "qiymət": 9.7, "təsvir": ""},
        {"id": 214, "category_translated": {"az": "LİKOR VƏ BİTTER", "ru": "ЛИКЕРЫ И БИТТЕРЫ", "en": "LIQUEUR & BITTERS"},
            "adı": {"az": "Absent", "ru": "Абсент", "en": "Absinthe"}, "qiymət": 12.5, "təsvir": ""},
    ],
    "ROM": [
        {"id": 215, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Bacardi Carta Blanca", "ru": "Bacardi Carta Blanca", "en": "Bacardi Carta Blanca"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 216, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Bacardi Carta Oro", "ru": "Bacardi Carta Oro", "en": "Bacardi Carta Oro"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 217, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Bacardi Carta Negra", "ru": "Bacardi Carta Negra", "en": "Bacardi Carta Negra"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 218, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Captain Morgan Gold", "ru": "Captain Morgan Gold", "en": "Captain Morgan Gold"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 219, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Captain Morgan Black", "ru": "Captain Morgan Black", "en": "Captain Morgan Black"}, "qiymət": 8.2, "təsvir": ""},
        {"id": 220, "category_translated": {"az": "ROM", "ru": "РОМ", "en": "RUM"}, "adı": {
            "az": "Lamb's Gold", "ru": "Lamb's Gold", "en": "Lamb's Gold"}, "qiymət": 8.5, "təsvir": ""},
    ],
    "ARAQ": [
        {"id": 221, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Stolicnaya Sever", "ru": "Столичная Север", "en": "Stolichnaya Sever"},
            "təsvir": "", "options": [{"label": {"az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 39.8}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 56.0}]},
        {"id": 222, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Absolut", "ru": "Absolut", "en": "Absolut"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 56.3}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 79.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 113.0}]},
        {"id": 223, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Finlandia", "ru": "Finlandia", "en": "Finlandia"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 52.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 73.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 104.0}]},
        {"id": 224, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Banketnaya", "ru": "Банкетная", "en": "Banketnaya"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 26.2}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 31.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 35.0}]},
        {"id": 225, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Goral", "ru": "Goral", "en": "Goral"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 99.6}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 71.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 142.0}]},
        {"id": 226, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Russkiy Standart Platinum", "ru": "Русский Стандарт Платинум", "en": "Russian Standard Platinum"}, "təsvir": "", "options": [
            {"label": {"az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 43.3}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 61.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 87.0}]},
        {"id": 227, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Zelyonaya Marka", "ru": "Зеленая Марка", "en": "Zelyonaya Marka"}, "təsvir": "",
            "options": [{"label": {"az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 30.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 42.0}]},
        {"id": 228, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Parlament", "ru": "Парламент", "en": "Parliament"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 33.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 46.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 62.0}]},
        {"id": 229, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Protokol Vstreçi", "ru": "Протокол Встречи", "en": "Protocol Vstrechi"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 16.7}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 22.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 31.0}]},
        {"id": 230, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Kazaçka Rada", "ru": "Козацкая Рада", "en": "Kazatskaya Rada"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 18.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 25.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 36.0}]},
        {"id": 231, "category_translated": {"az": "ARAQ", "ru": "ВОДКА", "en": "VODKA"}, "adı": {"az": "Svedka", "ru": "Svedka", "en": "Svedka"}, "təsvir": "", "options": [{"label": {
            "az": "0.5 L", "ru": "0.5 Л", "en": "0.5 L"}, "qiymət": 48.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 67.0}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 96.0}]},
    ],
    "TEKİLA": [
        {"id": 232, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Olmeca", "ru": "Olmeca", "en": "Olmeca"}, "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 7.5}, {
            "label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 74.5}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 93.4}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 124.0}]},
        {"id": 234, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Patron Silver", "ru": "Patron Silver", "en": "Patron Silver"}, "təsvir": "",
            "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 14.5}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 210.0}]},
        {"id": 235, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Don Julio Bianco", "ru": "Don Julio Bianco", "en": "Don Julio Bianco"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 15.0}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 220.0}]},
        {"id": 236, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Butterfly", "ru": "Butterfly", "en": "Butterfly"}, "təsvir": "",
            "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 11.0}, {"label": {"az": "500 ml", "ru": "500 мл", "en": "500 ml"}, "qiymət": 140.0}]},
        {"id": 237, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Milagro Silver", "ru": "Milagro Silver", "en": "Milagro Silver"}, "təsvir": "",
            "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 12.0}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 140.0}]},
        {"id": 238, "category_translated": {"az": "TEKİLA", "ru": "ТЕКИЛА", "en": "TEQUILA"}, "adı": {"az": "Sierra Antiguo Plata", "ru": "Sierra Antiguo Plata", "en": "Sierra Antiguo Plata"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 6.6}, {"label": {"az": "700 ml", "ru": "700 мл", "en": "700 ml"}, "qiymət": 96.6}]},
    ],
    "VİSKİ": [
        {"id": 239, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {"az": "Chivas Regal 12", "ru": "Chivas Regal 12", "en": "Chivas Regal 12"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 8.5}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 145.4}]},
        {"id": 240, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Chivas Regal 18 40ml", "ru": "Chivas Regal 18 40мл", "en": "Chivas Regal 18 40ml"}, "qiymət": 21.4, "təsvir": ""},
        {"id": 241, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Royal Salute 21 40ml", "ru": "Royal Salute 21 40мл", "en": "Royal Salute 21 40ml"}, "qiymət": 28.7, "təsvir": ""},
        {"id": 242, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Glenfiddich 12 40ml", "ru": "Glenfiddich 12 40мл", "en": "Glenfiddich 12 40ml"}, "qiymət": 14.7, "təsvir": ""},
        {"id": 243, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "J&B 40ml", "ru": "J&B 40мл", "en": "J&B 40ml"}, "qiymət": 6.3, "təsvir": ""},
        {"id": 244, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {"az": "Tullamore Dew", "ru": "Tullamore Dew", "en": "Tullamore Dew"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 6.5}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 103.3}]},
        {"id": 245, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Red Label 40ml", "ru": "Red Label 40мл", "en": "Red Label 40ml"}, "qiymət": 6.8, "təsvir": ""},
        {"id": 246, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Black Label 40ml", "ru": "Black Label 40мл", "en": "Black Label 40ml"}, "qiymət": 9.1, "təsvir": ""},
        {"id": 247, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Blue Label 40ml", "ru": "Blue Label 40мл", "en": "Blue Label 40ml"}, "qiymət": 50.4, "təsvir": ""},
        {"id": 248, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Jack Daniel's 40ml", "ru": "Jack Daniel's 40мл", "en": "Jack Daniel's 40ml"}, "qiymət": 8.9, "təsvir": ""},
        {"id": 249, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Jack Daniel's Honey 40ml", "ru": "Jack Daniel's Honey 40мл", "en": "Jack Daniel's Honey 40ml"}, "qiymət": 10.2, "təsvir": ""},
        {"id": 250, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {"az": "Jameson", "ru": "Jameson", "en": "Jameson"}, "təsvir": "",
            "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 8.9}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 132.3}]},
        {"id": 251, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Ballantine's 40ml", "ru": "Ballantine's 40мл", "en": "Ballantine's 40ml"}, "qiymət": 6.8, "təsvir": ""},
        {"id": 252, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {
            "az": "Monkey Shoulder 40ml", "ru": "Monkey Shoulder 40мл", "en": "Monkey Shoulder 40ml"}, "qiymət": 10.3, "təsvir": ""},
        {"id": 253, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {"az": "The Glenlivet 12 Y.O", "ru": "The Glenlivet 12 Y.O", "en": "The Glenlivet 12 Y.O"},
            "təsvir": "", "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 9.4}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 165.9}]},
        {"id": 254, "category_translated": {"az": "VİSKİ", "ru": "ВИСКИ", "en": "WHISKEY"}, "adı": {"az": "Fordman", "ru": "Fordman", "en": "Fordman"}, "təsvir": "",
            "options": [{"label": {"az": "40 ml", "ru": "40 мл", "en": "40 ml"}, "qiymət": 6.0}, {"label": {"az": "0.7 L", "ru": "0.7 Л", "en": "0.7 L"}, "qiymət": 93.4}]},
    ],
    "SƏRİN İÇKİLƏR": [
        {"id": 255, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {
            "az": "Coca-Cola / Fanta / Sprite", "ru": "Coca-Cola / Fanta / Sprite", "en": "Coca-Cola / Fanta / Sprite"}, "qiymət": 4.2, "təsvir": ""},
        {"id": 256, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {"az": "Təbii Şirə", "ru": "Натуральный сок", "en": "Fruit Juice"},
            "təsvir": "", "options": [{"label": {"az": "200 ml", "ru": "200 мл", "en": "200 ml"}, "qiymət": 4.2}, {"label": {"az": "1 L", "ru": "1 Л", "en": "1 L"}, "qiymət": 9.4}]},
        {"id": 257, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {"az": "Təbii Şirə Swell", "ru": "Натуральный сок Swell", "en": "Fruit Juice Swell"},
            "təsvir": "", "options": [{"label": {"az": "200 ml", "ru": "200 мл", "en": "200 ml"}, "qiymət": 5.8}, {"label": {"az": "750 ml", "ru": "750 мл", "en": "750 ml"}, "qiymət": 11.0}]},
        {"id": 258, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"},
            "adı": {"az": "İstisu 500ml", "ru": "Истису 500мл", "en": "Istisu 500ml"}, "qiymət": 3.4, "təsvir": ""},
        {"id": 259, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {
            "az": "Sirma (Qazlı / Qazsız) 700ml", "ru": "Sirma (С газом / Без газа) 700мл", "en": "Sirma (Sparkling / Still) 700ml"}, "qiymət": 6.3, "təsvir": ""},
        {"id": 260, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {
            "az": "Sirab (Qazlı / Qazsız) 500ml", "ru": "Sirab (С газом / Без газа) 500мл", "en": "Sirab (Sparkling / Still) 500ml"}, "qiymət": 3.4, "təsvir": ""},
        {"id": 261, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {
            "az": "Ev Sayağı Soyuq Çay", "ru": "Домашний холодный чай", "en": "Homemade Ice Tea"}, "qiymət": 6.3, "təsvir": ""},
        {"id": 262, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"},
            "adı": {"az": "Limonad", "ru": "Лимонад", "en": "Lemonade"}, "qiymət": 4.7, "təsvir": ""},
        {"id": 263, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"},
            "adı": {"az": "Sarıkız", "ru": "Сарыкыз", "en": "Sarikiiz"}, "qiymət": 4.2, "təsvir": ""},
        {"id": 264, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"},
            "adı": {"az": "Tonik Su", "ru": "Тоник", "en": "Tonic Water"}, "qiymət": 5.2, "təsvir": ""},
        {"id": 265, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"}, "adı": {
            "az": "Təzə Sıxılmış Şirələr", "ru": "Свежевыжатые соки", "en": "Freshly Squeezed Juices"}, "qiymət": 8.4, "təsvir": ""},
        {"id": 266, "category_translated": {"az": "SƏRİN İÇKİLƏR", "ru": "БЕЗАЛКОГОЛЬНЫЕ НАПИТКИ", "en": "SOFT DRINKS"},
            "adı": {"az": "Bizon Max", "ru": "Bizon Max", "en": "Bizon Max"}, "qiymət": 5.0, "təsvir": ""},
    ],
    "İSTİ İÇKİLƏR": [
        {"id": 267, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"}, "adı": {"az": "Qara Çay", "ru": "Черный чай", "en": "Black Tea"},
            "təsvir": "", "options": [{"label": {"az": "Fincan", "ru": "Чашка", "en": "Cup"}, "qiymət": 3.2}, {"label": {"az": "Çaydan", "ru": "Чайник", "en": "Teapot"}, "qiymət": 9.4}]},
        {"id": 268, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"}, "adı": {"az": "Yaşıl Çay", "ru": "Зеленый чай", "en": "Green Tea"},
            "təsvir": "", "options": [{"label": {"az": "Fincan", "ru": "Чашка", "en": "Cup"}, "qiymət": 4.2}, {"label": {"az": "Çaydan", "ru": "Чайник", "en": "Teapot"}, "qiymət": 9.4}]},
        {"id": 269, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"},
            "adı": {"az": "Amerikano", "ru": "Американо", "en": "Americano"}, "qiymət": 4.2, "təsvir": ""},
        {"id": 270, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"},
            "adı": {"az": "Latte", "ru": "Латте", "en": "Latte"}, "qiymət": 6.3, "təsvir": ""},
        {"id": 271, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"},
            "adı": {"az": "Kapuçino", "ru": "Капучино", "en": "Cappuccino"}, "qiymət": 5.2, "təsvir": ""},
        {"id": 272, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"},
            "adı": {"az": "Espresso", "ru": "Эспрессо", "en": "Espresso"}, "qiymət": 4.2, "təsvir": ""},
        {"id": 273, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"},
            "adı": {"az": "Glace Qəhvəsi", "ru": "Кофе Гляссе", "en": "Glace Coffee"}, "qiymət": 8.4, "təsvir": ""},
        {"id": 274, "category_translated": {"az": "İSTİ İÇKİLƏR", "ru": "ГОРЯЧИЕ НАПИТКИ", "en": "HOT DRINKS"}, "adı": {
            "az": "İrland Sayağı Qəhvə", "ru": "Кофе по-ирландски", "en": "Irish Coffee"}, "qiymət": 12.6, "təsvir": ""},
    ],
    "STAY CLASSIC": [
        {"id": 275, "category_translated": {"az": "STAY CLASSIC", "ru": "STAY CLASSIC", "en": "STAY CLASSIC"}, "adı": {
            "az": "Red Bull Vodka", "ru": "Red Bull Vodka", "en": "Red Bull Vodka"}, "qiymət": 12.1, "təsvir": ""},
        {"id": 276, "category_translated": {"az": "STAY CLASSIC", "ru": "STAY CLASSIC", "en": "STAY CLASSIC"}, "adı": {
            "az": "Red Bull Whisky", "ru": "Red Bull Whisky", "en": "Red Bull Whisky"}, "qiymət": 14.2, "təsvir": ""},
        {"id": 277, "category_translated": {"az": "STAY CLASSIC", "ru": "STAY CLASSIC", "en": "STAY CLASSIC"}, "adı": {
            "az": "Red Bull Jager", "ru": "Red Bull Jager", "en": "Red Bull Jager"}, "qiymət": 13.6, "təsvir": ""},
        {"id": 278, "category_translated": {"az": "STAY CLASSIC", "ru": "STAY CLASSIC", "en": "STAY CLASSIC"}, "adı": {
            "az": "Tropical Gin", "ru": "Tropical Gin", "en": "Tropical Gin"}, "qiymət": 12.6, "təsvir": ""},
    ],
}

# ==========================================
# ROUTE-LAR
# ==========================================


@app.route("/table/<table_number>")
def table_menu(table_number):
    user_token = request.args.get("token")

    # Əgər doğru NFC token ilə daxil olunubsa, telefona təkistifadəlik təsdiq bayrağı yazılır
    if user_token == NFC_SECRET_TOKEN:
        session[f"nfc_verified_table_{table_number}"] = True

    return render_template(
        "restoran_menu_qonaq.html",
        table_number=table_number,
        menu=MENU
    )


# ADMIN PANELİ ŞİFRƏ İLƏ QORUNUR
@app.route("/admin")
@requires_auth
def admin_panel():
    return render_template("restoran_menu_admin.html")


@app.route("/api/system-status", methods=["GET"])
@limiter.exempt
def get_system_status():
    return jsonify({"active": SYSTEM_ACTIVE})


@app.route("/api/orders", methods=["GET"])
@limiter.exempt
def get_orders():
    return jsonify(ORDERS)


# Dəqiqədə maks 5 sifariş göndərmək olar (Spam qoruması)
@app.route("/api/order", methods=["POST"])
@limiter.limit("5 per minute")
def place_order():
    if not SYSTEM_ACTIVE:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Restoran hazırda bağlıdır! Zəhmət olmasa iş saatlarında sifariş verin.",
                }
            ),
            400,
        )

    data = request.json or {}
    table_number = str(data.get("table_number", "1"))

    # SİFARİŞ ANINDA NFC YOXLANIŞI
    if not session.get(f"nfc_verified_table_{table_number}"):
        return jsonify({
            "status": "error",
            "message": "⚠️ Sifariş vermək üçün telefonunuzu masadakı NFC çipinə toxundurun!"
        }), 403

    raw_items = data.get("items", [])
    total_price = data.get("total_price", "0.00")
    note = str(data.get("note", "")).strip()

    order_id = len(ORDERS) + 1
    order_time = datetime.now().strftime("%H:%M:%S")

    def get_menu_item_by_id(item_id):
        for cat, item_list in MENU.items():
            for m_item in item_list:
                if str(m_item.get("id")) == str(item_id):
                    return m_item
        return None

    az_items = []
    for item in raw_items:
        item_id = item.get("itemId") or item.get("id")
        opt_index = item.get("optionIndex")

        menu_item = get_menu_item_by_id(
            item_id) if item_id is not None else None

        if menu_item:
            az_name = menu_item["adı"]["az"]
            if opt_index is not None and "options" in menu_item:
                try:
                    opt_idx = int(opt_index)
                    opt_label_az = menu_item["options"][opt_idx]["label"]["az"]
                    az_name += f" ({opt_label_az})"
                except (IndexError, TypeError, ValueError):
                    pass
            item_name = az_name
        else:
            raw_name = item.get("name", "")
            item_name = raw_name.get("az", str(raw_name)) if isinstance(
                raw_name, dict) else str(raw_name)

        az_items.append({
            "name": item_name,
            "price": item.get("price", 0.0)
        })

    order = {
        "id": order_id,
        "table_number": table_number,
        "items": az_items,
        "total_price": total_price,
        "note": note,
        "status": "Yeni Sifariş 🔔",
        "time": order_time,
    }

    ORDERS.append(order)

    # SİFARİŞ GÖNDƏRİLDİKDƏN SONRA NFC İCAZƏSİ SIFIRLANIR (Növbəti sifariş üçün təkrar NFC şərtləşir)
    session[f"nfc_verified_table_{table_number}"] = False

    safe_note = html.escape(note) if note else ""
    items_formatted = [
        f"• {html.escape(i['name'])} – {i['price']} AZN" for i in az_items]
    items_text = "\n".join(items_formatted)
    note_text = f"\n📝 <b>Qeyd:</b> {safe_note}\n" if safe_note else ""

    tg_message = (
        f"🍽️ <b>YENİ MASA SİFARİŞİ! #${order_id}</b>\n\n"
        f"📍 <b>Masa:</b> №{table_number}\n"
        f"⏰ <b>Vaxt:</b> {order_time}\n"
        f"📋 <b>Sifarişlər:</b>\n{items_text}\n"
        f"{note_text}\n"
        f"💰 <b>Cəmi:</b> {total_price} AZN"
    )

    send_telegram_notification(tg_message)

    return jsonify(
        {
            "status": "success",
            "message": "Sifarişiniz dərhal mətbəxə ötürüldü!",
            "order_id": order_id,
        }
    )


@app.route("/api/order/status", methods=["POST"])
@requires_auth
def update_order_status():
    try:
        data = request.json or {}
        order_id = data.get("order_id")
        new_status = data.get("status", "")

        target_table = None

        for order in ORDERS:
            if order.get("id") == order_id:
                order["status"] = new_status
                target_table = str(order.get("table_number"))
                break

        if "Ödənildi" in new_status and target_table:
            for order in ORDERS:
                if str(order.get("table_number")) == target_table:
                    order["status"] = "Ödənildi 💳"

        return jsonify({"status": "success", "message": "Status yeniləndi!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Dəqiqədə maks 3 dəfə çağırış etmək olar (Spam qoruması)
@app.route("/api/call-waiter", methods=["POST"])
@limiter.limit("3 per minute")
def call_waiter():
    if not SYSTEM_ACTIVE:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Restoran hazırda bağlıdır! Xidmət göstərilmir.",
                }
            ),
            400,
        )

    try:
        data = request.get_json(silent=True) or {}
        table = str(data.get("table_number", "1"))
        req_type = data.get("request_type", "Ofisiant Çağırılır 🔔")

        # ÇAĞIRIŞ ANINDA NFC YOXLANIŞI
        if not session.get(f"nfc_verified_table_{table}"):
            return jsonify({
                "status": "error",
                "message": "⚠️ Xidmət tələb etmək üçün telefonunuzu masadakı NFC çipinə toxundurun!"
            }), 403

        current_time = datetime.now().strftime("%H:%M")

        items_list = []
        total_sum = 0.0

        if "Hesab" in req_type and "ORDERS" in globals():
            for order in ORDERS:
                order_table = str(order.get("table_number"))
                order_status = str(order.get("status", ""))

                if order_table == table and "Ödənildi" not in order_status:
                    is_call_card = any(
                        "🔔" in str(item.get("name", ""))
                        for item in order.get("items", [])
                    )
                    if not is_call_card:
                        for item in order.get("items", []):
                            items_list.append(item)
                            try:
                                total_sum += float(item.get("price", 0))
                            except (ValueError, TypeError):
                                pass

        if not items_list:
            items_list = [{"name": f"🔔 {req_type}", "price": 0.0}]

        new_id = len(ORDERS) + 1 if "ORDERS" in globals() else 1

        call_order = {
            "id": new_id,
            "table_number": table,
            "items": items_list,
            "total_price": f"{total_sum:.2f}",
            "status": "Hazırlanır 🍳",
            "note": f"Müştəri çağırışı: {req_type}",
            "time": current_time,
        }

        if "ORDERS" in globals():
            ORDERS.append(call_order)

        # Çağırışdan sonra da NFC icazəsi sıfırlanır
        session[f"nfc_verified_table_{table}"] = False

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Masa №{table} üçün {req_type} bildirildi!",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reset-day", methods=["POST"])
@requires_auth
def reset_day():
    global ORDERS, SYSTEM_ACTIVE
    try:
        total_daily_revenue = 0.0
        total_orders_count = 0

        for order in ORDERS:
            if "Ödənildi" in str(order.get("status", "")):
                total_orders_count += 1
                try:
                    total_daily_revenue += float(order.get("total_price", 0))
                except (ValueError, TypeError):
                    pass

        ORDERS = []
        SYSTEM_ACTIVE = False

        summary_msg = f"Günün nəticəsi:\n------------------\nÖdənilmiş Sifariş Sayı: {total_orders_count}\nÜmumi Kassa Dövriyyəsi: {total_daily_revenue:.2f} AZN\n\nSistem bağlandı! Müştərilər artıq sifariş verə bilməyəcək."

        return jsonify({"status": "success", "message": summary_msg}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start-day", methods=["POST"])
@requires_auth
def start_day():
    global SYSTEM_ACTIVE
    SYSTEM_ACTIVE = True
    return jsonify(
        {
            "status": "success",
            "message": "Yeni iş günü başladı! Sistem müştərilər üçün aktiv edildi. 🚀",
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
