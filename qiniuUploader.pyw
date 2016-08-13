#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import os.path
import time
from Tkinter import *
import tkFont
import tkFileDialog
from qiniu import Auth
from qiniu import etag
from qiniu import put_file

g_type = 'img'


def show_msg(val):
    global txtLog
    print val
    txtLog.insert(END, "%s\n" % val)
    txtLog.focus_force()
    txtLog.see(END)
    txtLog.update()


def on_open_file():
    global g_filepath
    fullpath = tkFileDialog.askopenfilename(filetypes=[("All files", "*")])
    g_filepath.set(fullpath)


def on_go():
    global txtLog
    global g_filepath
    txtLog.delete(0.0, END)

    # check file
    filepath = g_filepath.get()
    if filepath == "":
        show_msg("Please choose a file to upload")
        return
    if not os.path.exists(filepath):
        show_msg("\nFile missing!\n%s" % filepath)
        return
    show_msg("Chosen file:%s" % filepath)

    # load key
    access_key = ''
    secret_key = ''
    bucket_name = ''
    link_prefix = ''
    key_file = open('key.txt')
    key_lines = key_file.readlines()
    for key_line in key_lines:
        key_key = key_line[:key_line.find('=')]
        key_val = key_line[key_line.find('=') + 1:]
        key_val = key_val.replace('\r', '').replace('\n', '')
        if key_key == 'access_key':
            access_key = key_val
        if key_key == 'secret_key':
            secret_key = key_val
        if key_key == 'bucket_name':
            bucket_name = key_val
        if key_key == 'link_prefix':
            link_prefix = key_val

    if access_key == '' or secret_key == '':
        show_msg("can't find key")
        return
    if bucket_name == '':
        show_msg("can't find bucket_name")
        return
    show_msg("access_key:%s...%s" % (access_key[:5], access_key[len(access_key) - 5:]))
    show_msg("secret_key:%s...%s" % (secret_key[:5], secret_key[len(secret_key) - 5:]))
    show_msg("bucket_name:%s" % bucket_name)

    # initialize
    q = Auth(access_key, secret_key)

    filename = filepath[filepath.rfind('/') + 1:]
    strdate = time.strftime("%Y%m%d", time.localtime())
    key = '%s/%s/%s' % (g_type, strdate, filename)
    show_msg("Target path = %s" % key)
    token = q.upload_token(bucket_name)
    if token:
        show_msg("Token got successfully...")
    ret, info = put_file(token, key, filepath, check_crc=True)

    if not ret:
        show_msg("======Upload Failed======")
        if info:
            dicinfo = {}
            dicinfo.update(info.__dict__)
            if "status_code" in dicinfo:
                show_msg("ErrorCode=%d" % dicinfo["status_code"])
            else:
                show_msg("Unknown Error")
        else:
            show_msg("Unknown Error")
        return
    ret_hash = ""
    ret_key = ""
    if "hash" in ret:
        ret_hash = ret["hash"]
    if "key" in ret:
        ret_key = ret["key"]
    if ret_key != key:
        show_msg("ret_key mismatch! - %s" % ret_key)
        return
    if ret_hash != etag(filepath):
        show_msg("ret_hash mismatch! - %s" % ret_hash)
        return
    show_msg("======Upload Successful=====")
    if link_prefix != "":
        show_msg("External Link:\n")
        show_msg(link_prefix + key)


if __name__ == "__main__":
    app = Tk()
    app.title("Qiniu Uploader")
    frame = Frame(app, padx=20, pady=20)
    frame.pack()

    g_filepath = StringVar(frame)

    titleFont = tkFont.Font(family="Consolas", size=20)
    lblTitle = Label(frame, text="Qiniu File Uploader", font=titleFont, padx=10, pady=10)
    lblTitle.grid(row=0, column=0, rowspan=2, columnspan=5)

    lblFile = Label(frame, text="File:")
    lblFile.grid(row=2, column=0, sticky=W)

    txtFilename = Entry(frame, width=40, textvariable=g_filepath, state=DISABLED)
    txtFilename.grid(row=2, column=1, columnspan=3)

    btnOpenFile = Button(frame, text="Choose...", command=on_open_file)
    btnOpenFile.grid(row=2, column=4)

    goFont = tkFont.Font(family="Consolas", size=15)
    btnGo = Button(frame, text="Upload", command=on_go, font=goFont)
    btnGo.grid(row=3, column=2)

    lblFrame = LabelFrame(frame, text="output")
    lblFrame.grid(row=4, column=0, columnspan=5)
    sbv = Scrollbar(lblFrame, orient=VERTICAL)
    txtLog = Text(lblFrame, width=50, height=10, padx=20, pady=20, yscrollcommand=sbv.set)
    sbv.config(command=txtLog.yview())
    sbv.pack(fill="y", expand=0, side=RIGHT, anchor=N)
    txtLog.pack(fill="x", expand=1, side=LEFT)

    app.mainloop()

    if len(sys.argv) > 1:
        # has parameter
        g_filepath.set(sys.argv[1])
