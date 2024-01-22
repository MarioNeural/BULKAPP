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
            "Rest": ["360", "360_ENC", "RKT", "QCT", "QCT_ESC", "ZEM", "ZEM_ENC"]
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
                            if not self.url_validate(link.split("&link=")[1]):
                                raise ValueError("#Error: url is malformed...")

                            creative_route = 'https://ppj05.cdnwebcloud.com/' + item["aws_path_1"] + s + item["aws_path_2"]

                            if not self.verify_response_code(creative_route):
                                raise ValueError("#Error: url response code is not 200...")

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
        with open("test.html", "w") as f:
            f.write("<html>")
            # f.write("<style>*{display: flex; flex-wrap: wrap;}</style>")
            f.write("<body>")
            for value in tag:
                tag_value = value["tag"]
                tag_name = value["name"]
                f.write(f"<div><p>{tag_name}</p>{tag_value}</div>")
            f.write("</body>")
            f.write("</html>")
            f.close()
            
    # Validate URL
    def url_validate(self, url):
      # Valida que la URL empiece por "https://"
      if not re.match(r'^https://', url):
        return False

      # Valida que la URL no tenga espacios
      if re.search(r'\s', url):
        return False

      # Valida que la URL tenga 0 o 1 interrogaciones
      if not re.match(r'^[^\?]*(\?[^\?]*){0,1}$', url):
        return False

      # Valida que los nombres de los parámetros no estén repetidos
      # if re.search(r'(\?|&)[^\?&]*\1', url):
      #   return False

      # Valida que la URL no tenga dos "&" juntos
      if re.search(r'&{2}', url):
        return False

      # Si la URL cumple con todas las condiciones, se considera válida
      return True

    #verify_response_code()
    def verify_response_code(self, url):
      error_code = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 421, 422, 423, 424, 425, 426, 428, 429, 431, 451, 500, 501, 502, 503, 504, 505, 506, 507, 508, 510, 511]
      try:
          response = requests.get(url)
          if response.status_code in error_code:
            raise ValueError(f"La URL devolvió el código de respuesta {response.status_code}")
          else:
            return True
      except requests.exceptions.RequestException as e:
          raise ValueError(f"La url no existe o no está activa")

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
        Patt_Click = "[CLICKURL]"
        Patt_Cache = "[CACHEBUSTER]"
        Valid_Patts = {
            "360_ENC": {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL_ENC}"},
            "TTD_ESC": {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK_ESC%%"},
            "ZEM_ENC": {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL_ENC}"},
            "QCT_ESC": {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICKESC}"},

            "360": {"CB": r"${CACHEBUSTER}", "Clk": r"${CLICK_URL}"},
            "TTD": {"CB": r"%%TTD_CACHEBUSTER%%", "Clk": r"%%TTD_CLK%%"},
            "RKT": {"CB": r"{timestamp}", "Clk": r"{scriptclickprefix}"},
            "QCT": {"CB": r"[CACHEBUSTER]", "Clk": r"${CLICK}"},
            "ZEM": {"CB": r"{CACHEBUSTER}", "Clk": r"{CLICK_URL}"},

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
