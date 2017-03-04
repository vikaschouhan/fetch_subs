#!/usr/bin/env python

# Python script for downloading subtitles from https://subscene.com
# Copyright : Vikas Chouhan (presentisgood@gmail.com)
# License   : GPLv2
#
# Dependencies : unrar should be installed
#                rarfile (python module) is required

import urllib2
import urllib
from   bs4 import BeautifulSoup
import re
import os
try:
  from cStringIO import StringIO
except:
  from StringIO import StringIO
import zipfile
import rarfile


user_agent = "Mozilla/5.0"

# Main function
def fetch_subs():
    out_dir   = os.path.expanduser('~') + '/subs/'    # Target directory
    url_home  = 'https://subscene.com'
    cntr      = 0;

    s_str     = str(raw_input('Enter movie name : '))
    # For url encoding
    url_enc_d = {
                    'q' : s_str,
                    'l' : '',
                }
    url_this  = url_home + '/subtitles/title?{}'.format(urllib.urlencode(url_enc_d))
    print "Querying {}".format(url_this)
    req_this  = urllib2.Request(url_this, headers={'User-Agent' : user_agent})
    data_this = urllib2.urlopen(req_this)
    page_root = data_this.read()
    soup_root = BeautifulSoup(page_root, 'lxml')
    
    # Find all hrefs
    hrefs_list = soup_root.find_all('a', href=re.compile(r'/subtitles/'))
    hrefs_list.pop()   # Remove last elements as it's irrelevant
    hrefs_list = list(set(hrefs_list))  # Remove duplicates
    
    if len(hrefs_list) == 0:
        print 'Nothing found !!'
        return
    # endif

    # Ask user to press a button
    p_str = 'Found following list.\n'
    for indx in range(0, len(hrefs_list)):
        p_str = p_str + '{} : {}\n'.format(indx, hrefs_list[indx].text.encode('utf-8'))
    # endfor
    p_str = p_str + 'Enter choice : '
    choice = int(raw_input(p_str))

    if choice > len(hrefs_list):
        print "Entered wrong choice {}".format(choice)
        return
    # endif

    print "Choice Entered is {}".format(choice)

    href_this   = hrefs_list[choice]
    link_title  = href_this['href'].split('/')[2]
    url_this    = url_home + href_this['href']
    print "Going to page {}".format(url_this)

    req_this    = urllib2.Request(url_this, headers={'User-Agent' : user_agent})
    data_this   = urllib2.urlopen(req_this)
    page_this   = data_this.read()

    soup_this   = BeautifulSoup(page_this, 'lxml')
    hrefs2_list = soup_this.find_all('a', href=re.compile(r'\/subtitles\/{}\/'.format(link_title)))
    print "Found {} subtitles in all languages.".format(len(hrefs2_list))

    main_lang   = u'English'
    title_list  = []

    for indx in range(0, len(hrefs2_list)):
        span_list = hrefs2_list[indx].find_all('span')
        lang_this = span_list[0].text.replace('\t', '').replace('\n', '').replace('\r', '')
        mov_name  = span_list[1].text.replace('\t', '').replace('\n', '').replace('\r', '')

        if lang_this == main_lang:
            title_list.append({
                                   'lang'   : lang_this,
                                   'title'  : mov_name,
                                   'href'   : hrefs2_list[indx],
                             })
        # endif
    # endfor

    print "Found {} {} subtitles.".format(len(title_list), main_lang)
    if len(title_list) == 0:               # if no list was returned, just return
        return
    # endif

    print "Downloading all {} subtitles.".format(main_lang)

    # Create out_dir if it doesn't exist
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    # endif

    for item in title_list:
        url_this    = url_home + item['href']['href']
        req_this    = urllib2.Request(url_this, headers={'User-Agent' : user_agent})
        data_this   = urllib2.urlopen(req_this)
        page_this   = data_this.read()

        soup_this   = BeautifulSoup(page_this, 'lxml')
        down_btn    = soup_this.find('div', { 'class' : 'download'})   # Get download button
        if down_btn == None:
            continue
        # endif
        btn_href    = down_btn.find('a')['href']
        url_next    = url_home + btn_href

        req_this    = urllib2.Request(url_next, headers={'User-Agent' : user_agent})
        data_this   = urllib2.urlopen(req_this)
        file_fp     = StringIO(data_this.read())
        try:
            try:
                with zipfile.ZipFile(file_fp, "r") as zfp:
                    print "Extracting {} in {}".format(item['title'].encode('utf-8'), out_dir)
                    zfp.extractall(out_dir)
                # endwith
            except zipfile.BadZipfile:
                with rarfile.RarFile(file_fp, "r") as rfp:
                    print "Extracting {} in {}".format(item['title'].encode('utf-8'), out_dir)
                    rfp.extractall(out_dir)
                # endwith
            # endtry
        except rarfile.RarUnknownError:
            print "Warning: Not a valid zip or rar file. Writing as it is.".format(url_next)
            with open('{}/{}.{}'.format(out_dir, cntr, 'unknown'), 'w') as fp:
                fp.write(file_fp.getvalue())
            # endwith
            cntr = cntr + 1
    # endfor
# enddef

if __name__ == '__main__':
    fetch_subs()
# endif
