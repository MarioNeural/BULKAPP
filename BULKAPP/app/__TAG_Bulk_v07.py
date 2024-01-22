#!/usr/bin/env python3
# Copyright 2009-2017 BHG http://bw.org/


import os
import re
import textwrap
import xlsxwriter
import xlrd
import csv

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
# import pdb; pdb.set_trace()

class TAG_Bulk:
  def __init__(self, file_list, mode, config):    
    self._f_count = 1
    self._recount = []
    self._END_TAG = False
    self._TAG_TAKEN = False
    self._check_nonsript_tag = False
    self._ALL_LIST = []
    self._TAG_LIST = [{"id": ""}]
    self._missing_clktags_printed = False
    self.DSPs = {
      "TTD": ["TTD", "TTD_ESC"],
      "Rest": ["360", "360_ENC", "RKT", "QCT", "QCT_ESC", "ZEM", "ZEM_ENC", "STACK_ENC", "STACK"]
      # "Rest": ["APN", "APN_ENC", "ADF", "360", "360_ENC", "RKT"]
    }

    self._file_list = file_list
    self._landing = config["landing"]
    self._mode = mode

    if mode == "1":
      self._name_w_size = config["name_w_size"]
      self._xls_all_tags = config["xls_all_tags"]
      self.create_list_mode_1()
    elif mode == "2":
      self._name_w_size = False
      self._aws_path_start = config["aws_path_start"]
      self._aws_path_end = config["aws_path_end"]
      self._first_row_variant = config["first_row_variant"]
      self._aws_variant_array_index = None
      self.create_list_mode_2()

  # create_list_mode_1()
  def create_list_mode_1(self):
    # create list
    print("-----------\nFiles to convert:")
    cont = 0
    for f in self._file_list:
      cont += 1
      print(f" - file_{cont} - {f}")
      if ".txt" in f:
        self.open_read_addToList_from_TXT(f)
      else:
        self.open_read_addToList_from_XLS(f)
    print("\n-----------")
    # check for clicktags in <ins>
    self.checkClickTagSize()

    self.create_documents()
  
  # create_list_mode_2()
  def create_list_mode_2(self):
    # create list
    print("-----------\nFiles to convert:")
    cont = 0
    for f in self._file_list:
      cont += 1
      print(f" - file_{cont} - {f}")
      if ".xls" in f:
        self.open_read_addToList_from_XLS_mode_2(f)
      else:
        print('Invalid format for mode 2: ".txt"')
    print("\n-----------")
    self.create_documents()

  # create_documents()
  def create_documents(self):
    self.print_All_List()

    # create XLSX files
    for dsp in self.DSPs["Rest"]:
      self.create_XLSX(dsp)
    for dsp in self.DSPs["TTD"]:
      self.create_TTD_XLSX(dsp)

    self.print_info()
    print("\nXLSX files have been created successfully!!!\n")  


  # reset_values()
  def reset_values(self):
    self._f_count += 1
    self._END_TAG = False
    self._TAG_TAKEN = False
    self._check_nonsript_tag = False
    self._TAG_LIST = [{"id": ""}]  
  

  # clear_append_reset()
  def clear_append_reset(self):
    temp_list = []
    count = 0
    for obj in self._TAG_LIST:
      if obj.get("tag"):
        count += 1
        obj["id"] = f"{self._f_count}.{count}"
        temp_list.append(obj)

    self._recount.append([self._f_count, count])    
    self._ALL_LIST.append(temp_list)
    self.reset_values()  


  # open_read_addToList_from_XLS()
  def open_read_addToList_from_XLS(self, f):
    wb = xlrd.open_workbook(f'{ROOT_PATH}/FILES_TO_CONVERT/{f}')
    sh = wb.sheet_by_index(0)
    name = f.split(".")[0]
    tag_row = 0
    tag_col = 0
    
    # get Tag column and row
    for x in range(sh.nrows):
      for y in range(sh.ncols):
        if re.match("Iframes/JavaScript Tag", str(sh.cell_value(x, y))) or re.match("Legacy JavaScript Tag", str(sh.cell_value(x, y))):
          tag_row = x
          tag_col = y
          break
    
    count = 0
    # get Tags content and add to _TAG_LIST
    for x in range(tag_row+1, sh.nrows):
      obj = self._TAG_LIST[count]
      tag = sh.cell_value(x, tag_col)
      # remove multiple tags
      if not self._xls_all_tags:
        frst_tag = re.match(r'<\w+', tag).group(0).replace("<", "")
        part = tag.partition(f'</{frst_tag}>')
        tag = part[0]+part[1]
      
      # create object
      obj["name"] = name
      obj["name w/size"] = name
      obj["tag"] = tag
      self.getSize(tag, count)
      count += 1
      self._TAG_LIST.insert(count, {"id": ""})
      
    self.clear_append_reset()


  # open_read_addToList_from_XLS_mode_2()
  def open_read_addToList_from_XLS_mode_2(self, f):
    wb = xlrd.open_workbook(f'{ROOT_PATH}/FILES_TO_CONVERT/{f}')
    sh = wb.sheet_by_index(0)
    name = f.split(".")[0]
    row_headers = 0
    col_placement_name = 0
    col_impression_tag = 0
    col_click_tag = 0
    
    # get Tag column and row
    for x in range(sh.nrows):
      if row_headers > 0:
        break
      for y in range(sh.ncols):
        if re.match("Placement Name", str(sh.cell_value(x, y))):
          row_headers = x
          col_placement_name = y
        if re.match("Impression Tag \(JavaScript\)", str(sh.cell_value(x, y))):
          col_impression_tag = y
        if re.match("Click Tag", str(sh.cell_value(x, y))):
          col_click_tag = y
    
    count = 0

    # get Tags content and add to _TAG_LIST
    for x in range(row_headers+1, sh.nrows):
      obj = self._TAG_LIST[count]
      name = sh.cell_value(x, col_placement_name)
      impression_tag = sh.cell_value(x, col_impression_tag)
      click_tag = sh.cell_value(x, col_click_tag)
      
      if count == 0:
        self.aws_variant(name, set=True)
      # create object
      self.getSize(name, count)
      self.create_tag(name, impression_tag, click_tag, obj)
      count += 1
      self._TAG_LIST.insert(count, {"id": ""})
      
    self.clear_append_reset()


  # create_tag()
  def create_tag(self, name, impression_tag, click_tag, obj):
    obj["name"] = name
    size = obj.get("size")
    width = obj.get("width")
    height = obj.get("height")
    aws_path_variant = self.aws_variant(name)
    
    obj["tag"] =  f"<a href='[CLICKURL]{click_tag}' target='_blank'><img src='https://ppj05.cdnwebcloud.com/{self._aws_path_start}{aws_path_variant}/{size}{self._aws_path_end}' width='{width}' height='{height}' /></a> {impression_tag}"


  # aws_variant()
  def aws_variant(self, name, set=False):
    # import pdb; pdb.set_trace()
    name_wo_size = re.sub(r'(\d){2,4}x(\d){2,4}', '', name)
    arr_name = name_wo_size.split("_")
  
    if set:
      self._aws_variant_array_index = arr_name.index(self._first_row_variant)
    
    return arr_name[self._aws_variant_array_index]


  # open_read_addToList_from_TXT()
  def open_read_addToList_from_TXT(self, f):
    infile = open(f'{ROOT_PATH}/FILES_TO_CONVERT/{f}', 'rt')
    name = ""
    count = 0
    # Loop through all lines to create TAG_LIST
    for line in infile:
      obj = self._TAG_LIST[count]
      if len(line.strip()) >= 1 :
        # (tag line)
        if self._END_TAG:
          self.isClosingTag(line, count)
          if not self._END_TAG: 
            self._TAG_TAKEN = True
          continue
        elif not self._TAG_TAKEN:
          self.isOpeningTag(line, count)
        
        # (name line)
        if re.match(r'_\w', line): 
          name = line.replace("_", "", 1).strip()
          obj["name"] = name
          obj["name w/size"] = name 

        # (separating line)
        elif re.match(r'(\W)\1{5,}', line):
          # check if last list item has content, else delete it
          count+=1 
          self._TAG_TAKEN = False
          self._TAG_LIST.insert(count, {"id": "", "name": name, "name w/size": name})
    
    self.clear_append_reset()
    

  # isOpeningTag()
  def isOpeningTag(self, line, cnt):
    obj = self._TAG_LIST[cnt]
    possible_tags = ["iframe", "script", "ins", "a"]

    if line[0] == "<" and line[1] != "!":
      tag = line.split()[0]
      #check wich tag
      for t in possible_tags:
        if tag.lower() == "<"+t: 
          self.getSize(line, cnt)
          if "</"+t in line:
            obj["tag"] = line.rstrip()
            self._TAG_TAKEN = True
            return
          else:  
            obj["tag"] = line
            self._END_TAG = "</"+t+">"
            return
      raise TypeError(f'unknown tag: "{tag}" on tag number {self._f_count}.{cnt+1}')

  # isClosingTag() 
  def isClosingTag(self, line, cnt):
    obj = self._TAG_LIST[cnt]
    self.getSize(line, cnt)
    if self._END_TAG in line: 
      obj["tag"] += line.rstrip()
      self._END_TAG = False
    else:
      obj["tag"] += line

    # print(obj["tag"])  

  # getSize()    
  def getSize(self, line, cnt):
    obj = self._TAG_LIST[cnt]
    size_exists = obj.get("size")
    if size_exists: return
    else:
      # if the word "width" is there...
      if "width" in line.lower():
        for i in line.split():
          for j in i.split(";"):
            if "width" in j.lower():
              w = re.search(r'\d{2,4}', j)
              if w: obj["width"] = w.group(0)
            if "height" in j.lower():
              h = re.search(r'\d{2,4}', j)
              if h: obj["height"] = h.group(0)

        if obj.get("width"):
          obj["size"] = obj["width"]+"x"+obj["height"]    
            
      # no word "width" found...
      else: 
        s = re.search(r'(\d){2,4}x(\d){2,4}', line)
        if s: 
          obj["size"] = s.group(0)
          obj["width"] = obj.get("size").split("x")[0]
          obj["height"] = obj.get("size").split("x")[1]
      
      if obj.get("size") and obj.get("name w/size"):
        obj["name w/size"] += "_"+obj["size"]
          

  # checkClickTagSize()
  def checkClickTagSize(self):
    clk_tag_holder = "data-dcm-click-tracker="
    for i in self._ALL_LIST:
      for item in i:
        # print("item: ", item)
        #clicktag
        if "<ins" in item["tag"] and not clk_tag_holder in item["tag"]: 
          item["tag"] = item["tag"].replace(">", "\n    "+clk_tag_holder+"'${CLICK_URL}'>", 1)
          print(f'tag {item["id"]} (<ins>): added "{clk_tag_holder}CLICK_URL"')
        #size
        if not item.get("size"): 
          s = re.search(r'(\d){2,4}(x|X)(\d){2,4}', item["tag"])
          if not s: 
            s = re.search(r'(\d){2,4}(x|X)(\d){2,4}', item["name"])
          if s: 
            item["size"] = s.group(0).lower()
            item["width"] = item.get("size").split("x")[0]
            item["height"] = item.get("size").split("x")[1]
            item["name w/size"] += "_"+item["size"]
          else:
            print(f'tag {item["id"]}: NO SIZE FOUND!!')


  # cache_and_clicktag()
  def cache_and_clicktag(self, id, tag, dsp):
    # import pdb; pdb.set_trace()
    Patt_Click = [r"${CLICK_URL}", r"[CLICKURL]", r"CLICK_TAG_GOES_HERE", r"${ClickURL}", r"{scriptclickprefix}", r"[clicktag]", r"${CLICK_URL_ENC}", r"%%TTD_CLK%%", r"%%TTD_CLK_ESC%%", r"%%c1;cpdir="]
    Patt_Cache = [r"${CACHEBUSTER}", r"{timestamp}", r"[timestamp]", r"[CACHEBUSTER]", "YOUR_CUSTOM_CACHE_BUSTER", r"%%TTD_CACHEBUSTER%%", r"%%ADFRND%%", ]
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

    for patt in Patt_Click:
      if patt.upper() in tag.upper():
        tag = tag.replace(patt, Valid_Patts[dsp]["Clk"])
        break
    else: 
      if not self._missing_clktags_printed: 
        print(f'-> tag {id} ({tag.split()[0]}>): [clicktag] not recognized or missing, please check')

    for patt in Patt_Cache:
      if patt.upper() in tag.upper():
        tag = tag.replace(patt, Valid_Patts[dsp]["CB"])
        break   
    return tag
  

  # create_TTD_XLSX()
  def create_TTD_XLSX(self, DSP):
    templ_wb = xlrd.open_workbook(f'{ROOT_PATH}/_Template_TTD(dont_delete).xlsx')
    new_wb = xlsxwriter.Workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')

    for name in templ_wb.sheet_names():
      sh = templ_wb.sheet_by_name(name)
      new_sh = new_wb.add_worksheet(name)
      row = 0
      col = 0
      
      for x in range(sh.nrows):
        for y in range(sh.ncols):
          new_sh.write(row, col, sh.cell_value(x, y))
          col +=1
        col = 0
        row += 1
    
      if new_sh.name == "Third Party Display": 
        ws = new_sh  # set the sheet to pass as a param 
    
    order = ["name w/size" if self._name_w_size else "name", "_blank", "width", "height", "tag", "_landing", "_blank", "_blank", "_blank", "_secure"]  
    missing_content = {"_blank": "", "_landing": self._landing, "_secure": "yes"}
    # write_XLSX
    self.write_XLSX(DSP, row, new_wb, ws, order, missing_content)

  
  # create_XLSX()
  def create_XLSX(self, DSP):
    wb = xlsxwriter.Workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')
    ws = wb.add_worksheet()
    row = 0
    col = 0
    missing_content = {'_blank': '', '_landing': self._landing}
    name_column_field = 'name w/size' if self._name_w_size else 'name'

    if DSP == 'RKT':
      labels = ['Placement Name', 'Ad Tag', 'Width', 'Height', 'Start Date', 'End Date', 'Landing Page Url']
      order = [name_column_field, 'tag', 'width', 'height', '_blank', '_blank', '_landing']
    elif DSP == '360' or DSP == '360_ENC' or DSP == 'QCT' or DSP == 'QCT_ESC':
      labels = ['Creative name', 'Dimensions (width x height)', 'Third-party tag', 'Landing page URL', 'Expanding direction', 'Expands on hover ("Yes" or "No")', 'Requires HTML5 ("Yes" or "No")', 'Requires MRAID ("Yes" or "No")', 'Requires ping for attribution ("Yes" or "No")', 'Integration code (Optional)', 'Notes (Optional)']
      order = [name_column_field, 'size', 'tag', '_landing', '_blank', 'exp_hover', 'html', 'mraid', 'ping']  
      missing_content.update({'exp_dir': '','exp_hover': 'No', 'html': 'Yes', 'mraid': 'No', 'ping': 'No'})
    elif DSP == 'ZEM' or DSP == 'ZEM_ENC':
      labels = ['URL', 'Title', 'Display URL', 'Ad tag', 'Ad tag width', 'Ad tag height']
      order = ['_landing', name_column_field, '_landing', 'tag', 'width', 'height']
    elif DSP == 'STACK' or DSP == 'STACK_ENC':
      labels = ['Campaign Id', 'Campaign Name (Read only)','Creative Id', 'Image File', 'Creative Name', 'JS Code / HTML', 'Dimension (Image File - Read only)', 'Dimension (JS Code)', 'Is expandable (JS Code)', 'Click URL', 'Sponsored By', 'Impression Tracking URLs']
      order = ['_blank', '_blank', '_blank', '_blank', name_column_field, 'tag', '_blank', 'size', '_blank', '_landing', 'sponsored_by', '_blank']
      missing_content.update({'sponsored_by': 'none'})
    
    # elif DSP == 'APN' or DSP == 'APN_ENC':  
    #   labels = ['File Name', 'Size', 'Tag Content']
    #   order = ['name w/size' if self._name_w_size else 'name', 'size', 'tag']
    # elif DSP == 'ADF':
    #   labels = ['Name', 'Click URL', 'Content', 'Size']
    #   order = ['name w/size' if self._name_w_size else 'name', '_blank', 'tag', 'size']  

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
      for i in item:
        for k in order:
          key_exists = i.get(k)
          #...if the key exists in the dsict (most cases)
          if key_exists:
            # change cachebuster and clicktag
            if k == "tag": 
              temp = self.cache_and_clicktag(i["id"], i[k], DSP) 
              ws.write(row, col, temp)
            else:  
              ws.write(row, col, i[k])
          #...key doesn't exist (for 360)    
          else: ws.write(row, col, missing_content[k])
          col += 1
        col = 0  
        row += 1  
    
    self._missing_clktags_printed = True  #only show missing clicktags the fist time cache_and_clicktag() runs
    wb.close()
    # create CSV file    
    if "360" in DSP:
      self.create_CSV(DSP)
    
      
  # create_CSV()
  def create_CSV(self, DSP):
    wb = xlrd.open_workbook(f'{ROOT_PATH}/{DSP}_file.xlsx')
    sh = wb.sheet_by_name('Sheet1')

    csv_file = open(f'{ROOT_PATH}/{DSP}_file.csv', 'w')
    wr = csv.writer(csv_file, quoting = csv.QUOTE_ALL)
    for rownum in range(sh.nrows):
      wr.writerow(sh.row_values(rownum))
    
    csv_file.close()
    os.remove(f'{ROOT_PATH}/{DSP}_file.xlsx') # delete .xlsx after creating .csv


  # print_info()
  def print_info(self):
    tot = 0
    print()
    for i in self._recount:
      file_of_tag = self._file_list[i[0]-1]
      print(f"- {i[1]} tags in file_{i[0]} - {textwrap.shorten(file_of_tag, width=50)} ")
      tot += i[1]
    print(f"Total amount of tags: {tot}")


  # print_All_List()        
  def print_All_List(self):
    print("---------------------\n", "ALL_LIST:")   
    for i in self._ALL_LIST:
      for d in i:
        for k in d:
          print(k, ":", d[k])    
        print("--------")
      print("********************")     


# --------- end of TAG_Bulk() --------

# ask_what_mode()
def ask_what_mode():
  q = input('What mode do you want to run?\n 1 - regular mode \n 2 - civitatis mode\n')
  if q != "1" and q != "2":
    print(f' > Invalid command "{q}", try again\n')
    q = ask_what_mode()
  return q 


# ask_landing()
def ask_landing():    
  return input('Type landing URL of creatives (e.i.: "https://www.iberostar.com/"):\n')


# ask_add_size_at_end()
def ask_add_size_at_end():
  q = input('Add the SIZE at the end of the NAMES? Y/N\n')
  if q.lower() != "y" and q.lower() != "n":
    print(f' > Invalid command "{q}", try again\n')
    q = ask_add_size_at_end()
  return q 

# ask_xls_add_script_tags()
def ask_xls_add_script_tags():
  q = input('Use ALL the TAGS in the XLS cell? Y/N\n')
  if q.lower() != "y" and q.lower() != "n":
    print(f' > Invalid command "{q}", try again\n')
    q = ask_xls_add_script_tags()
  return q   


# -------- MAIN() -------
def main():

  # pass TEXT files to convert
  files = []
  is_xls = False
  print("-----------\nFiles in folder:")
  for f in sorted(os.listdir(ROOT_PATH+"/FILES_TO_CONVERT")):
    ext = re.search(r'(.txt)|(.xls)', f)
    if ext: 
      if ext.group(0) == ".xls": is_xls = True
      files.append(f)
      print(f"- {f}")
    else: 
      print(f"- ... Extension not recognized on file: {f}")
  print("-----------")    

  
  if files:
    ## initial inputs
    landing = ""
    name_w_size = False
    xls_all_tags = False

    mode = ask_what_mode()
    # 1 - regular mode
    if mode == "1":
      config = {}
      config["xls_all_tags"] = False

      config["landing"] = ask_landing()
 
      name_w_size = ask_add_size_at_end()
      config["name_w_size"] = True if name_w_size.lower() == "y" else False

      if is_xls: 
        xls_all_tags = ask_xls_add_script_tags()
        if xls_all_tags.lower() == "y": config["xls_all_tags"] = True 
    
    # 2 - civitatis mode
    elif mode == "2":
      config = {
        "aws_path_start": "CIVITATIS/2023/03/semana_santa/",
        "aws_path_end": ".gif",
        "first_row_variant": "AR",
        "landing": "www.civitatis.com"
      }

    TAG_Bulk(files, mode, config)


if __name__ == '__main__': main()
