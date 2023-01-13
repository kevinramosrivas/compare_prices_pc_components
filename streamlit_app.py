
#importar librerias para scraping
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
import threading


def get_price_dolares():
    #obtener el tipo de cambio
    url = 'https://kambista.com/tipo-de-cambio/'
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    #buscar el div con la clase 'wpb_wrapper'
    wrapper = soup.find('div', class_='km_calc')
    #buscar el strong con id 'valcompra'
    strong = wrapper.find('strong', id='valcompra')
    #obtener el texto del strong
    strong = strong.text
    #eliminar el simbolo de soles
    strong = strong.replace('S/.', '')
    #convertir a float
    strong = float(strong)
    return strong

#crear un dataframe para que servira para guardar los datos de sercoplus
df_sercoplus = pd.DataFrame()
#crear un dataframe para que servira para guardar los datos de infotec
df_infotec = pd.DataFrame()
#variable para guardar el tipo de cambio hoy
tipo_cambio = get_price_dolares()


def clean_price_dollars(price):
    #eliminar $ por vacio
    price = price.replace('$', '')
    #eliminar espacios en blanco
    price = price.replace(' ', '')
    #reemplazar , por .
    price = price.replace(',', '.')
    if price.count('.') > 1:
        price = price.replace('.', '', 1)
    #convertir a float
    price = float(price)
    return price

def clean_price_soles(price):
    #eliminar ( o ) por vacio
    price = price.replace('(', '')
    price = price.replace(')', '')
    #eliminar espacios en blanco
    price = price.replace(' ', '')
    #eliminar S/ por vacio
    price = price.replace('S/', '')
    #reemplazar , por .
    price = price.replace(',', '.')
    if price.count('.') > 1:
        price = price.replace('.', '', 1)
    #convertir a float
    price = float(price)
    return price
def clean_stock(stock):
    #eliminar espacios en blanco
    stock = stock.replace(' ', '')
    #obtner mediantes una regex solo numeros
    stock = re.findall(r'\d+', stock)
    #convertir a int
    stock = int(stock[0])
    return stock

def get_info_products_Sercoplus(products):
    #crear lista de imagen, nombre, precio en dolares y precio en soles
    image_list = []
    name_list = []
    price_list_dolares = []
    price_list_soles = []
    link_list = []
    stock_list = []
    #recorrer productos
    for product in products:
        #capturar imagen en un div con clase product-thumbnail
        image = product.find('div', class_='product-thumbnail')
        #capturar imagen en un img con clase img-fluid
        image = image.find('img', class_='img-fluid')
        #obtener el link de la propiedad data-original
        image = image['data-original']
        #capturar nombre del producto en un h5 con clase product-name
        name = product.find('h5', class_='product-name')
        #capturar el link en una etiqueta a dentro de h5 en la propiedad href
        link = name.find('a')['href']
        #capturar el texto del nombre en una etiqueta a dentro de h5
        name = name.find('a').text
        #obtener el div que contiene el precio
        price = product.find('div', class_='first-prices d-flex flex-column')
        #obtener todos los span que contienen el precio
        price = price.find_all('span')
        #el precio del primer span es el precio en dolares
        price_dolares = price[0].text
        price_dolares = clean_price_dollars(price_dolares)
        #el precio del segundo span es el precio en soles
        price_soles = price[1].text
        price_soles = clean_price_soles(price_soles)
        #obtnemos el stock del producto
        stock = product.find('div', class_='first-prices d-flex flex-row')
        #encontramos todos los span que contienen el stock
        stock = stock.find_all('span')
        #el segundo span es el stock
        stock = stock[1].text
        stock = clean_stock(stock)
        #si el stock es 0, no agregar a las listas
        if stock == 0:
            continue
        #agregar a las listas
        image_list.append(image)
        name_list.append(name)
        price_list_dolares.append(price_dolares)
        price_list_soles.append(price_soles)
        link_list.append(link)
        stock_list.append(stock)
    return image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list

def get_number_pages(soup):
    #encontrar cuantas paginas hay
    pages_ul = soup.find('ul', class_='page-list')
    #si pages_ul es None, no hay paginas
    if pages_ul is None:
        return 1
    pages = pages_ul.find_all('li')
    #si no hay paginas, solo hay un elemento
    #obtener el numero de paginas en el penultimo elemento
    pages = pages[-2].text
    pages = int(pages)
    return pages

def get_prices_Sercoplus(producto):
    #reemplazar espacios en blanco por %20
    producto = producto.replace(' ', '%20')
    #definir url de busqueda
    url = 'https://www.sercoplus.com/busqueda?controller=search&s={}&order=product.price.asc'.format(producto)
    
    #hacer request
    response = requests.get(url)
    html = response.text
    #crear lista de imagen, nombre, precio en dolares y precio en soles
    image_list = []
    name_list = []
    price_list_dolares = []
    price_list_soles = []
    link_list = []
    stock_list = []
    #parsear html
    soup = BeautifulSoup(html, 'html.parser')
    pages = get_number_pages(soup)
    images = []
    names = []
    prices_dolares = []
    prices_soles = []
    links = []
    stocks = []

    #si hay mas de una pagina el url cambia
    if pages > 1: 
        #recorrer paginas
        for page in range(1, pages+1):
            #definir url de busqueda
            url = 'https://www.sercoplus.com/busqueda?controller=search&s={}&order=product.price.asc&page={}'.format(producto, page)
            #hacer request
            response = requests.get(url)
            html = response.text
            #parsear html
            soup = BeautifulSoup(html, 'html.parser')
            #capturar todos los productos
            products = soup.find_all('article', class_='product-miniature js-product-miniature')
            #obtener informacion de los productos
            image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_Sercoplus(products)
            #agregar a las listas
            images.extend(image_list)
            names.extend(name_list)
            prices_dolares.extend(price_list_dolares)
            prices_soles.extend(price_list_soles)
            links.extend(link_list)
            stocks.extend(stock_list)
    else:
        #capturar todos los productos
        products = soup.find_all('article', class_='product-miniature js-product-miniature')
        #obtener informacion de los productos
        image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_Sercoplus(products)
        #agregar a las listas
        images.extend(image_list)
        names.extend(name_list)
        prices_dolares.extend(price_list_dolares)
        prices_soles.extend(price_list_soles)
        links.extend(link_list)
        stocks.extend(stock_list)
    global df_sercoplus
    #crear dataframe con las listas ordenadas por precio en soles
    df_sercoplus = pd.DataFrame({'imagen': images, 'nombre': names, 'precio_dolares': prices_dolares, 'precio_soles': prices_soles, 'link': links, 'stock': stocks})
    #convertir nombre a string
    df_sercoplus['nombre'] = df_sercoplus['nombre'].astype(str)



def get_info_products_Infotec(products):
    #crear listas de imagen, nombre, precio en dolares, precio en soles, link y stock
    image_list = []
    name_list = []
    price_list_soles = []
    price_list_dolares = []
    link_list = []
    stock_list = []
    #recorrer todos los productos
    for product in products:
        #obtener imagen
        image = product.find('div', class_='thumbnail-container')
        image = image.find('img')
        image = image['src']
        #obtener nombre
        name = product.find('div', class_='product-name')
        name = name.find('a')
        #obtener el link del producto del href del nombre
        link = name['href']
        name = name.text
        #obtener precio en soles
        price = product.find('div', class_='price price-dark')
        #buscar la etiqueta ins
        price = price.find('ins')
        #obtener el texto de la etiqueta ins
        price = price.text
        #eliminar el simbolo de soles
        price = clean_price_soles(price)
        #obtener precio en dolares
        global price_dolares
        price_dolares = price/tipo_cambio
        #obtener stock
        stock = product.find('span', id='product-availability')
        stock = stock.find('span')
        stock = stock.text
        #agregar a las listas
        image_list.append(image)
        name_list.append(name)
        price_list_soles.append(price)
        price_list_dolares.append(price_dolares)
        link_list.append(link)
        stock_list.append(stock)
    return image_list, name_list, price_list_dolares,  price_list_soles, link_list, stock_list




def get_prices_Infotec(producto):
    #reemplazar espacios en blanco por %20
    producto = producto.replace(' ', '+')
    #definir url de busqueda
    url = 'https://www.infotec.com.pe/busquedas?search_query=={}'.format(producto)
    
    #hacer request
    response = requests.get(url)
    html = response.text
    #crear lista de imagen, nombre,link y precio en soles
    images = []
    names = []
    links = []
    prices_soles = []
    stocks = []
    price_dolares = []
    #parsear html
    soup = BeautifulSoup(html, 'html.parser')
    #buscar un div con la clase 'pagination'
    pagination = soup.find('div', class_='pagination')
    #verifiar cuantas paginas hay
    pages_ul = pagination.find('ul')
    #si pages_ul es None, no hay paginas
    if pages_ul is None:
        pages = 1
    else:
        pages = pages_ul.find_all('li')
        #si no hay paginas, solo hay un elemento
        #obtener el numero de paginas en el penultimo elemento
        pages = pages[-2].text
        pages = int(pages)
    #si hay mas de una pagina el url cambia
    if pages > 1:
        #recorrer paginas
        for page in range(1, pages+1):
            #definir url de busqueda
            url= 'https://www.infotec.com.pe/busquedas?page={}&search_query={}'.format(page, producto)
            #hacer request
            response = requests.get(url)
            html = response.text
            #parsear html
            soup = BeautifulSoup(html, 'html.parser')
            #capturar todos los productos
            products = soup.find_all('article', class_='product-miniature product-item js-product-miniature')
            #obtener informacion de los productos
            image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_Infotec(products)
            #agregar a las listas
            images.extend(image_list)
            names.extend(name_list)
            prices_soles.extend(price_list_soles)
            links.extend(link_list)
            stocks.extend(stock_list)
            price_dolares.extend(price_list_dolares)
    else:
        #capturar todos los productos
        products = soup.find_all('article', class_='product-miniature product-item')
        #obtener informacion de los productos
        image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_Infotec(products)
        #agregar a las listas
        images.extend(image_list)
        names.extend(name_list)
        prices_soles.extend(price_list_soles)
        links.extend(link_list)
        stocks.extend(stock_list)
        price_dolares.extend(price_list_dolares)
    global df_infotec
    #guardar en dataframe df_infotec con las listas ordenadas por precio en soles
    df_infotec = pd.DataFrame({'imagen':images, 'nombre':names, 'precio_dolares':price_dolares, 'precio_soles':prices_soles, 'link':links, 'stock':stocks})
    df_infotec = df_infotec.sort_values(by='precio_soles')
    df_infotec = df_infotec.reset_index(drop=True)
    #convertir la columna nombre a string
    df_infotec['nombre'] = df_infotec['nombre'].astype(str)



#eliminar productos que no tengan el nombre del producto buscado
def filter_products(df, producto):
    #convertir a minuscula
    producto = producto.lower()
    #eliminar productos que no tengan el nombre del producto buscado
    df = df[df['nombre'].str.lower().str.contains(producto)]
    return df







st.title('Comparador de precios de componentes de PC')
#recibimos el link de la pagina del usuario
link = st.text_input('Ingrese el producto que desea buscar: ')
#usamos un boton para que el usuario pueda enviar el link
if st.button('Enviar'):
    #poner un aviso de espere mientras se hace el request
    with st.spinner(text='Buscando los mejores precios...🕵️🪙🪄'):
        #crear 2 hilos para obtener los precios de los productos
        #hilo 1: sercoplus
        t1 = threading.Thread(target=get_prices_Sercoplus, args=(link,))
        #hilo 2: infotec
        t2 = threading.Thread(target=get_prices_Infotec, args=(link,))
        #iniciar los hilos
        t1.start()
        t2.start()
        #esperar a que los hilos terminen
        t1.join()
        t2.join()
        st.success('Precios encontrados!🪙🪄')
        #crear un dataframe con los precios de los productos
        #comparemos los precios en soles de los dos dataframes
        df_sercoplus = df_sercoplus.sort_values(by='precio_soles')
        df_sercoplus = df_sercoplus.reset_index(drop=True)
        df_infotec = df_infotec.sort_values(by='precio_soles')
        df_infotec = df_infotec.reset_index(drop=True)
        #filtrar los productos que no tengan el nombre del producto buscado
        df_sercoplus = filter_products(df_sercoplus, link)
        df_infotec = filter_products(df_infotec, link)
        #resetear los indices
        df_sercoplus = df_sercoplus.reset_index(drop=True)
        df_infotec = df_infotec.reset_index(drop=True)
        #redondear precio en soles y dolares a 2 decimales de sercoplus
        df_sercoplus['precio_dolares'] = df_sercoplus['precio_dolares'].round(2)
        df_sercoplus['precio_soles'] = df_sercoplus['precio_soles'].round(2)
        #redondear precio en soles y dolares a 2 decimales de infotec
        df_infotec['precio_dolares'] = df_infotec['precio_dolares'].round(2)
        df_infotec['precio_soles'] = df_infotec['precio_soles'].round(2)

    #haemos una tabla comparativa de los precios en soles de los 5 productos mas baratos
    st.subheader('Comparativa de precios en soles')
    st.write('Infotec')
    st.table(df_infotec.head(5))
    st.write('Sercoplus')
    st.table(df_sercoplus.head(5))







