
#importar librerias para scraping
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
import threading
import matplotlib.pyplot as plt
import concurrent.futures
import time
not_found_img = 'not_found.png'

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
#crear un dataframe para que servira para guardar los datos de sercoplus con las columnas imagen, nombre, precio_dolares, precio_soles, link, stock
df_sercoplus = pd.DataFrame(columns=['imagen', 'nombre', 'precio_dolares', 'precio_soles', 'link', 'stock'])
#crear un dataframe para que servira para guardar los datos de infotec
df_infotec = pd.DataFrame(columns=['imagen', 'nombre', 'precio_dolares', 'precio_soles', 'link', 'stock'])
#crear un dataframe para que servira para guardar los datos de cc computer
df_cccomputer = pd.DataFrame(columns=['imagen', 'nombre', 'precio_dolares', 'precio_soles', 'link', 'stock'])
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


def get_html_pags(url):
    #obtener html de la url
    response = requests.get(url)
    html = response.text
    return html



def get_prices_Sercoplus(producto):
    #contar el tiempo de inicio
    start_time = time.time()
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
    pages_url_list = []
    #si hay mas de una pagina el url cambia
    if pages > 1: 
        pages_url_list = []
        #guardar el url de cada pagina en una lista
        for page in range(1, pages+1):
            pages_url_list.append('https://www.sercoplus.com/busqueda?controller=search&s={}&order=product.price.asc&page={}'.format(producto, page))
        #crear pool de procesos
        with concurrent.futures.ThreadPoolExecutor() as executor:
          html = executor.map(get_html_pags, pages_url_list)
        #recorrer html de cada pagina
        for html_page in html:
            soup = BeautifulSoup(html_page, 'html.parser')
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
    df_sercoplus = df_sercoplus.sort_values(by='precio_soles')
    df_sercoplus = df_sercoplus.reset_index(drop=True)
    #contar el tiempo de finalizacion
    end_time = time.time()
    print('Sercoplus acabado en {} segundos'.format(end_time - start_time))


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
        #si no hay imagen, rellenar con None
        if image == '':
            image = None
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
    #contar el tiempo de inicio
    start_time = time.time()
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
        pages_url_list = []
        #guardar el url de cada pagina en una lista
        for page in range(1, pages+1):
            pages_url_list.append('https://www.infotec.com.pe/busquedas?page={}&search_query={}'.format(page, producto))
        with concurrent.futures.ThreadPoolExecutor() as executor:
          html = executor.map(get_html_pags, pages_url_list)
        for codigo in html:
            #parsear html
            soup = BeautifulSoup(codigo, 'html.parser')
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
    global df_infotec
    #guardar en dataframe df_infotec con las listas ordenadas por precio en soles
    df_infotec = pd.DataFrame({'imagen':images, 'nombre':names, 'precio_soles':prices_soles, 'precio_dolares':price_dolares, 'link':links, 'stock':stocks})
    df_infotec = df_infotec.sort_values(by='precio_soles')
    df_infotec = df_infotec.reset_index(drop=True)
    #convertir la columna nombre a string
    df_infotec['nombre'] = df_infotec['nombre'].astype(str)
    df_infotec = df_infotec.sort_values(by='precio_soles')
    df_infotec = df_infotec.reset_index(drop=True)
    #tomar el tiempo de ejecucion
    end_time = time.time()
    print('Infotec acabado en {} segundos'.format(end_time-start_time))

def get_info_products_cc_computer(products):
    #crear listas de imagen, nombre, precio en dolares, precio en soles, link y stock
    image_list = []
    name_list = []
    price_list_soles = []
    price_list_dolares = []
    link_list = []
    stock_list = []
    #recorrer todos los productos
    for product in products:
        description = product.find('div', class_='laber-product-description')
        #obtener imagen
        image = product.find('div', class_='laberProduct-image')
        image = image.find('img')
        image = image['src']
        #si no hay imagen, rellenar con None
        if image == '':
             image = None
        #obtener el stock para evitar procesar productos sin stock class="product-quantities manufacturer_name"
        stock = description.find('div', class_='product-quantities manufacturer_name')
        #si no hay stock, saltar al siguiente producto
        if stock is None:
            continue
        #obtener solo los numeros del stock
        stock = stock.text
        stock = clean_stock(stock)
        if stock == 0:
            continue
        #obtener nombre en h2 con clase productName
        name = description.find('h2', class_='productName')
        name = name.find('a')
        #obtener el link del producto del href del nombre
        link = name['href']
        name = name.text
        #buscar 'laber-product-price-and-shipping' o 'laber-product-price-and-shipping '
        price = product.find('div', class_='laber-product-price-and-shipping')
        #hay 2 etiquetas span con clase price, la primera es el precio en soles y la segunda es el precio en dolares
        price = price.find_all('span', class_='price')
        #obtener el precio en soles
        price_dolares = price[0]
        price_dolares = price_dolares.text
        # #eliminar el simbolo de soles
        price_dolares = clean_price_dollars(price_dolares)
        price_soles = price[1]
        price_soles = price_soles.text
        # #eliminar el simbolo de dolares
        price_soles = clean_price_soles(price_soles)
        #convertir los precios a float
        #agregar a las listas
        image_list.append(image)
        name_list.append(name)
        price_list_soles.append(price_soles)
        price_list_dolares.append(price_dolares)
        link_list.append(link)
        stock_list.append(stock)
    return image_list, name_list, price_list_dolares,  price_list_soles, link_list, stock_list
def get_prices_cc_computer(producto):
    global df_cccomputer
    #reemplazar espacios en blanco por %20
    producto = producto.replace(' ', '+')
    #definir url de busqueda
    url = 'https://cyccomputer.pe/busqueda?controller=search&orderby=position&orderway=desc&search_category=all&s={}'.format(producto)
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
    #buscar un nav con la clase pagination 
    pagination = soup.find('nav', class_='pagination')
    if pagination is None:
        #retornar un dataframe vacio
        df_cc_computer = pd.DataFrame({'imagen':images, 'nombre':names, 'precio_soles':prices_soles, 'precio_dolares':price_dolares, 'link':links, 'stock':stocks})
        print('No hay resultados para {}'.format(producto))
        return df_cc_computer
    #buscar ul nav-links
    pages_ul = pagination.find('ul', class_='page-list')
    #buscar li
    li = pages_ul.find_all('li')
    #ver cuantos elementos hay en la lista
    if len(li) == 1 or pagination is None:
        pages = 1
    else:
        pages = pages_ul.find_all('li')
        #si no hay paginas, solo hay un elemento
        #obtener el numero de paginas en el penultimo elemento
        pages = pages[-2].text
        pages = int(pages)
    #si hay mas de una pagina el url cambia
    if pages > 1:
        pages_url_list = []
        #guardar el url de cada pagina en una lista
        for page in range(1, pages+1):
            pages_url_list.append('https://cyccomputer.pe/busqueda?controller=search&orderby=position&orderway=desc&search_category=all&s={}&page={}'.format(producto, page))
        with concurrent.futures.ThreadPoolExecutor() as executor:
          html = executor.map(get_html_pags, pages_url_list)
        for codigo in html:
            #parsear html
            soup = BeautifulSoup(codigo, 'html.parser')
            products = soup.find_all('article', class_='product-miniature')
            #obtener informacion de los productos
            image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_cc_computer(products)
            # agregar a las listas
            images.extend(image_list)
            names.extend(name_list)
            prices_soles.extend(price_list_soles)
            links.extend(link_list)
            stocks.extend(stock_list)
            price_dolares.extend(price_list_dolares)
    else:
        #capturar todos los productos
        products = soup.find_all('div', class_='item-inner')
        #obtener informacion de los productos
        image_list, name_list, price_list_dolares, price_list_soles, link_list, stock_list = get_info_products_cc_computer(products)
        #agregar a las listas
        images.extend(image_list)
        names.extend(name_list)
        prices_soles.extend(price_list_soles)
        links.extend(link_list)
        stocks.extend(stock_list)
        price_dolares.extend(price_list_dolares)
    #guardar en dataframe df_infotec con las listas ordenadas por precio en soles
    df_cccomputer = pd.DataFrame({'imagen':images, 'nombre':names, 'precio_soles':prices_soles, 'precio_dolares':price_dolares, 'link':links, 'stock':stocks})
    df_cccomputer = df_cccomputer.sort_values(by='precio_soles')
    df_cccomputer = df_cccomputer.reset_index(drop=True)
    #convertir la columna nombre a string
    df_cccomputer['nombre'] = df_cccomputer['nombre'].astype(str)
    print('CyC computer acabado')


#eliminar productos que no tengan el nombre del producto buscado
def filter_products(df, producto):
    #convertir a minuscula
    producto_lower = producto.lower()
    #hacer una regex para buscar el producto
    regex = re.compile(producto_lower)
    #crear una lista de indices
    indices = []
    #iterar sobre el dataframe
    for index, row in df.iterrows():
        #buscar el producto en el nombre
        if regex.search(row['nombre'].lower()):
            indices.append(index)
    #crear un nuevo dataframe con los indices
    df_new = df.iloc[indices]
    df_new = df_new.reset_index(drop=True)
    #guardar en un csv
    df_new.to_csv('productos filtrados.csv')
    return df_new

#crear un mejor filtro para los productos
def filter_products2(df, producto):
    #convertir a minuscula
    producto_lower = producto.lower()
    #si es que el producto esta compuesto de mas de una palabra
    #asegurarse de que cada palabra aparezca al menos una vez en el nombre
    #sin importar si estan juntas o no
    if len(producto_lower.split()) > 1:
        #crear una lista de palabras
        palabras = producto_lower.split()
        #crear una lista de indices
        indices = []
        #iterar sobre el dataframe
        for index, row in df.iterrows():
            #crear una lista de palabras del nombre del producto
            palabras_nombre = row['nombre'].lower().split()
            #crear una lista de palabras que no estan en el nombre
            palabras_faltantes = [palabra for palabra in palabras if palabra not in palabras_nombre]
            #si la lista esta vacia, significa que todas las palabras estan en el nombre
            if len(palabras_faltantes) == 0:
                indices.append(index)
        #crear un nuevo dataframe con los indices
        df_new = df.iloc[indices]
        df_new = df_new.reset_index(drop=True)
        #guardar en un csv
        return df_new
    else:
        #si es que el producto solo tiene una palabra
        #crear una lista de indices
        indices = []
        #iterar sobre el dataframe
        for index, row in df.iterrows():
            #buscar el producto en el nombre
            if producto_lower in row['nombre'].lower():
                indices.append(index)
        #crear un nuevo dataframe con los indices
        df_new = df.iloc[indices]
        df_new = df_new.reset_index(drop=True)
        return df_new






st.title('Comparador de precios de componentes de PC')
#recibimos el link de la pagina del usuario
link = st.text_input('Ingrese el producto que desea buscar: ')
#usamos un boton para que el usuario pueda enviar el link
if st.button('Buscar producto'):
    #poner un aviso de espere mientras se hace el request
    with st.spinner(text='Buscando los mejores precios...🕵️🪙🪄'):
        #crear 2 hilos para obtener los precios de los productos
        #hilo 1: sercoplus
        t1 = threading.Thread(target=get_prices_Sercoplus, args=(link,))
        #hilo 2: infotec
        t2 = threading.Thread(target=get_prices_Infotec, args=(link,))
        #hilo 3: cc computer
        t3 = threading.Thread(target=get_prices_cc_computer, args=(link,))
        #iniciar los hilos
        t1.start()
        t2.start()
        t3.start()
        #esperar a que los hilos terminen
        t1.join()
        t2.join()
        t3.join()
        st.success('Mejores Precios encontrados!🪙🪄')
        #crear un dataframe con los precios de los productos
        #comparemos los precios en soles de los dos dataframes
        # #guardar los precios en un csv
        # df_sercoplus.to_csv('precios_sercoplus.csv', index=False)
        # df_infotec.to_csv('precios_infotec.csv', index=False)
        # df_cccomputer.to_csv('precios_cccomputer.csv', index=False)
        # #filtrar los productos que no tengan el nombre del producto buscado
        # df_sercoplus = filter_products2(df_sercoplus, link)
        df_infotec_filter = filter_products2(df_infotec, link)
        # df_cccomputer = filter_products2(df_cccomputer,link)
        #redondear precio en soles y dolares a 2 decimales de sercoplus
        df_sercoplus['precio_dolares'] = df_sercoplus['precio_dolares'].round(2)
        df_sercoplus['precio_soles'] = df_sercoplus['precio_soles'].round(2)
        #redondear precio en soles y dolares a 2 decimales de infotec
        df_infotec_filter['precio_dolares'] = df_infotec_filter['precio_dolares'].round(2)
        df_infotec_filter['precio_soles'] = df_infotec_filter['precio_soles'].round(2)
    #hacer una grilla de 3 columnas
    col1, col2 , col3 = st.columns(3)
    #colocar el dataframe de sercoplus en la columna 1
    with col1:
        st.image('sercoplus_logo.jpg')
        st.subheader('Sercoplus')
        if len(df_sercoplus) == 0:
            st.write('😢 No se encontro el producto en Sercoplus')
        #escribir el nombre del primer producto en el dataframe
        for i in range(len(df_sercoplus)):
            st.write(df_sercoplus['nombre'][i])
            #si es que no hay el indice de la imagen, entonces no mostrar la imagen
            if df_sercoplus['imagen'][i] is None:
                st.image(not_found_img)
            else:
                st.image(df_sercoplus['imagen'][i])
            st.write('Precio en soles: ', df_sercoplus['precio_soles'][i])
            st.write('Precio en dolares: ', df_sercoplus['precio_dolares'][i])
            #escribir el stock del primer producto en el dataframe
            st.write('Stock: ', df_sercoplus['stock'][i])
            #link acortado
            link = '[Ir al producto](' + df_sercoplus['link'][i] + ')'
            st.markdown(link)
            #escribir una linea horizontal
            st.write('---------------------------------------')
            #si i es igual a 4, entonces guardar los datos en un desplegable
            if i == 4:
                #crear un desplegable para mostrar los productos
                with st.expander('Ver más productos de Sercoplus'):
                    #escribir el nombre del primer producto en el dataframe
                    for j in range(i+1, len(df_sercoplus)):
                        st.write(df_sercoplus['nombre'][j])
                        if df_sercoplus['imagen'][j] is None:
                            st.image(not_found_img)
                        else:
                            st.image(df_sercoplus['imagen'][j])
                        st.write('Precio en soles: ', df_sercoplus['precio_soles'][j])
                        st.write('Precio en dolares: ', df_sercoplus['precio_dolares'][j])
                        #escribir el stock del primer producto en el dataframe
                        st.write('Stock: ', df_sercoplus['stock'][j])
                        #link acortado
                        link = '[Ir al producto](' + df_sercoplus['link'][j] + ')'
                        st.markdown(link)
                        #escribir una linea horizontal
                        st.write('---------------------------------------')
                break

                
    #colocar el dataframe de infotec en la columna 2
    with col2:
        st.image('infotec_logo.jpg')
        st.subheader('Infotec')
        if len(df_infotec_filter) == 0:
            st.write('😢 No se encontro el producto en Infotec')
        for i in range(len(df_infotec_filter)):
            st.write(df_infotec_filter['nombre'][i])
            #si imagen es none, entonces mostrar una imagen por defecto
            if df_infotec_filter['imagen'][i] is None:
                st.image(not_found_img)
            else:
                st.image(df_infotec_filter['imagen'][i])
            #escribir el precio en soles y dolares del primer producto en el dataframe
            st.write('Precio en soles: ', df_infotec_filter['precio_soles'][i])
            st.write('Precio en dolares: ', df_infotec_filter['precio_dolares'][i])
            #escribir el stock del primer producto en el dataframe
            st.write('Stock: ', df_infotec_filter['stock'][i])
            #link acortado
            link = '[Ir al producto](' + df_infotec_filter['link'][i] + ')'
            st.markdown(link)
            #escribir una linea horizontal
            st.write('---------------------------------------')
            #si i es igual a 4, entonces guardar los datos en un desplegable
            if i == 4:
                #crear un desplegable
                with st.expander('Ver más productos de Infotec'):
                    for j in range(i+1, len(df_infotec_filter)):
                        #escribir el precio en soles y dolares del primer producto en el dataframe si el precio esta entre el rango de precio
                        st.write(df_infotec_filter['nombre'][j])
                        if df_infotec_filter['imagen'][j] is None:
                            st.image(not_found_img)
                        else:
                            st.image(df_infotec_filter['imagen'][j])
                        st.write('Precio en soles: ', df_infotec_filter['precio_soles'][j])
                        st.write('Precio en dolares: ', df_infotec_filter['precio_dolares'][j])
                        #escribir el stock del primer producto en el dataframe
                        st.write('Stock: ', df_infotec_filter['stock'][j])
                        #link acortado
                        link = '[Ir al producto](' + df_infotec_filter['link'][j] + ')'
                        st.markdown(link)
                        #escribir una linea horizontal
                        st.write('---------------------------------------')
                break
    #colocar el dataframe de cc computer en la columna 3
    with col3:
        st.image('cc_computer_logo.png')
        #dejar espacio en blanco
        #escribir el titulo de la columna
        st.subheader('C&C Computer')
        #si el dataframe esta vacio, entonces mostrar un mensaje
        if len(df_cccomputer) == 0:
            st.write('😢 No se encontro el producto en C&C Computer')
        #escribir el dataframe de cc computer
        for i in range(len(df_cccomputer)):
            st.write(df_cccomputer['nombre'][i])
            #si es que no hay el indice de la imagen, entonces no mostrar la imagen
            if df_cccomputer['imagen'][i] is None:
                st.image(not_found_img)
            else:
                st.image(df_cccomputer['imagen'][i])
            st.write('Precio en soles: ', df_cccomputer['precio_soles'][i])
            st.write('Precio en dolares: ', df_cccomputer['precio_dolares'][i])
            #escribir el stock del primer producto en el dataframe
            st.write('Stock: ', df_cccomputer['stock'][i])
            #link acortado
            link = '[Ir al producto](' + df_cccomputer['link'][i] + ')'
            st.markdown(link)
            #escribir una linea horizontal
            st.write('---------------------------------------')
            #si i es igual a 4, entonces guardar los datos en un desplegable
            if i == 4:
                #escribir un boton para ver mas productos
                with st.expander('Ver mas productos de CyC computer'):
                    #escribir el dataframe de cc computer
                    for j in range(i+1,len(df_cccomputer)):
                        st.write(df_cccomputer['nombre'][j])
                        #si es que no hay el indice de la imagen, entonces no mostrar la imagen
                        if df_cccomputer['imagen'][j] is None:
                            st.image(not_found_img)
                        else:
                            st.image(df_cccomputer['imagen'][j])
                        st.write('Precio en soles: ', df_cccomputer['precio_soles'][j])
                        st.write('Precio en dolares: ', df_cccomputer['precio_dolares'][j])
                        #escribir el stock del primer producto en el dataframe
                        st.write('Stock: ', df_cccomputer['stock'][j])
                        #link acortado
                        link = '[Ir al producto](' + df_cccomputer['link'][j] + ')'
                        st.markdown(link)
                        #escribir una linea horizontal
                        st.write('---------------------------------------')
                break
#hacer un footer
st.write('Hecho por [Kevin Ramos Rivas](https://github.com/KevinRamosRivas) 👨‍💻')











