
HOW TO USE XLSXConv_DSP:

* Put the files with the tags you want to convert in the folder "FILES_TO_CONVERT"


* Edit .txt files:
    - For any line to be recognized, it must START WITHOUT ANY SPACES!
    - Any line starting with at least 5 NON-ALPHANUMERIC CHARS ("[^a-zA-Z0-9_]"), e.i.: "======", will be taken as a separator: the end of a creative and the start of the next one.
    - Any line starting with UNDERSCORE + ALPHANUMERIC CHAR ("_\w") will be set as the NAME of that creative (optional). In case there is more than one, the LAST NAME it encounters will prevail. If no name has been given for a creative but any previous one has one, that creative will get the SAME NAME.
    - Any line starting with LESS-THAN SIGN ("<") + ("ins", "iframe" or "script") will be taken as the start of the tag. If it doesn't have a closing tag ("</tag>"), it will look for it on the successive lines until it finds it. Those lines will be recognized even if they start with a space. In case there is more than one, the FIRST TAG it encounters will prevail.
    - All the other lines will be ignored.

    - if tags DON'T include the SIZE, set the name of each creative with the size to avoid errors



* Edit .xls or .xlsx files:
    - The NAME OF THE FILE + SIZE (taken from each tag) will be set as the name of the creatives. 
    - The tags will be taken from the column "Iframes/JavaScript Tag"



* Run XLSXConv_DSP.py:

   "Type landing URL of creatives (e.i.: "https://www.iberostar.com/")": 
      - It is the base of the Click URL. It will be used for audition purposes.

   "Add the SIZE at the end of the NAMES? Y/N":
      - If you want to add the dimensions of each creative at the end of its name or not.
      - N/n -> "name_you_set_on_txt_file"
      - Y/y -> "name_you_set_on_txt_file_300x600"


___________________________________________________________________________

 
for <ins>: data-dcm-click-tracker='${CLICK_URL}'

landing: 

_name goes here



====================================================================

