import numpy as np
import pandas as pd
import re
import os
import sys
import tkinter
from tkinter import filedialog

CUR_FOLDER = os.getcwd()  # this is the folder used as initial for file and folder dialogs


def fileparts(fullFile):
	pathName, file = os.path.split(fullFile)
	return pathName, file


def fileparts2(fullFile):
	filePath, ext = os.path.splitext(fullFile)
	return filePath, ext


def fileparts3(fullFile):
	filePath, ext = os.path.splitext(fullFile)
	pathName, file = os.path.split(filePath)
	return pathName, file, ext


# request files by user selection
def requestFiles(fileType=(("All files", "*.*"),), dialogTitle="", multiselect="on", folder=None):
	global CUR_FOLDER
	if folder is None:
		folder = CUR_FOLDER
	if len(dialogTitle) == 0:
		if multiselect == "on":
			dialogTitle = "Select files"
		else:
			dialogTitle = "Select file"
	# request file(s)
	# `win32` for Windows(Win32), 'cygwin' for Windows(cygwin), 'linux' for Linux, 'darwin' for macOS, 'aix' for AIX
	if sys.platform != 'darwin':
		root = tkinter.Tk()
		root.wm_attributes('-topmost', True)  # show dialog in front of all
		root.withdraw()
	if multiselect == "on":
		if sys.platform != 'darwin':
			files = filedialog.askopenfilenames(initialdir=folder, title=dialogTitle, filetypes=fileType, parent=root)
		else:
			files = filedialog.askopenfilenames(initialdir=folder, title=dialogTitle, filetypes=fileType)
	else:
		# put single file into tuple
		if sys.platform != 'darwin':
			files = (filedialog.askopenfilename(initialdir=folder, title=dialogTitle, filetypes=fileType, parent=root),)
		else:
			files = (filedialog.askopenfilename(initialdir=folder, title=dialogTitle, filetypes=fileType),)
	# get path of first selected file to set as new working directory
	if len(files) > 0 and len(files[0]) > 0:
		CUR_FOLDER, file = fileparts(files[0])
	return files


def read_fio(f_name, includeFixData=False):
	header = dict()
	data = pd.DataFrame()
	param_line = re.compile(r'^(?P<key>[\w\.]+) = (?P<val>[\d\.+-eE]+)\n')
	t_header_line = re.compile(r'^ Col (?P<col>[\d]+) (?P<key>[\w\.]+) (?P<type>[\w\.]+)\n')
	with open(f_name, 'r') as f:
		lines = f.readlines()
		for line in lines[lines.index('%p\n') + 1:]:
			m = param_line.match(line)
			if m:
				header[m.group('key')] = float(m.group('val'))
		if not header:
			return header, data
		columns = dict()
		for ii, line in enumerate(lines[lines.index('%d\n') + 1:]):
			m = t_header_line.match(line)
			if m:
				columns[int(m.group('col'))] = m.group('key')
			else:
				break
		if not columns:
			return header, data
		cols = list(columns.values())
		if includeFixData:
			cols.extend(header.keys())
		data = pd.DataFrame(columns=list(set(cols)))
		# t_row_line = re.compile(r'^' + r'\s+([\d\.+-eE]+)' * len(columns) + r'\n')
		t_row_line = re.compile(r'^' + r'\s+([\w\.+-]+)' * len(columns) + r'\n')

		def _float(s):
			try:
				return float(s)
			except ValueError:
				return None

		for line in lines[lines.index('%d\n') + ii + 1:]:
			m = t_row_line.match(line)
			if m is not None:
				vals = m.groups()
				row = {columns[i + 1]: _float(vals[i]) for i in range(len(columns))}
				if includeFixData:
					row_ext = header
					row_ext.update(row)
					data.loc[data.shape[0]] = row_ext
				else:
					data.loc[data.shape[0]] = row
	return data, header


def write_fio(header, data, f_name, checkFixData=False):
	if checkFixData:
		fix_cols = np.zeros(data.columns.shape)
		for ii, col in enumerate(data.columns):
			fix_cols[ii] = np.unique(data[col]).size == 1
		extract_cols = data.columns[fix_cols == 1]
		header.update({col: data[col][0] for col in extract_cols})
		data.drop(extract_cols, axis=1, inplace=True)
	with open(f_name, 'w') as f:
		f.write('!\n! Parameter\n!\n%p\n')
		for k in header:
			f.write('%s = %f\n' % (k, header[k]))
		f.write('!\n! Data\n!\n%d\n')
		for ii, col in enumerate(data.columns):
			f.write(' Col %d %s DOUBLE\n' % (ii + 1, col))
		for ii in data.index:
			for col in data.columns:
				f.write(' %.03f' % data.loc[ii, col])
			f.write('\n')
		f.write('!\n')
		return True
