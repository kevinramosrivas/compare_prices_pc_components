
#importar librerias para scraping
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
import threading
import matplotlib.pyplot as plt


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
    df_sercoplus = df_sercoplus.sort_values(by='precio_soles')
    df_sercoplus = df_sercoplus.reset_index(drop=True)
    print('Sercoplus acabado')


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
        #gurdar la lista como un dataframe
        df_pages_url = pd.DataFrame({'url': pages_url_list})
        #guardar el dataframe como un csv
        df_pages_url.to_csv('pages_url.csv', index=False)
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
    df_infotec = pd.DataFrame({'imagen':images, 'nombre':names, 'precio_soles':prices_soles, 'precio_dolares':price_dolares, 'link':links, 'stock':stocks})
    df_infotec = df_infotec.sort_values(by='precio_soles')
    df_infotec = df_infotec.reset_index(drop=True)
    #convertir la columna nombre a string
    df_infotec['nombre'] = df_infotec['nombre'].astype(str)
    df_infotec = df_infotec.sort_values(by='precio_soles')
    df_infotec = df_infotec.reset_index(drop=True)
    print('Infotec acabado')



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
        #iniciar los hilos
        t1.start()
        t2.start()
        #esperar a que los hilos terminen
        t1.join()
        t2.join()
        st.success('Precios encontrados!🪙🪄')
        #crear un dataframe con los precios de los productos
        #comparemos los precios en soles de los dos dataframes
        #guardar los precios en un csv
        df_sercoplus.to_csv('precios_sercoplus.csv', index=False)
        df_infotec.to_csv('precios_infotec.csv', index=False)
        # #filtrar los productos que no tengan el nombre del producto buscado
        #df_sercoplus = filter_products(df_sercoplus, link)
        df_infotec_filter = filter_products(df_infotec, link)
        #df_infotec_filter = df_infotec
        #redondear precio en soles y dolares a 2 decimales de sercoplus
        df_sercoplus['precio_dolares'] = df_sercoplus['precio_dolares'].round(2)
        df_sercoplus['precio_soles'] = df_sercoplus['precio_soles'].round(2)
        #redondear precio en soles y dolares a 2 decimales de infotec
        df_infotec_filter['precio_dolares'] = df_infotec_filter['precio_dolares'].round(2)
        df_infotec_filter['precio_soles'] = df_infotec_filter['precio_soles'].round(2)
    #hacer una grilla de 1 fila y 5 columnas
    col1, col2 = st.columns(2)
    #colocar el dataframe de sercoplus en la columna 1
    with col1:
        st.subheader('Sercoplus')
        #escribir el nombre del primer producto en el dataframe
        for i in range(len(df_sercoplus)):
            #escribir el precio en soles y dolares del primer producto en el dataframe si el precio esta entre el rango de precio
            st.write(df_sercoplus['nombre'][i])
            #si es que no hay el indice de la imagen, entonces no mostrar la imagen

            st.image(df_sercoplus['imagen'][i])
            st.write('Precio en soles: ', df_sercoplus['precio_soles'][i])
            st.write('Precio en dolares: ', df_sercoplus['precio_dolares'][i])
            #escribir el link del primer producto en el dataframe
            st.write('Link: ', df_sercoplus['link'][i])
            #escribir el stock del primer producto en el dataframe
            st.write('Stock: ', df_sercoplus['stock'][i])
            #escribir una linea horizontal
            st.write('---------------------------------------')
            #si i es igual a 4, entonces guardar los datos en un desplegable
            if i == 4:
                #crear un desplegable para mostrar los productos
                with st.expander('Ver más productos'):
                    #escribir el nombre del primer producto en el dataframe
                    for j in range(i+1, len(df_sercoplus)):
                        #escribir el precio en soles y dolares del primer producto en el dataframe si el precio esta entre el rango de precio
                        st.write(df_sercoplus['nombre'][j])
                        st.image(df_sercoplus['imagen'][j])
                        st.write('Precio en soles: ', df_sercoplus['precio_soles'][j])
                        st.write('Precio en dolares: ', df_sercoplus['precio_dolares'][j])
                        #escribir el link del primer producto en el dataframe
                        st.write('Link: ', df_sercoplus['link'][j])
                        #escribir el stock del primer producto en el dataframe
                        st.write('Stock: ', df_sercoplus['stock'][j])
                        #escribir una linea horizontal
                        st.write('---------------------------------------')
                break

                
    #colocar el dataframe de infotec en la columna 2
    with col2:
        st.subheader('Infotec')
        for i in range(len(df_infotec_filter)):
            #escribir el precio en soles y dolares del primer producto en el dataframe si el precio esta entre el rango de precio
            st.write(df_infotec_filter['nombre'][i])
            #si imagen es none, entonces mostrar una imagen por defecto
            if df_infotec_filter['imagen'][i] is None:
                st.image('data:image/png;base64,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')
            else:
                st.image(df_infotec_filter['imagen'][i])
            #escribir el precio en soles y dolares del primer producto en el dataframe
            st.write('Precio en soles: ', df_infotec_filter['precio_soles'][i])
            st.write('Precio en dolares: ', df_infotec_filter['precio_dolares'][i])
            #escribir el link del primer producto en el dataframe
            st.write('Link: ', df_infotec_filter['link'][i])
            #escribir el stock del primer producto en el dataframe
            st.write('Stock: ', df_infotec_filter['stock'][i])
            #escribir una linea horizontal
            st.write('---------------------------------------')
            #si i es igual a 4, entonces guardar los datos en un desplegable
            if i == 4:
                #crear un desplegable
                with st.expander('Ver más'):
                    for j in range(i+1, len(df_infotec_filter)):
                        #escribir el precio en soles y dolares del primer producto en el dataframe si el precio esta entre el rango de precio
                        st.write(df_infotec_filter['nombre'][j])
                        if df_infotec_filter['imagen'][j] is None:
                            st.image('data:image/png;base64,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')
                        else:
                            st.image(df_infotec_filter['imagen'][j])
                        st.write('Precio en soles: ', df_infotec_filter['precio_soles'][j])
                        st.write('Precio en dolares: ', df_infotec_filter['precio_dolares'][j])
                        #escribir el link del primer producto en el dataframe
                        st.write('Link: ', df_infotec_filter['link'][j])
                        #escribir el stock del primer producto en el dataframe
                        st.write('Stock: ', df_infotec_filter['stock'][j])
                        #escribir una linea horizontal
                        st.write('---------------------------------------')
                break








