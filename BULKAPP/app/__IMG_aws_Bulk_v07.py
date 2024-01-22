#!/usr/bin/env python3
# Copyright 2009-2017 BHG http://bw.org/


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
import requests


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))


class IMG_aws_TAG_Bulk:
    def __init__(self, files):
        self._data = []

        self.get_data_from_json(files)
        self._ALL_LIST = []
        error = self.add_to_LIST()

        if error:
            print(error)
            return
        # print(self._ALL_LIST)

        self.DSPs = {
            "TTD": ["TTD", "TTD_ESC"],
            "Rest": ["360", "360_ENC", "RKT", "QCT", "QCT_ESC", "ZEM", "ZEM_ENC", "STACK_ENC", "STACK"]
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
        print("\nXLSX files have been created successfully!!!\n")


    # get_data_from_json()
    def get_data_from_json(self, files):
        for f_name in files:
            f = open(f"{ROOT_PATH}/INPUT_JSON/{f_name}")
            self._data.append(json.load(f))

    # add_to_LIST()
    def add_to_LIST(self):
        for f_data in self._data:
            for item in f_data:

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
                                view + '.js?n_o_nu=not&n_o_ord=[CACHEBUSTER]"></script>'
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
        with open("HTML/test.html", "w") as f:
            f.write("<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>Document</title>")
            f.write("<style>\n")
            f.write("    body{\n")
            f.write("        margin: 0;\n")
            f.write("        padding: 0;\n")
            f.write("        background-color: #EFF0E8;\n")
            f.write("    }\n")
            f.write("    header {\n")
            f.write("        position: sticky;\n")
            f.write("        top: 0;\n")
            f.write("        z-index: 10;\n")
            f.write("        padding: 20px;\n")
            f.write("        background-color: #34534d;\n")
            f.write("        font-family: Poppins,Helvetica,Arial,\"sans-serif\";\n")
            f.write("    }\n")
            f.write("    #logo img {\n")
            f.write("        width: 70px;\n")
            f.write("        height: 70px;\n")
            f.write("    }\n")
            f.write("    p {\n")
            f.write("        font-family: Poppins,Helvetica,Arial,\"sans-serif\";\n")
            f.write("        margin: 0px 40px 60px 40px;\n")
            f.write("        font-size: 20px;\n")
            f.write("    }\n")
            f.write("    .title{\n")
            f.write("        font-family: Poppins,Helvetica,Arial,\"sans-serif\";\n")
            f.write("        margin: 0px 40px 60px 40px;\n")
            f.write("        font-size: 22px;\n")
            f.write("        font-weight: bold;\n")
            f.write("    }\n")
            f.write("    .container{\n")
            f.write("        width: auto;\n")
            f.write("        height: auto;\n")
            f.write("        margin: auto;\n")
            f.write("        text-align: center;\n")
            f.write("    }\n")
            f.write("    .row{\n")
            f.write("        width: 920px;\n")
            f.write("        margin: auto;\n")
            f.write("        border-bottom: 1px solid gray;\n")
            f.write("        padding: 40px;\n")
            f.write("        background-color: #ffffff;\n")
            f.write("    }\n")
            f.write("    .main{\n")
            f.write("        display: flex;\n")
            f.write("        flex-direction: row;\n")
            f.write("        text-align: left;\n")
            f.write("        font-size: 40px !important;\n")
            f.write("    }\n")
            f.write("    .vertical-text {\n")
            f.write("        flex-direction: column !important;\n")
            f.write("        align-items: center;\n")
            f.write("    }\n")
            f.write("    .parrafo {\n")
            f.write("        margin-top: 40px;\n")
            f.write("    }\n")
            f.write("    .text{\n")
            f.write("        font-weight: 200;\n")
            f.write("    }\n")
            f.write("</style></head>\n")
            f.write("<body><div class=\"container\"><header>\n")
            f.write("    <a href=\"https://login.neural.one/\" target=\"_blank\">\n")
            f.write("    <div id=\"logo\">\n")
            f.write("        <img src=\"logo-neural.svg\" alt=\"Neural\">\n")
            f.write("    </div>  \n")
            f.write("    </a>\n")
            f.write("</header>\n")

            # Insertar el contenido de las etiquetas <div class="row"> aquí
            for value in tag:
                tag_value = value["tag"]
                tag_name = value["name"]
                f.write(f"<div class=\"row\"><p class=\"title\">{tag_name}</p><div class=\"main\">{tag_value}<p class=\"text\">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus pretium ut est nec dignissim. Vestibulum pellentesque ac elit porta rhoncus. Donec vulputate odio leo, at posuere purus tincidunt et. Vivamus ut eleifend orci. Sed iaculis tortor vel ultrices tincidunt. Donec in ipsum ut velit interdum venenatis eget a leo. Nullam pulvinar iaculis tincidunt. Vivamus quis elementum nunc. In arcu ante, sagittis ut finibus a, vehicula eu tortor. Nam blandit pretium quam ac finibus. Praesent finibus ex ex.Donec suscipit vulputate erat, a malesuada ligula hendrerit vitae. Nam bibendum ipsum condimentum sapien pretium, sit amet vehicula erat tempor. Etiam ut ornare leo, quis porttitor felis. Mauris varius tempor nisi, ac blandit elit. Cras a consectetur quam, sit amet vestibulum odio. Fusce semper mauris nisl, tristique volutpat enim pulvinar vitae. Sed rhoncus turpis eu venenatis hendrerit. Sed efficitur augue libero. Quisque urna neque, interdum at feugiat eu, laoreet id metus. Vivamus mi dui, feugiat vel vulputate eu, accumsan vel massa. Duis laoreet, leo sit amet egestas lobortis, nibh ante luctus lorem, sit amet consequat diam lectus a nisl. Donec id tortor gravida lorem cursus ornare. Morbi a consectetur urna, non tempor leo. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices.</p></div></div>")
            f.write("</div><script type=\"text/javascript\" src=\"application.js\"></script></body></html>")
            f.close()
                
                

    # Validate URL
    def url_validate(self, url):
        errors = []

        # Valida que la URL empiece por "https://"
        if not re.match(r'^https://', url):
            errors.append("La URL no comienza con 'https://'")

        # Valida que la URL no tenga espacios
        if re.search(r'\s', url):
            errors.append("La URL contiene espacios en blanco")

        # Valida que la URL no contenga el carácter #
        if '#' in url:
            errors.append("La URL contiene el carácter ('#')")

        # Valida que la URL tenga 0 o 1 interrogaciones
        if not re.match(r'^[^\?]*(\?[^\?]*){0,1}$', url):
            errors.append("La URL contiene más de una interrogación ('?')")

        # Valida que la URL no tenga dos "&" juntos
        if re.search(r'&{2}', url):
            errors.append("La URL contiene dos '&' consecutivos")

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
        403: "No esta actualizado/publicado/encontrado en s3",
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
        try:
            response = requests.get(url)
            if response.status_code in error_code:
                error_description = error_code[response.status_code]
                raise ValueError(f"Error Servidor => {response.status_code}: {error_description}")
            else:
                return True
        except requests.exceptions.RequestException as e:
            raise ValueError("La URL no existe o no está activa")

    # set_url_or_link()
    def set_url_or_link(self, href, tcs, i, type, url_param_sep="", utm_size=""):
        if (len(tcs) > 1):
            tc = str(tcs[i])
        elif (len(tcs) > 0):
            tc = str(tcs[0])
        else:
            tc = ""
        
        if type == "link" and href.lower() == "only_tc":
            return '&link=' + tc
        else:
            tc_param = "tc_alt=" if type != "view" and tc else ""
            tc = tc_param + tc
            if utm_size and tc:
                utm_size += "&"
            param = '&link=' if type == "link" else ""
            url_complete = param + href + url_param_sep + utm_size + tc
            # print(url_complete)
            
            return param + href + url_param_sep + utm_size + tc

    # cache_and_clicktag()
    def cache_and_clicktag(self, tag, dsp, url):
        Patt_Click = "${CLICK_URL}"
        Patt_Cache = "[CACHEBUSTER]"
        Valid_Patts = {
            "360_ENC"  : {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL_ENC}"},
            "TTD_ESC"  : {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK_ESC%%"},
            "ZEM_ENC"  : {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL_ENC}"},
            "QCT_ESC"  : {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICKESC}"},
            "STACK_ENC": {"CB": r"[CACHEBUSTER]", "Clk": r"${SA_CLICK_URL_ENC}"},

            "360"  : {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL}"},
            "TTD"  : {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK%%"},
            "RKT"  : {"CB": r"{timestamp}", "Clk": r"{scriptclickprefix}"},
            "QCT"  : {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICK}"},
            "ZEM"  : {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL}"},
            "STACK": {"CB": r"[CACHEBUSTER]", "Clk": r"${SA_CLICK_URL}"},

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

        csv_file = open(f'{ROOT_PATH}/{DSP}_file.csv', 'w')
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


# -------- MAIN() -------
def main():
    
    files = []
    print("-----------\nFiles in folder:")
    for f in sorted(os.listdir(ROOT_PATH+"/INPUT_JSON")):
        ext = re.search(r'(.json)', f)
        if ext:
            files.append(f)
            print(f"- {f}")
        else:
            print(f"- ... Extension not recognized on file: {f}")
    print("-----------")

    run_code = ask_to_run_code()
    if run_code.lower() == "y":
        run_code = True
    else:
        run_code = False

    if run_code:
        IMG_aws_TAG_Bulk(files)


if __name__ == '__main__':
    main()
