import tkinter as tk
from tkinter import messagebox
import re


def one_line_arrays(json_string):
    def replace_array(match):
        items = match.group(1).split(',')
        cleaned_items = [item.strip() for item in items if item.strip()]
        return '[' + ', '.join(cleaned_items) + ']'

    return re.sub(r'\[\s*((?:"[^"]+",?\s*)+)\]', replace_array, json_string)