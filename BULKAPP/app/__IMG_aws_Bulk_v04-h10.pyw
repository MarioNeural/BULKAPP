import os
import re
import json
import textwrap
from tkinter import Y
import xlsxwriter
import xlrd
import csv
import urllib.parse
import requests
import datetime
import shutil
import tkinter as tk
from tkinter import messagebox



ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


class IMG_aws_TAG_Bulk:
    def __init__(self, files):
        self._data = []
        self._name_viewability_matches = []
        self.get_data_from_json(files)
        self._ALL_LIST = []
        error = self.add_to_LIST()

        if error:
            print(error)
            return
        # print(self._ALL_LIST)

        self.DSPs = {
            "TTD": ["TTD", "TTD_ESC"],
            "Rest": ["360", "360_ENC", "RKT", "QCT", "QCT_ESC", "ZEM", "ZEM_ENC", "STACK_ENC", "STACK", "ADF"]
            # "Rest": ["APN", "APN_ENC", "ADF", "360", "360_ENC", "RKT"]
        }

        # create XLSX files
        for dsp in self.DSPs["Rest"]:
            self.create_XLSX(dsp)
        for dsp in self.DSPs["TTD"]:
            self.create_TTD_XLSX(dsp)

        # print info
        print("-----------------\n-----------------")
        print(f"Total amount of tags: {len(self._ALL_LIST)}")
        matches = sum(self._name_viewability_matches)
        print(f"Coincidencias de 'name' en 'viewability': {matches} de {len(self._name_viewability_matches)}")
        print("\nXLSX files have been created successfully!!!\n")


    # get_data_from_json()
    def get_data_from_json(self, files):
        for f_name in files:
            f = open(f"{ROOT_PATH}/INPUT_JSON/{f_name}")
            self._data.append(json.load(f))

    def check_name_in_viewability(self, json_str):
        try:
            data = json.loads(json_str)
            name = data.get('name', '')
            viewability = data.get('viewability', '')
            first_word_name = name.split('-')[0]
            return first_word_name in viewability
        except json.JSONDecodeError:
            print("Error al decodificar el JSON.")
            return False

    # add_to_LIST()
    def add_to_LIST(self):
        for f_data in self._data:
            for item in f_data:
                json_str = json.dumps(item)
                match = self.check_name_in_viewability(json_str)
                self._name_viewability_matches.append(match)

                tcs = item["tcs"]
                sizes = item["sizes"]
                url_param_sep = self.url_param_separator(item)


                 
                for i, s in enumerate(sizes):
                    obj = {}
                    obj["size"] = s
                    width = s.split("x")[0]
                    height = s.split("x")[1]
                    obj["width"] = width
                    obj["height"] = height

                    obj["name"] = item["name"] + '_' + s
                    obj["landing"] = item["landing"]
                    
                    utm_size = item["add_utm_size"] + s if item.get("add_utm_size") else ""

                    if item["type"] == "link":
                        url = self.set_url_or_link(item["url"], tcs, i, "url", url_param_sep, utm_size)
                        creative_route = 'https://ppj05.cdnwebcloud.com/' + \
                        item["aws_path_1"] + s + item["aws_path_2"]
                        if not self.verify_response_code(creative_route):
                            raise ValueError("#Error: url response code is not 200...")
                        obj["url"] = url
                        obj["tag"] = '<a href="${CLICK_URL}' + url + \
                        '" target="_blank"><img src="https://ppj05.cdnwebcloud.com/' + \
                        item["aws_path_1"] + s + item["aws_path_2"] + \
                        '" width="' + width + '" height="' + height + '"/></a>'

                    elif item["type"] == "iframe":
                        link = ""
                        if item.get("link"):
                            link = self.set_url_or_link(item["link"], tcs, i, "link", url_param_sep, utm_size)
                            is_valid, errors = self.url_validate(link.split("&link=")[1])

                        if not is_valid:
                            for error in errors:
                                print(f"Error: {error}")
                            raise ValueError(f"Error: {error}")
                        else:
                            # Tu código para el caso en que la URL sea válida
                            creative_route = 'https://ppj05.cdnwebcloud.com/' + item["aws_path_1"] + s + item["aws_path_2"]
                            if not self.verify_response_code(creative_route):
                                raise ValueError("#Error: El código de respuesta de la URL no es 200")

                        obj["url"] = False
                        obj["tag"] = '<iframe src="https://ppj05.cdnwebcloud.com/' + \
                        item["aws_path_1"] + s + item["aws_path_2"] + \
                        '?n_o_ct=${CLICK_URL}' + link + '" width="' + width + '" height="' + height + \
                        '" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"></iframe>'
                    
                    if item.get("viewability"):
                        try:
                            if item["viewability"]:
                                if not tcs:
                                    raise ValueError("#Error: Can't add viewability without TCs...")
                                
                                view = self.set_url_or_link(item["viewability"], tcs, i, "view")
                                
                                if not self.verify_response_code("http:" + view + ".js"):
                                  raise ValueError("#Error: url response code is not 200...")
                                
                                
                                obj["tag"] += '<script type="text/javascript" src="' + \
                                view + '&n_o_ord=[CACHEBUSTER]"></script>'
                        except Exception as error:
                            return error
                        
                    # if item.get("viewability_2"):
                    #     try:
                    #         if item["viewability_2"]:
                    #             if not tcs:
                    #                 raise ValueError("#Error: Can't add viewability_2 without TCs...")

                    #             view = "https://bucket.cdnwebcloud.com/n_one_vway_v2_TEST-es.js?tc=" + item.get("viewability_2_tcs")[i]
                                
                    #             if not self.verify_response_code(view + ".js"):
                    #               raise ValueError("#Error: url response code is not 200...")
                                
                                
                    #             obj["tag"] += '<script type="text/javascript" src="' + \
                    #             view + '&n_o_ord=[CACHEBUSTER]"></script>'
                    #     except Exception as error:
                    #         return error
                        
                    if item.get("impression_tag"):
                        try:
                            if item["impression_tag"]:

                                view = item.get("impression_tag")
                                
                                obj["tag"] += view

                        except Exception as error:
                            return error
                        
                    if item.get("impression_tag_2"):
                        try:
                            if item["impression_tag_2"]:

                                view = item.get("impression_tag_2")
                                
                                obj["tag"] += view

                        except Exception as error:
                            return error

                    if item.get("impression"):
                        if item["impression"]:
                            obj["tag"] += '<img src="' + item["impression"] + \
                            '[CACHEBUSTER]" width="1" height="1" border="0" style="display:none;" />'

                    # if item.get("cruce"):
                    #     if item["cruce"]:
                    #         obj["tag"] += '<script type="text/javascript" src="' + item["cruce"] + item["crucetc"][i]+ '&cid=3456&size='+ width + 'x' +height +'&cb=ADD-RANDOM-NUMBER-HERE&gdpr=${GDPR}&gdpr_consent=${GDPR_CONSENT_152}" async="async" ></script>'
                            

                    self._ALL_LIST.append(obj)
                    print("-----------")
                    print(obj)
                    self.create_html(self._ALL_LIST)
                    self.create_html_web(self._ALL_LIST)

    # url_param_separator()

    def url_param_separator(self, item):
        if item["tcs"] or item.get("add_utm_size"):
            if item.get("url"):
                href = item["url"]
            elif item.get("link"):
                href = item["link"]

            return "&" if len(href.split("?")) > 1 or href[0:8] != "https://" else "?"
        else:
            return ""

    #Create html file to preview tags        
    def create_html(self, tag):
        with open("app/HTML/test.html", "w") as f:
            f.write("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Document</title>")
            f.write("<style>\n")
            f.write("    body{\n")
            f.write("        margin: 0;\n")
            f.write("        padding: 0;\n")
            f.write("    }\n")
            f.write("    header {\n")
            f.write("        position: sticky;\n")
            f.write("        top: 0;\n")
            f.write("        z-index: 10;\n")
            f.write("        display: flex;\n")
            f.write("        justify-content: center;\n")
            f.write("        align-items: center;\n")
            f.write("        padding: 16px;\n")
            f.write("        background-color: #34534d;\n")
            f.write("        font-family: Poppins,Helvetica,Arial,\"sans-serif\";\n")
            f.write("    }\n")
            f.write("\n")
            f.write("    #logo img {\n")
            f.write("        width: 60px;\n")
            f.write("        height: 60px;\n")
            f.write("    }\n")
            f.write("\n")
            f.write("    p {\n")
            f.write("        font-family: Poppins,Helvetica,Arial,\"sans-serif\";\n")
            f.write("        margin: 40px;\n")
            f.write("        font-size: 16px;\n")
            f.write("    }\n")
            f.write("    .container{\n")
            f.write("        width: auto;\n")
            f.write("        height: auto;\n")
            f.write("        margin: auto;\n")
            f.write("        text-align: center;\n")
            f.write("    }\n")
            f.write("    .row{\n")
            f.write("        border-bottom: 1px solid gray;\n")
            f.write("    }\n")
            f.write("    iframe{\n")
            f.write("        margin-bottom: 60px;\n")
            f.write("    }\n")
            f.write("</style></head>\n")
            f.write("<body><div class=\"container\">")
            f.write("<header>\n")
            f.write("    <div id=\"logo\">\n")
            f.write("        <img src=\"logo-neural.svg\" alt=\"Neural\">\n")
            f.write("    </div>\n")
            f.write("</header>\n")
            for value in tag:
                tag_value = value["tag"]
                tag_name = value["name"]
                f.write(f"<div class=\"row\"><p>{tag_name}</p>{tag_value}</div>")
            f.write("</div></body>")
            f.write("</html>")
            f.close()


    #Create html web prototype

    def create_html_web(self, tag):
        with open("app/HTML/test_web.html", "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Document</title>")
             # Estilo CSS
            css_style = '''
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    background-color: #d8d8d8;
                    color:#29475b
                }
        
                header {
                    position: fixed;
                    width: 100%;
                    top: 0;
                    z-index: 10;
                    padding: 20px;
                    display: flex;
                    justify-content: space-evenly;
                    align-items: center;
                    background-color: #ffffff;
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                }
                .left-section,
                .right-section {
                    display: flex;
                }
                
                .left-section ul,
                .right-section ul {
                    list-style: none;
                    display: flex;
                    padding: 0;
                    margin: 0;
                }
                
                .left-section li,
                .right-section li {
                    margin-right: 20px;
                }
                nav{
                    align-items: center;
                }
                
                nav a {
                    text-decoration: none;
                    color: #29475b;
                }
                
                .logo {
                    font-size: 24px;
                    text-align: center;
                }
                
                /* Cambiar el estilo de los enlaces al pasar el mouse */
                nav a:hover {
                    text-decoration: underline;
                }
 
                #logo img {
                    width: 40px;
                    height: 40px;
                }
        
                p {
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                    font-size: 20px;
                }
        
                h4 {
                    margin: 0;
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                    text-align: left;
                }
        
                .title {
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                    margin: 0px 40px 60px 40px;
                    font-size: 22px;
                    font-weight: bold;
                }
        
                .container {
                    width: auto;
                    height: auto;
                    margin: auto;
                    text-align: center;
                    position: relative;
                }
        
                .row {
                    width: 890px;
                    justify-content: center;
                    margin: auto;
                    padding: 40px;
                    background-color: #ffffff;
                }
        
                .main {
                    display: flex;
                    flex-direction: row;
                    text-align: left;
                    width: 100%;
                    font-size: 40px !important;
                    padding-bottom: 40px;
                }
        
                .parrafo {
                    margin-top: 40px;
                }
        
                .text {
                    font-weight: 200;
                    font-size: 16px;
                }
        
                .img-noticia {
                    width: 100%;
                }
        
                .img-sticky {
                    position: sticky;
                    top: 80px;
                    /* margin-left: 20px; */
                }
        
                hr {
                    margin-bottom: 15px;
                }
        
                .caja-970x250 {
                    display: contents;
                }
        
                .caja-noticia {
                    width: 100%;
                    display: grid;
                    justify-content: center;
                    padding: 0 20px;
                    height: 100%;
                    border-left: 1px solid gray;
                    border-right: 1px solid gray;
                }
        
                .caja-flex {
                    display: flex;
                }
        
                .img-publi {
                    width: auto;
                    height: 100%;
                    position: sticky;
                    text-align: center;
                }
        
                #publi-1 {
                    margin-top: 20px;
                    display: flex;
                    width: 100%;
                    justify-content: center;
        
                }
                footer {
                    background-color:#d8d8d8;
                    color: #29475b;
                    display: flex;
                    justify-content: space-evenly;
                    align-items: center;
                    padding: 50px 10px;
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                }
                
                .footer-section {
                    display: flex;
                    align-items: center;
                    text-align: left;
                    font-family: Poppins, Helvetica, Arial, "sans-serif";
                }
                
                .vertical-menu a {
                    text-decoration: none;
                    color: #29475b;
                    display: block;
                    margin: 10px 0;
                }
                .publi{
                    font-size: 9px;
                    font-family: Poppins, Helvetica, Arial, "sans-serif";

                }

                @media (max-width: 1300px) {
                body{
                transform:scale(0.8)
                }
                }
            </style>
            '''

            img_src_300x600 = ''
            img_src_970x250 = ''
            img_src_160x600 = ''
            img_src_300x250 = ''
            img_src_320x100 = ''
            img_src_728x90 = ''

            for value in tag:
                tag_value = value["tag"]
                # tag_name = value["name"]

                if "300x600" in tag_value:
                    img_src_300x600 = tag_value

                elif "970x250" in tag_value:
                    img_src_970x250 = tag_value

                elif "160x600" in tag_value:
                    img_src_160x600 = tag_value

                elif "300x250" in tag_value:
                    img_src_300x250 = tag_value

                elif "320x100" in tag_value:
                    img_src_320x100 = tag_value

                elif "728x90" in tag_value:
                    img_src_728x90 = tag_value

            f.write(css_style)
            f.write("</div></body>")
            f.write(f'''
                    </head>
                    <body>
                <div class="container">
                <header>
                    <nav class="left-section">
                        <ul>
                            <li><a href="#">Accounts</a></li>
                            <li><a href="#">Traffickers</a></li>
                            <li><a href="#">Campaigns</a></li>
                        </ul>
                    </nav>
                    <div class="logo">
                        <img src="logo_web.png" alt="Neural">
                    </div>
                    <nav class="right-section">
                        <ul>
                            <li><a href="#">Developers</a></li>
                            <li><a href="#">Graphic Designers</a></li>
                            <li><a href="#">Data</a></li>
                        </ul>
                    </nav>
                </header>
            <div style="justify-content: center;display: flex;">
            <div style="position: absolute;max-width: 1410px;min-width: 1410px; top: 94px;margin: auto;">
                <div class="img-publi" style="float: left;  margin: 1.9vw 1vw;">{img_src_160x600}</div>
                <div class="img-publi" style="float: right; margin: 1.9vw 1vw;">{img_src_160x600}</div>
                <div>
                    <div style="margin: 1vw;position: relative;"><p class="publi">PUBLICIDAD</p>{img_src_970x250}</div>
                </div>
                <div class="row">
                    <div class="main">
                        <div class="caja-noticia">
                            <h4>Creatividades dinámicas en el ecosistema digital</h4>
                            <p class="text">Han pasado más de tres años desde que Google Chrome manifestó por primera vez su intención de bloquear el uso de cookies de terceros. Aunque Chrome no ha cumplido con los plazos iniciales, pronto lo hará y se sumará a la cada vez más larga lista de navegadores que sólo permiten el uso de cookies propias. Por ese motivo, desde Neural.ONE llevamos trabajando más de año y medio en una tecnología que nos permita trabajar con los feeds de cliente de la manera más óptima posible para poder impactar a los usuarios en base a sus gustos y preferencias sin la necesidad de utilizar cookies de terceros.</p>
                            <p class="text">Para conseguirlo, hemos tenido que enfrentarnos a cuatro grandes retos. El primero es el volumen de los feeds de producto. Gracias a nuestra experiencia previa manejando millones de datos en nuestro modelo de atribución, conseguimos aplicar las últimas tecnologías en Big Data. Con ellas podemos tratar en una sola campaña feeds de hasta 30.000 productos distintos, con la capacidad de actualizarlos cada hora. Esto permite a nuestros clientes tener siempre actualizadas sus DCO (Dynamic Creative Optimization) frente a cambios de precio, stock, url, etc.</p>
                            <img class="img-noticia" src="./img/img_1280x853.jpg">
                            <p class="text">Un segundo reto ha sido la personalización del anuncio. Para poder determinar cuáles son los productos más relevantes para los usuarios, analizamos más de una decena de métricas, entre las que destacan el número de visitas por producto y las interacciones realizadas. Alimentamos a nuestro algoritmo con toda esta información y determinamos cuales son los productos más relevantes para cada usuario. Para explicar este punto podemos tomar de referencia un e-commerce de ropa en el que un cliente ha visto 5 productos distintos, gracias a nuestro algoritmo, podemos saber cuánto tiempo ha pasado interactuando el usuario con cada uno de ellos, lo que le permitirá adelantarnos a la demanda del cliente y ofrecerle en las siguientes creatividades aquellos artículos que más le ha interesado.</p>
                                <div style="margin:auto">{img_src_320x100}</div>
      
                        </div>
                        <div class="img-sticky img-publi" style="margin-left: 1.1vw;"><p class="publi">PUBLICIDAD</p>{img_src_300x600}</div>
                    </div>
                    <hr>
                    <div class="main">
                        <div class="caja-noticia">
                            <h4>Las nuevas tendencias digitales en el forum digital</h4>
                            <p class="text">Las nuevas tendencias digitales sobre publicidad se han dado cita esta mañana en el forum digital celebrado por Neural One, con el que las compañías ha querido inaugurar sus nuevas oficinas, que cuentan con un espacio habilitado en el que celebrarán de forma habitual forums y cursos de formación interna.</p>
                            <p class="text">Por otro lado, ha aseverado que «a día de hoy somos capaces de mostrar una casa a través de visitas virtuales en las que además se pueden ver las casas decoradas«, todo un paso para las inmobiliarias de la banca, que normalmente ofrecen pisos vacíos. Además, «podemos mostrar la zona gracias a planos que hemos sacado con drones», ha puntualizado, lo que ofrece a los usuarios una experiencia más completa.</p>
                            <img class="img-noticia" src="./img/img_1280x853.jpg">
                            <p class="text">Entre las mejoras que han implementado en el grupo, la directora de Marketing Digital de la compañía ha subrayado la posibilidad de lanzar la búsqueda colocando como un punto de partida la ubicación actual del usuario o las funcionalidades en el mapa.</p>

                        </div>
                        <div style="display: grid;">
                            <div>
                                <div style="margin-left: 20px;" class="img-sticky">{img_src_300x250}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="width: 100%;">
                    <div class="img-publi" style="margin: 20px auto;justify-content: center;display: flex;">{img_src_728x90}</div>
                </div>
                <footer>
                    <div class="footer-section">
                        <div class="vertical-menu">
                            <a href="#">Contacto</a>
                            <a href="#">Aviso Legal</a>
                            <a href="#">Política de Privacidad</a>
                            <a href="#">Política de Cookies</a>
                        </div>
                    </div>
                    <div class="footer-section">
                        <a href="https://www.linkedin.com/company/adgmediagroup/" target="_blank">
                            <img src="logo-linkedin.png" alt="LinkedIn Logo">
                        </a>
                    </div>
                </footer>
            </div>
                ''')
            f.write("</html>")
            f.close()
            
    # Validate URL
    def url_validate(self, url):
        errors = []

        # Valida que la URL empiece por "https://"
        if not re.match(r'^https://', url):
            errors.append("The URL does not start with 'https://'")

        # Valida que la URL no tenga espacios
        if re.search(r'\s', url):
            errors.append("URL contains whitespaces")

        # Valida que la URL no contenga el carácter #
        if '#' in url:
            errors.append("The URL contains the character ('#')")

        # Valida que la URL tenga 0 o 1 interrogaciones
        # if not re.match(r'^[^\?]*(\?[^\?]*){0,1}$', url):
        #     errors.append("The URL contains more than one question mark ('?')")

        # Valida que la URL no tenga dos "&" juntos
        if re.search(r'&{2}', url):
            errors.append("The URL contains two consecutive '&'")

        # Si se encontraron errores, devuelve un mensaje de error
        if errors:
            return False, errors

        # Si la URL cumple con todas las condiciones, se considera válida
        return True, []
    

    #verify_response_code()
    def verify_response_code(self, url):
        error_code = {
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        404: "Page Not Found",
        403: "Viewability errónea / No exiten uno o más tc's / No está publicado en S3",
        405: "Method Not Allowed",
        406: "No Such",
        407: "No Such Model",
        408: "Request Timeout",
        409: "Conflicto",
        410: "File Delete",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Request Entity Too Large",
        414: "Request-URI Too Large",
        415: "Unsupported Media Type",
        416: "Rango No Satisfecho",
        417: "Expectation Failed",
        418: "El servidor se rehusa a preparar café porque es una tetera",
        421: "Misdirect request",
        422: "Crash - Block Machine",
        423: "Locked",
        424: "Microsoft Learn",
        425: "Too Fast",
        426: "Upgrade Required",
        428: "Precondition Required",
        429: "Too Many Requests",
        431: "Request Header Fields Too Large",
        451: "Unavailable For Legal Reasons",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
        505: "HTTP Version Not Supported",
        506: "Variant Also Negotiates",
        507: "Insufficient Storage",
        508: "Loop Detected)",
        510: "Not Extended",
        511: "Network Authentication Required",
        
    }
        
        if "globales.com" in url:
            error_code[403] = "Desactivado para globales.com"
        else:
            error_code[403] = "No esta actualizado/publicado/encontrado en s3"

        try:
            response = requests.get(url)
            if response.status_code in error_code:
                error_description = error_code[response.status_code]
                raise ValueError(f"Error Servidor => {response.status_code}: {error_description}")
            else:
                return True
        except requests.exceptions.RequestException as e:
            print('sdfdsfdsfs')
            raise ValueError("La URL no existe o no está activa")

    # set_url_or_link()
    def set_url_or_link(self, href, tcs, i, type, url_param_sep="", utm_size=""):
        if (len(tcs) >= 1):
            tc = str(tcs[i])
            tch10 = str(tcs[i])
        elif (len(tcs) > 0):
            tc = str(tcs[0])
        else:
            tc = ""
   
        
        if type == "link" and href.lower() == "only_tc":
            return '&link=' + tc
        elif type == "view":
            return href + url_param_sep + utm_size + tc
        else:
            tc_param = "tc_alt=" if tc else ""
            tc = tc_param + tc
            if utm_size and tc:
                utm_size += "&"
            param = '&link=' if type == "link" else ""

            return param + 'https://neural15.cdnwebcloud.com/atc?tc=' + tch10 + '&n_o_p=v1mp&n_o_ord=&[CACHEBUSTER]&url_n_o=' + href + url_param_sep + utm_size + tc


    # cache_and_clicktag()
    def cache_and_clicktag(self, tag, dsp, url):
        Patt_Click = "${CLICK_URL}"
        Patt_Cache = "[CACHEBUSTER]"
        Valid_Patts = {
            "360_ENC"  : {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL_ENC}"},
            "TTD_ESC"  : {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK_ESC%%"},
            "ZEM_ENC"  : {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL_ENC}"},
            "QCT_ESC"  : {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICKESC}"},
            "STACK_ENC": {"CB": r"[CACHEBUSTER]", "Clk": r"{SA_CLICK_URL_ENC}"},
            "ADF": {"CB": r"%%ADFRND%%", "Clk": r"%%c1;cpdir="},

            "360"  : {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL}"},
            "TTD"  : {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK%%"},
            "RKT"  : {"CB": r"{timestamp}", "Clk": r"{scriptclickprefix}"},
            "QCT"  : {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICK}"},
            "ZEM"  : {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL}"},
            "STACK": {"CB": r"[CACHEBUSTER]", "Clk": r"{SA_CLICK_URL}"},

            # "APN_ENC": {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL_ENC}"},
            # "APN": {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL}"},
            # "ADF": {"CB": r"%%ADFRND%%", "Clk": r"%%c1;cpdir="}
        }
        if Patt_Click in tag:
            tag = tag.replace(Patt_Click, Valid_Patts[dsp]["Clk"])

        if Patt_Cache in tag:
            tag = tag.replace(Patt_Cache, Valid_Patts[dsp]["CB"])

        if dsp == "ADF" and url:
            url_enc = urllib.parse.quote(url)
            tag = tag.replace(url, url_enc)

        return tag

    # create_TTD_XLSX()
    def create_TTD_XLSX(self, DSP):
        templ_wb = xlrd.open_workbook(
            f'{ROOT_PATH}/_Template_TTD(dont_delete).xlsx')
        new_wb = xlsxwriter.Workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')

        for name in templ_wb.sheet_names():
            sh = templ_wb.sheet_by_name(name)
            new_sh = new_wb.add_worksheet(name)
            row = 0
            col = 0

            for x in range(sh.nrows):
                for y in range(sh.ncols):
                    new_sh.write(row, col, sh.cell_value(x, y))
                    col += 1
                col = 0
                row += 1

            if new_sh.name == "Third Party Display":
                ws = new_sh  # set the sheet to pass as a param

        order = ["name", "_blank", "width", "height", "tag",
                 "landing", "_blank", "_blank", "_blank", "_secure"]
        missing_content = {"_blank": "", "_secure": "yes", }
        # write_XLSX
        self.write_XLSX(DSP, row, new_wb, ws, order, missing_content)

    # create_XLSX()
    def create_XLSX(self, DSP):
        wb = xlsxwriter.Workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')
        ws = wb.add_worksheet()
        row = 0
        col = 0
        missing_content = {"_blank": ""}
        if DSP == 'RKT':
            labels = ['Placement Name', 'Ad Tag', 'Width', 'Height',
                      'Start Date', 'End Date', 'Landing Page Url']
            order = ['name', 'tag', 'width', 'height',
                     "Start Date", "End Date", "landing"]
            missing_content = {"Start Date": "", "End Date": ""}
        elif DSP == '360' or DSP == '360_ENC' or DSP == 'QCT' or DSP == 'QCT_ESC':
            labels = ['Creative name', 'Dimensions (width x height)', 'Third-party tag', 'Landing page URL', 'Expanding direction', 'Expands on hover ("Yes" or "No")', 'Requires HTML5 ("Yes" or "No")',
                      'Requires MRAID ("Yes" or "No")', 'Requires ping for attribution ("Yes" or "No")', 'Integration code (Optional)', 'Notes (Optional)']
            order = ["name", "size", "tag", "landing",
                     "exp_dir", "exp_hover", "html", "mraid", "ping"]
            missing_content = {"exp_dir": "","exp_hover": "No", "html": "Yes", "mraid": "No", "ping": "No"}
        elif DSP == 'ZEM' or DSP == 'ZEM_ENC':
            labels = ['URL', 'Title', 'Display URL', 'Ad tag', 'Ad tag width', 'Ad tag height']
            order = ['landing', 'name', 'landing', 'tag', 'width', 'height']
        elif DSP == 'STACK' or DSP == 'STACK_ENC':
            labels = ['Campaign Id', 'Campaign Name (Read only)','Creative Id', 'Image File', 'Creative Name', 'JS Code / HTML', 'Dimension (Image File - Read only)', 'Dimension (JS Code)', 'Is expandable (JS Code)', 'Click URL', 'Sponsored By', 'Impression Tracking URLs']
            order = ['campaign_id', 'campaign_name', 'creative_id', 'image_file', 'name', 'tag', 'dimension_image', 'size', 'is_expandable', 'landing', 'sponsored_by', 'landing']
            missing_content = {'campaign_id':'', 'campaign_name':'', 'creative_id':'', 'image_file': '', 'dimension_image': '', 'is_expandable': '', 'sponsored_by': 'none'}
        elif DSP == 'ADF':
            labels = ['Name', 'Click URL', 'Content', 'Size']
            order = ['name', '_blank', 'tag', 'size']

        # elif DSP == 'APN' or DSP == 'APN_ENC':
        #     labels = ['File Name', 'Size', 'Tag Content']
        #     order = ['name', 'size', 'tag']
        # elif DSP == 'ADF':
        #     labels = ['Name', 'Click URL', 'Content', 'Size']
        #     order = ['name', '_blank', 'tag', 'size']
        # create title row
        for i in labels:
            ws.write(row, col, i)
            col += 1
        col = 0
        row += 4 if "APN" in DSP else 1  # ADF 15
        # write_XLSX
        self.write_XLSX(DSP, row, wb, ws, order, missing_content)

    # write_XLSX()
    def write_XLSX(self, DSP, row, wb, ws, order, missing_content):
        row = row
        col = 0
        # add data to file
        for item in self._ALL_LIST:

            for k in order:
                key_exists = item.get(k)
                # ...if the key exists in the dict (most cases)
                if key_exists:
                    # change cachebuster and clicktag
                    if k == "tag":
                        temp = self.cache_and_clicktag(
                            item[k], DSP, item["url"])
                        ws.write(row, col, temp)
                    else:
                        ws.write(row, col, item[k])
                # ...key doesn't exist (for 360)
                else:
                    ws.write(row, col, missing_content[k])
                col += 1
            col = 0
            row += 1

        # only show missing clicktags the fist time cache_and_clicktag() runs
        self._missing_clktags_printed = True
        wb.close()
        # create CSV file
        if "360" in DSP or DSP == "QCT":
            self.create_CSV(DSP)

    # create_CSV()
    def create_CSV(self, DSP):
        wb = xlrd.open_workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')
        sh = wb.sheet_by_name('Sheet1')

        csv_file = open(f'{ROOT_PATH}/{DSP}_file.csv', 'w', newline='')
        wr = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        for rownum in range(sh.nrows):
            wr.writerow(sh.row_values(rownum))

        csv_file.close()
        # delete .xlsx after creating .csv
        os.remove(f'{ROOT_PATH}/{DSP}_file.xlsx')

# --------- end of IMG_aws_TAG_Bulk() --------


# ask_to_run_code()
def ask_to_run_code():
    q = input('JSON is ready and you want to RUN the script? Y/N\n')
    if q.lower() != "y" and q.lower() != "n":
        print(f'Invalid command "{q}", try again')
        q = ask_to_run_code()
    return q

INPUT_JSON_PATH = os.path.join(ROOT_PATH, "INPUT_JSON")

# Backup function
def backup_json(file_name, aws_path_1):
    folder_name = aws_path_1.split("/")[0]  
    backup_folder = os.path.join(INPUT_JSON_PATH, folder_name)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    today = datetime.date.today()
    base_name = f"input_{today.day}_{today.strftime('%B')}"
    backup_name = base_name + ".json"
    counter = 1

    while os.path.exists(os.path.join(backup_folder, backup_name)):
        backup_name = f"{base_name}({counter}).json"
        counter += 1

    shutil.copy(os.path.join(INPUT_JSON_PATH, file_name), os.path.join(backup_folder, backup_name))

# MAIN()
def on_closing():
    print("Operación cancelada por el usuario.")

def ask_to_run_code():
    root = tk.Tk()
    root.withdraw()
    
    dialog_title = "Confirmación"
    dialog_message = "¿Quieres continuar con los siguientes archivos?"

    for f in sorted(os.listdir(INPUT_JSON_PATH)):
        ext = re.search(r'(.json)', f)
        if ext:
            dialog_message += f"\n- {f}"

    response = messagebox.askyesno(dialog_title, dialog_message)
    
    root.destroy()  # Esto destruirá la instancia de Tk
    if response:
        return "y"
    else:
        return "n"

def main():
    files = []

    # Leer los archivos JSON
    with open(os.path.join(INPUT_JSON_PATH, 'input.json'), 'r') as json_file:
        data = json.load(json_file)

    aws_path_1 = data[0].get('aws_path_1', '')

    # Muestra los archivos en el directorio
    print("-----------")
    print("Files in folder:")
    for f in sorted(os.listdir(INPUT_JSON_PATH)):
        ext = re.search(r'(.json)', f)
        if ext:
            files.append(f)
            print(f"- {f}")
            backup_json(f, aws_path_1)
        else:
            print(f"- ... Extension not recognized on file: {f}")
    print("-----------")

    # Procesamiento principal
    IMG_aws_TAG_Bulk(files)

if __name__ == '__main__':
    main()